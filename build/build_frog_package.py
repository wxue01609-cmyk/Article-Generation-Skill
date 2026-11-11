#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""青蛙平台上传包构建器（唯一源：本仓库的 geo-* skill 目录）。

用途：
  本地/GitHub 的 skill 是唯一规则源；本脚本把它们自动转换成青蛙平台需要的
  prompts/*.md（规则正文 + references 全文内联 + 平台适配说明）、tools/*.py、
  agent.json 与 agent.md，并打成 zip。禁止再手改青蛙包里的提示词。

用法：
  python3 build/build_frog_package.py                 # 构建到 dist/ 并打 zip 到桌面
  python3 build/build_frog_package.py --out /tmp/pkg  # 只构建目录
  python3 build/build_frog_package.py --no-zip        # 不打包
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parent
REPO = BUILD_DIR.parent
TEMPLATES = BUILD_DIR / 'templates'
PLATFORM = BUILD_DIR / 'platform'
DIST = BUILD_DIR / 'dist'
DESKTOP = Path.home() / 'Desktop'
ZIP_NAME = '青蛙-内容建设agent-上传包v37.zip'

# 内容建设链路的 13 个技能，按实际执行顺序排列
SKILLS = [
    'geo-doc-parse',
    'geo-layered-sampling',
    'geo-path-plan',
    'geo-content-plan',
    'geo-evidence',
    'geo-source-fetch',
    'geo-content-write',
    'geo-sku-rewrite',
    'geo-pdp',
    'geo-asset-render',
    'geo-translate',
    'geo-polish',
    'geo-diagnose',
]

# 分类器唯一实现（本地平台与青蛙工具共用这一段代码）
CLASSIFIER_SOURCE = REPO / 'geo-research' / 'scripts' / 'sample_by_stage.py'
CLASSIFIER_START = 'STAGE_ORDER = ('
CLASSIFIER_END = 'def build_question('


def read_frontmatter(text):
    """解析 SKILL.md 的 YAML 头部（只取 name / description）"""
    meta = {}
    match = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not match:
        return meta, text
    for line in match.group(1).splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            meta[key.strip()] = value.strip()
    return meta, text[match.end():]


def skill_title(body, name):
    """从一级标题取中文技能名，去掉括号里的英文名"""
    match = re.search(r'^#\s+(.+)$', body, re.M)
    if not match:
        return name
    return re.sub(r'（[^）]*）\s*$', '', match.group(1)).strip()


def collect_references(skill_dir):
    """收集 references 下的规则文件（排除 legacy 与嵌套副本）"""
    refdir = skill_dir / 'references'
    if not refdir.is_dir():
        return []
    items = []
    for path in sorted(refdir.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in ('.md', '.txt'):
            continue
        rel = path.relative_to(refdir)
        parts = rel.parts
        if any(p == 'legacy' for p in parts):
            continue
        # geo-polish 目录里有一份嵌套旧副本，跳过
        if skill_dir.name in parts:
            continue
        items.append((rel.as_posix(), path.read_text(encoding='utf-8').strip()))
    return items


def collect_assets(skill_dir):
    """收集 assets 下的 JSON 数据文件（如 factor_library.json），内联进提示词。

    青蛙包没有仓库目录结构，必须把默认数据一并内联，运行时才能读到 v1 草案因子库。
    """
    adir = skill_dir / 'assets'
    if not adir.is_dir():
        return []
    items = []
    for path in sorted(adir.rglob('*.json')):
        if not path.is_file():
            continue
        items.append((path.relative_to(adir).as_posix(), path.read_text(encoding='utf-8').strip()))
    return items


def build_prompt(skill):
    """生成青蛙提示词：平台适配 + 本地规则正文 + references 全文"""
    skill_dir = REPO / skill
    raw = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
    meta, body = read_frontmatter(raw)
    body = body.strip()
    refs = collect_references(skill_dir)
    assets = collect_assets(skill_dir)
    common = (PLATFORM / '_common.md').read_text(encoding='utf-8').strip()
    specific_path = PLATFORM / (skill + '.md')
    specific = specific_path.read_text(encoding='utf-8').strip() if specific_path.exists() else ''

    chunks = [
        '<!-- 本文件由 build/build_frog_package.py 自动生成，请勿手改。',
        '     规则源：%s/SKILL.md + references/（与本地、GitHub 同一份）。 -->' % skill,
        '',
        body,
        '',
        '---',
        '',
        common,
    ]
    if specific:
        chunks += ['', specific]
    chunks += [
        '',
        '---',
        '',
        '# 规则参考文件（与本地 references/ 全文一致，已内联，无需再读外部文件）',
    ]
    for rel, content in refs:
        chunks += ['', '## references/%s' % rel, '', content]
    if assets:
        chunks += ['', '---', '', '# 默认数据文件（与本地 assets/ 一致，已内联）']
        for rel, content in assets:
            chunks += ['', '## assets/%s' % rel, '', '```json', content, '```']
    chunks += [
        '',
        '---',
        '',
        '## 规则优先级声明',
        '- 上面「规则正文 + 规则参考文件」是唯一规则来源，与本地和 GitHub 完全一致。',
        '- 平台执行约定只说明运行方式，不得覆盖或简化规则；两者冲突时以规则正文为准。',
    ]
    return meta, '\n'.join(chunks).rstrip() + '\n'


def build_classifier_block():
    """从本地 sample_by_stage.py 抽出分类器代码块（唯一实现）"""
    text = CLASSIFIER_SOURCE.read_text(encoding='utf-8')
    start = text.index(CLASSIFIER_START)
    end = text.index(CLASSIFIER_END)
    block = text[start:end].rstrip()
    return (
        '# >>> STAGE-RULES:BEGIN 自动同步自 %s，禁止手改\n' % CLASSIFIER_SOURCE.name
        + block + '\n'
        + '# <<< STAGE-RULES:END\n'
    )


def build_sample_tool():
    """生成青蛙的 geo-sample.py：分类器段替换为本地唯一实现"""
    text = (TEMPLATES / 'tools' / 'geo-sample.py').read_text(encoding='utf-8')
    start = text.index(CLASSIFIER_START)
    end = text.index('def domain_of(url):')
    prefix = text[:start]
    suffix = text[end:]
    labels = (
        "STAGE_LABELS = {'ai_exposure': 'AI 曝光', 'pdp': '转化层', 'conversion': '对比决策'}\n"
        "PLATFORM_LABELS = {'chatgpt': 'ChatGPT', 'gemini': 'Gemini', 'perplexity': 'Perplexity', 'api': 'API 问答'}\n\n"
    )
    return prefix + labels + build_classifier_block() + '\n\n' + suffix


def build_agent_json(prompts_meta):
    """生成 agent.json：技能与描述来自本地 SKILL.md，其余平台字段沿用模板"""
    data = json.loads((TEMPLATES / 'agent.json').read_text(encoding='utf-8'))
    skills = []
    for skill in SKILLS:
        meta = prompts_meta[skill]
        skills.append({
            'skill_name': meta['title'],
            'skill_name_en': skill,
            'description': meta['description'],
            'skill_prompt_ref': './prompts/%s.md' % skill,
        })
    data['skills'] = skills
    data['agent']['skill_refs'] = list(SKILLS)  # 必须是字符串数组
    return data


def build_agent_md(prompts_meta):
    """生成 agent.md：保留平台编排模板，追加自动生成的技能清单"""
    text = (TEMPLATES / 'agent.md').read_text(encoding='utf-8')
    factor_block = build_factor_block()
    if factor_block:
        text = text.rstrip() + '\n\n' + factor_block
    lines = ['', '', '## 附：技能清单与规则源（自动生成，禁止手改）', '']
    lines.append('| 顺序 | 技能 | 作用 | 提示词 |')
    lines.append('|---|---|---|---|')
    for idx, skill in enumerate(SKILLS, 1):
        meta = prompts_meta[skill]
        lines.append('| %d | `%s` | %s | `prompts/%s.md` |'
                     % (idx, skill, meta['title'], skill))
    lines += [
        '',
        '> 以上 13 个技能与本地、GitHub 的 `geo-*/SKILL.md` 同源；',
        '> 青蛙提示词由构建脚本自动内联本地规则生成，三处规则一致。',
        '',
    ]
    return text.rstrip() + '\n' + '\n'.join(lines)


def build_factor_block():
    """把因子库压缩成系统提示词数据块：所有阶段都能读，避免 write/polish/diagnose 读不到方案提示词。"""
    path = REPO / 'geo-content-plan' / 'assets' / 'factor_library.json'
    if not path.exists():
        return ''
    try:
        lib = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return ''
    compact = {
        'version': lib.get('version'),
        'updated_at': lib.get('updated_at'),
        'calibration_rules': lib.get('calibration_rules') or {},
        'admission_factors': [
            {k: f.get(k) for k in ('factor_id', 'name', 'check', 'status') if f.get(k) is not None}
            for f in (lib.get('admission_factors') or [])
        ],
        'factors': [
            {k: f.get(k) for k in ('factor_id', 'name', 'category', 'stage', 'weight',
                                   'definition', 'check', 'action') if f.get(k) is not None}
            for f in (lib.get('factors') or [])
        ],
    }
    return '\n'.join([
        '## 附：因子库数据（自动生成，禁止手改；与本地 `factor_library.json` 同源）',
        '',
        '所有阶段（方案 / 成稿 / 诊断）都读这一份，不需要再找其它文件；'
        '矩阵 item 若带 `factor_details`，以 Brief 内联的定义为准（与这里同源）。'
        '准入因子一票否决、不参与权重；增益因子按层归一化（层内权重加和为 1）。',
        '',
        '```json',
        json.dumps(compact, ensure_ascii=False, indent=1),
        '```',
    ])


def write_zip(pkg_dir, zip_path):
    """打包：zip 根目录直接放 agent.json / agent.md / prompts / tools"""
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(pkg_dir.rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            zf.write(path, path.relative_to(pkg_dir).as_posix())
    return zip_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(DIST))
    parser.add_argument('--no-zip', action='store_true')
    parser.add_argument('--zip-name', default=ZIP_NAME)
    args = parser.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / 'prompts').mkdir(parents=True)
    (out / 'tools').mkdir(parents=True)

    prompts_meta = {}
    for skill in SKILLS:
        skill_dir = REPO / skill
        if not (skill_dir / 'SKILL.md').exists():
            sys.exit('缺少规则源：%s' % (skill_dir / 'SKILL.md'))
        meta, prompt = build_prompt(skill)
        meta['title'] = skill_title(prompt, skill)
        prompts_meta[skill] = meta
        (out / 'prompts' / (skill + '.md')).write_text(prompt, encoding='utf-8')
        print('  prompt  %-22s %6d 字符' % (skill, len(prompt)))

    # 工具：三个原样复制，geo-sample 重新注入统一分类器
    for src in sorted((TEMPLATES / 'tools').glob('*.py')):
        if src.name == 'geo-sample.py':
            (out / 'tools' / src.name).write_text(build_sample_tool(), encoding='utf-8')
        else:
            shutil.copy2(src, out / 'tools' / src.name)
    print('  tools   %d 个' % len(list((out / 'tools').glob('*.py'))))

    agent_json = build_agent_json(prompts_meta)
    (out / 'agent.json').write_text(json.dumps(agent_json, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'agent.md').write_text(build_agent_md(prompts_meta), encoding='utf-8')

    # 语法自检：生成的 python 工具必须可编译（内存编译，不落 .pyc）
    for py in (out / 'tools').glob('*.py'):
        compile(py.read_text(encoding='utf-8'), str(py), 'exec')

    print('构建完成：%s（%d 技能 / %d 工具）' % (out, len(SKILLS), len(list((out / 'tools').glob('*.py')))))
    if not args.no_zip:
        zip_path = DESKTOP / args.zip_name
        write_zip(out, zip_path)
        print('已打包：%s（%.1f KB）' % (zip_path, zip_path.stat().st_size / 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
