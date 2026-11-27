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
import pathlib
import zipfile
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parent
REPO = BUILD_DIR.parent
TEMPLATES = BUILD_DIR / 'templates'
PLATFORM = BUILD_DIR / 'platform'
DIST = BUILD_DIR / 'dist'
DESKTOP = Path.home() / 'Desktop'
ZIP_PREFIX = '青蛙-内容建设agent-上传包'
ZIP_NAME = ZIP_PREFIX + 'v41.zip'


def package_dir(desktop=None):
    """青蛙包统一放桌面「青蛙skill更新迭代」目录；该目录不存在时退回桌面根目录"""
    base = pathlib.Path(desktop or DESKTOP)
    archive = base / '青蛙skill更新迭代'
    return archive if archive.is_dir() else base


def next_zip_name(desktop=None):
    """按已有包的最大版本号 +1，避免每次重建都覆盖同一个旧版本号"""
    desktop = package_dir(desktop)
    top = 0
    for f in desktop.glob(ZIP_PREFIX + 'v*.zip'):
        m = re.search(r'v(\d+)\.zip$', f.name)
        if m:
            top = max(top, int(m.group(1)))
    return '%sv%d.zip' % (ZIP_PREFIX, top + 1)

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

# 青蛙平台技能提示词字段是 MySQL TEXT，上限 65535 字节，超了会被静默截断
PROMPT_LIMIT_BYTES = 65535
PROMPT_WARN_BYTES = 63000

# 超出上限的技能不再内联这两个数据块（因子库已在系统提示词里，词库只在成稿/质检用）
SKIP_ASSET_INLINE = {
    'geo-content-plan': ('factor_library.json', 'locale_profiles.json'),
}

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


def minify_json(text):
    """压缩 JSON：去掉缩进空白，降低提示词体积（平台单字段上限 64KB）"""
    try:
        return json.dumps(json.loads(text), ensure_ascii=False, separators=(',', ':'))
    except Exception:
        return text


def collect_assets(skill_dir, skip=()):
    """收集 assets 下的 JSON 数据文件（如 factor_library.json），压缩后内联进提示词。

    青蛙包没有仓库目录结构，必须把默认数据一并内联，运行时才能读到 v1 草案因子库；
    skip 里的文件不内联（用于规避平台 64KB 单字段上限），改由提示词说明数据来源。
    """
    adir = skill_dir / 'assets'
    if not adir.is_dir():
        return []
    items = []
    for path in sorted(adir.rglob('*.json')):
        if not path.is_file():
            continue
        rel = path.relative_to(adir).as_posix()
        if rel in skip:
            continue
        items.append((rel, minify_json(path.read_text(encoding='utf-8').strip())))
    return items


def market_aliases_block(skill_dir):
    """取出词库的市场别名表（很小），供方案阶段解析目标市场代码"""
    path = skill_dir / 'assets' / 'locale_profiles.json'
    if not path.exists():
        return ''
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return ''
    aliases = data.get('market_aliases') or {}
    if not aliases:
        return ''
    return json.dumps(aliases, ensure_ascii=False, separators=(',', ':'))


def build_prompt(skill):
    """生成青蛙提示词：平台适配 + 本地规则正文 + references 全文"""
    skill_dir = REPO / skill
    raw = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
    meta, body = read_frontmatter(raw)
    body = body.strip()
    refs = collect_references(skill_dir)
    skip_assets = SKIP_ASSET_INLINE.get(skill, ())
    assets = collect_assets(skill_dir, skip_assets)
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
    if skip_assets:
        chunks += ['', '---', '', '# 默认数据文件（未内联：超出平台单字段 64KB 上限）',
                   '', '青蛙平台单个提示词字段上限 64KB，以下数据不在本技能重复内联：']
        for rel in skip_assets:
            if rel == 'factor_library.json':
                chunks += ['', '- `assets/%s`：全文在系统提示词 `agent.md` 末尾「因子库数据」块（与本地同源），'
                               '直接按 `factor_id` 引用，不要再找文件。' % rel]
            elif rel == 'locale_profiles.json':
                chunks += ['', '- `assets/%s`：词库全文内联在成稿 `geo-content-write` 与质检 `geo-polish` 提示词中；'
                               '本阶段只用下面的市场别名表解析市场代码，具体用词约束由成稿阶段执行。' % rel,
                           '', '```json', market_aliases_block(skill_dir), '```']
            else:
                chunks += ['', '- `assets/%s`：数据较大，未内联，运行时按规则说明取平台侧同源数据。' % rel]
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
    # Agent Key 只允许英文字母、中划线、下划线；带数字会被青蛙平台拒绝，打包时直接拦下
    _key = str((data.get('agent') or {}).get('agent_key') or '')
    if not re.fullmatch(r'[A-Za-z_-]+', _key):
        raise SystemExit('agent_key 只允许英文字母、中划线 - 和下划线 _，且不允许数字：%r' % _key)
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
    parser.add_argument('--zip-name', default=None)
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
        size = len(prompt.encode('utf-8'))
        if size > PROMPT_LIMIT_BYTES:
            sys.exit('提示词超出青蛙单字段上限：%s = %d 字节 > %d（会被平台截断）'
                     % (skill, size, PROMPT_LIMIT_BYTES))
        flag = '  ⚠ 接近上限' if size > PROMPT_WARN_BYTES else ''
        print('  prompt  %-22s %6d 字符 %7d 字节%s' % (skill, len(prompt), size, flag))

    # 工具：三个原样复制，geo-sample 重新注入统一分类器
    for src in sorted((TEMPLATES / 'tools').glob('*.py')):
        if src.name == 'geo-sample.py':
            (out / 'tools' / src.name).write_text(build_sample_tool(), encoding='utf-8')
        else:
            shutil.copy2(src, out / 'tools' / src.name)
    print('  tools   %d 个' % len(list((out / 'tools').glob('*.py'))))

    agent_json = build_agent_json(prompts_meta)
    (out / 'agent.json').write_text(json.dumps(agent_json, ensure_ascii=False, indent=2), encoding='utf-8')
    # 系统提示词同样是 MySQL TEXT 字段：超限会被静默截断，必须在打包时硬拦
    agent_md = build_agent_md(prompts_meta)
    md_bytes = len(agent_md.encode('utf-8'))
    if md_bytes > PROMPT_LIMIT_BYTES:
        sys.exit('系统提示词 agent.md 超出青蛙单字段上限：%d 字节 > %d（会被平台截断）'
                 % (md_bytes, PROMPT_LIMIT_BYTES))
    md_flag = '  ⚠ 接近上限' if md_bytes > PROMPT_WARN_BYTES else ''
    print('  prompt  %-22s %6d 字符 %7d 字节%s' % ('agent.md', len(agent_md), md_bytes, md_flag))
    (out / 'agent.md').write_text(agent_md, encoding='utf-8')

    # 语法自检：生成的 python 工具必须可编译（内存编译，不落 .pyc）
    for py in (out / 'tools').glob('*.py'):
        compile(py.read_text(encoding='utf-8'), str(py), 'exec')

    print('构建完成：%s（%d 技能 / %d 工具）' % (out, len(SKILLS), len(list((out / 'tools').glob('*.py')))))
    if not args.no_zip:
        zip_path = package_dir() / (args.zip_name or next_zip_name())
        write_zip(out, zip_path)
        print('已打包：%s（%.1f KB）' % (zip_path, zip_path.stat().st_size / 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
