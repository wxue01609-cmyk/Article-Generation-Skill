#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容建设三端一致性校验：本地 ↔ GitHub ↔ 青蛙包。

检查项：
  1. 仓库 skill 与 ~/.codex/skills（本地平台实际读取）逐字节一致；
  2. 生成的青蛙提示词完整包含本地规则正文与 references（逐字覆盖 100%）；
  3. 分层分类器（本地 sample_by_stage.py vs 青蛙 geo-sample.py）输出 100% 一致；
  4. agent.json 注册 13 技能、引用文件齐全；
  5. agent.md 覆盖全部 13 技能。

用法：
  python3 build/parity_check.py
  python3 build/parity_check.py --pkg /tmp/frogv14   # 指定已构建的包目录
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

BUILD_DIR = Path(__file__).resolve().parent
REPO = BUILD_DIR.parent
LOCAL_SKILLS = Path.home() / '.codex' / 'skills'

SKILLS = [
    'geo-doc-parse', 'geo-layered-sampling', 'geo-path-plan', 'geo-content-plan',
    'geo-evidence', 'geo-source-fetch', 'geo-content-write', 'geo-sku-rewrite',
    'geo-pdp', 'geo-asset-render', 'geo-translate', 'geo-polish', 'geo-diagnose',
]

TEST_QUERIES = [
    'best pet water fountain 2026',
    'how to choose a pet water fountain for cats',
    'pet water fountain price',
    'pawflow pet water fountain specs',
    'pawflow pet water fountain return policy',
    'pawflow pet water fountain review reddit',
    'is petkit water fountain worth it',
    'pet water fountain vs bowl for dogs',
    'how to return pawflow pet water fountain',
    'pawflow G980H best price',
    'does pawflow G980H work with cats',
    'pet water fountain warranty',
    'top 10 pet water fountains under 50 dollars',
    'pawflow pet water fountain shipping time',
    'what is the difference between pawflow G980H and G980',
    'pawflow G980H customer service phone number',
    'how to install dash cam hardware kit',
    'what is a supercapacitor dash cam',
]

# 文档（geo-path-plan/references/01-stage-map.md 示例）与代码必须一致的关键词：不满足则发布前 FAIL
DOC_CONSISTENCY = {
    'how to install dash cam hardware kit': 'conversion',
    'what is a supercapacitor dash cam': 'ai_exposure',
    'how to clean robot vacuum': 'conversion',
    'how to choose a pet water fountain for cats': 'ai_exposure',
}

failures = []


def check(name, ok, detail=''):
    status = 'PASS' if ok else 'FAIL'
    print('  [%s] %s%s' % (status, name, ('  ' + detail) if detail else ''))
    if not ok:
        failures.append(name)
    return ok


def md5_of(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def normalize(text):
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.S)
    text = re.sub(r'\s+', '', text)
    return text


def canonical_of(skill):
    """本地规则正文 + references（与 build 脚本相同的文件集合）"""
    skill_dir = REPO / skill
    body = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
    body = re.sub(r'^---\n.*?\n---\n', '', body, flags=re.S).strip()
    parts = [body]
    refdir = skill_dir / 'references'
    if refdir.is_dir():
        for path in sorted(refdir.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in ('.md', '.txt'):
                continue
            rel = path.relative_to(refdir)
            if any(p == 'legacy' for p in rel.parts) or skill in rel.parts:
                continue
            parts.append((refdir / rel).read_text(encoding='utf-8').strip())
    return normalize('\n'.join(parts))


def rule_files_of(skill):
    """返回 (说明, 去格式化的规则文本) 列表：SKILL.md 正文 + 每个 references 文件"""
    skill_dir = REPO / skill
    raw = (skill_dir / 'SKILL.md').read_text(encoding='utf-8')
    body = re.sub(r'^---\n.*?\n---\n', '', raw, flags=re.S).strip()
    out = [('SKILL.md', normalize(body))]
    refdir = skill_dir / 'references'
    if refdir.is_dir():
        for path in sorted(refdir.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in ('.md', '.txt'):
                continue
            rel = path.relative_to(refdir)
            if any(p == 'legacy' for p in rel.parts) or skill in rel.parts:
                continue
            out.append((path.relative_to(skill_dir).as_posix(),
                        normalize((refdir / rel).read_text(encoding='utf-8'))))
    return out


def coverage_of(rules, prompt):
    """每个规则文件必须 100% 逐字出现在提示词中（去空白后子串匹配）"""
    nprompt = normalize(prompt)
    result = []
    for name, text in rules:
        if not text:
            continue
        ok = text in nprompt
        result.append((name, ok))
    return result


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pkg', default=str(BUILD_DIR / 'dist'))
    args = parser.parse_args()
    pkg = Path(args.pkg)

    print('== 1. 仓库 skill 与本地 ~/.codex/skills 一致性 ==')
    for skill in SKILLS:
        rp = REPO / skill / 'SKILL.md'
        lp = LOCAL_SKILLS / skill / 'SKILL.md'
        if not (rp.exists() and lp.exists()):
            check('%s 缺失' % skill, False, 'repo=%s local=%s' % (rp.exists(), lp.exists()))
            continue
        same = md5_of(rp) == md5_of(lp)
        # references 目录整体比对
        for sub in ('SKILL.md',):
            check('%s/%s' % (skill, sub), same, '' if same else '仓库与本地不一致，请先同步')
        for root_name in ('references',):
            rd, ld = rp.parent / root_name, lp.parent / root_name
            rf = {p.relative_to(rd).as_posix(): md5_of(p) for p in rd.rglob('*') if p.is_file()} if rd.is_dir() else {}
            lf = {p.relative_to(ld).as_posix(): md5_of(p) for p in ld.rglob('*') if p.is_file()} if ld.is_dir() else {}
            check('%s/%s' % (skill, root_name), rf == lf, '仓库与本地不一致' if rf != lf else '')

    print('== 2. 青蛙提示词逐字包含本地规则（每个规则文件 100%） ==')
    for skill in SKILLS:
        prompt_path = pkg / 'prompts' / (skill + '.md')
        if not prompt_path.exists():
            check('%s prompt 缺失' % skill, False)
            continue
        rules = rule_files_of(skill)
        prompt = prompt_path.read_text(encoding='utf-8')
        results = coverage_of(rules, prompt)
        bad = [n for n, ok in results if not ok]
        check('%s 共 %d 个规则文件全部内联' % (skill, len(rules)), not bad,
              ('缺失: %s' % ', '.join(bad)) if bad else '(%d 个文件, %d 字符规则全文)' % (len(rules), sum(len(t) for _, t in rules)))

    print('== 3. 分层分类器输出一致性 ==')
    local_mod = load_module(REPO / 'geo-research' / 'scripts' / 'sample_by_stage.py', 'local_sbs')
    frog_mod = load_module(pkg / 'tools' / 'geo-sample.py', 'frog_geo_sample')
    mism = 0
    for q in TEST_QUERIES:
        for brand, model in (('PawFlow', 'G980H'), ('Botslab', ''), ('', '')):
            a = local_mod.classify_stage(q, brand, model)
            b = frog_mod.classify_stage(q, brand, model)
            if a != b:
                mism += 1
                print('    不一致: q=%r brand=%r model=%r local=%s frog=%s' % (q, brand, model, a, b))
    check('分类器 %d×%d 组输出一致' % (len(TEST_QUERIES), 3), mism == 0,
          '不一致 %d 组' % mism if mism else '')
    for attr in ('STAGE_ORDER', 'TIE_PRIORITY', 'CONVERSION_HOWTO', 'STAGE_SIGNALS'):
        check('常量 %s 一致' % attr, getattr(local_mod, attr) == getattr(frog_mod, attr))

    print('== 3.2 文档（01-stage-map.md 示例）与代码一致性 ==')
    doc_bad = []
    for q, expected in DOC_CONSISTENCY.items():
        got = local_mod.classify_stage(q, '', '')['stage']
        if got != expected:
            doc_bad.append('%r 代码=%s 文档期望=%s' % (q, got, expected))
    check('文档 stage-map 示例与代码一致', not doc_bad, '；'.join(doc_bad) if doc_bad else '')


    print('== 3.3 stage-map 双文件一致性（path-plan 完整版 vs content-plan 镜像版） ==')
    canonical = REPO / 'geo-path-plan' / 'references' / '01-stage-map.md'
    mirror = REPO / 'geo-content-plan' / 'references' / 'stage-map.md'
    if canonical.exists() and mirror.exists():
        def table_rows(path):
            rows = []
            in_table = False
            for line in path.read_text(encoding='utf-8').splitlines():
                s = line.strip()
                if s.startswith('|'):
                    if in_table:
                        rows.append(re.sub(r'[|\s]+', '|', s.strip('|')).strip('|'))
                    else:
                        in_table = True
                else:
                    in_table = False
            return rows
        canonical_rows = table_rows(canonical)
        mirror_rows = table_rows(mirror)
        same = canonical_rows == mirror_rows
        # 镜像必须在开头声明源文件，防止变成独立规则
        declares = '01-stage-map.md' in '\n'.join(mirror.read_text(encoding='utf-8').split('\n')[:6])
        check('stage-map 镜像与完整版逐表一致', same,
              '' if same else ('canonical=%d 行 mirror=%d 行' % (len(canonical_rows), len(mirror_rows))))
        check('stage-map 镜像声明源文件', declares)
    else:
        check('stage-map 双文件存在', False, '缺少 canonical 或 mirror')

    print('== 4. agent.json 技能注册 ==')
    agent = json.loads((pkg / 'agent.json').read_text(encoding='utf-8'))
    names = [s['skill_name_en'] for s in agent.get('skills', [])]
    check('注册 13 技能', len(names) == 13 and set(names) == set(SKILLS))
    refs_ok = all((pkg / s['skill_prompt_ref'].lstrip('./')).exists() for s in agent.get('skills', []))
    check('skill_prompt_ref 文件齐全', refs_ok)
    for t in agent.get('tools', []):
        ref = t.get('code_content_ref', '')
        check('tool 文件 %s' % ref, (pkg / ref.lstrip('./')).exists())
    sr, tr = agent.get('agent', {}).get('skill_refs'), agent.get('agent', {}).get('tool_refs')
    check('agent.skill_refs 是字符串数组', isinstance(sr, list) and all(isinstance(x, str) for x in sr), repr(sr)[:80])
    check('agent.tool_refs 是字符串数组', isinstance(tr, list) and all(isinstance(x, str) for x in tr), repr(tr)[:80])

    print('== 5. agent.md 覆盖全部技能 ==')
    md = (pkg / 'agent.md').read_text(encoding='utf-8')
    missing = [s for s in SKILLS if s not in md]
    check('agent.md 覆盖 13 技能', not missing, '缺失: %s' % missing if missing else '')

    print('== 5.1 agent.md 阶段路由表 ==')
    routing = {
        'plan 方案': ['geo-doc-parse', 'geo-layered-sampling', 'geo-path-plan', 'geo-content-plan'],
        'write 成稿': ['geo-source-fetch', 'geo-evidence', 'geo-content-write', 'geo-sku-rewrite',
                       'geo-pdp', 'geo-asset-render', 'geo-translate', 'geo-polish'],
        'diagnose 诊断': ['geo-diagnose'],
    }
    rows = {}
    for line in md.splitlines():
        for stage_name in routing:
            if line.strip().startswith('| %s' % stage_name):
                rows[stage_name] = line
    check('阶段路由表 3 行齐全', len(rows) == 3, '缺失: %s' % [k for k in routing if k not in rows] if len(rows) != 3 else '')
    for stage_name, want in routing.items():
        line = rows.get(stage_name, '')
        miss = [w for w in want if w not in line]
        check('%s 路由技能齐全' % stage_name, not miss, '缺失: %s' % miss if miss else '')

    print('== 6. 本地平台编排锚点（与青蛙 agent.md 同构） ==')
    local_platform = Path(os.environ.get('GEO_PLATFORM_DIR') or '/Users/wangxue10/生文工具2')
    if local_platform.exists() and (local_platform / 'plan_builder.py').exists():
        pb = (local_platform / 'plan_builder.py').read_text(encoding='utf-8')
        plan_anchors = ['geo-layered-sampling', 'geo-path-plan', 'plan/path_plan.json',
                        'asset_id', 'primary_query', 'article_count', 'source_page']
        asset_anchors = ['geo-evidence', 'geo-polish', 'geo-translate', 'geo-sku-rewrite',
                         'geo-pdp', 'polish_report.json', 'stage_index.json']
        for label, anchors, text in (
                ('方案提示词', plan_anchors, pb),
                ('成稿提示词', asset_anchors, pb)):
            missing_a = [a for a in anchors if a not in text]
            check('本地 %s 锚点齐全' % label, not missing_a,
                  ('缺失: %s' % ', '.join(missing_a)) if missing_a else '')
        server = (local_platform / 'server.py').read_text(encoding='utf-8')
        # 成稿 Brief 下发 / 客户确认事实回填 / 5 类产出落盘：平台侧必须与青蛙 agent.md 同口径
        missing_s = [a for a in ('selected_stages', 'monitoring_json', 'frog_content_agent_params',
                                 'plan_matrix_json', 'confirmed_facts_json', 'frog_write_outputs')
                     if a not in server]
        check('server.py 透传字段', not missing_s, '缺失: %s' % missing_s if missing_s else '')
    else:
        print('  [SKIP] 未找到本地平台目录，跳过（可用 GEO_PLATFORM_DIR 指定）')

    print()
    if failures:
        print('校验结果：FAIL（%d 项）' % len(failures))
        for f in failures:
            print('  - ' + f)
        return 1

    print('== 7. 因子库一致性（本地 / GitHub / 青蛙包 / 平台根目录） ==')
    factor_srcs = [
        ('GitHub', REPO / 'geo-content-plan' / 'assets' / 'factor_library.json'),
        ('本地 skill', LOCAL_SKILLS / 'geo-content-plan' / 'assets' / 'factor_library.json'),
        ('平台根目录', local_platform / 'factor_library.json' if 'local_platform' in dir() else None),
    ]
    digests = {}
    for label, p in factor_srcs:
        if p is None or not p.exists():
            check('因子库 [%s] 存在' % label, False, '路径缺失: %s' % p)
            continue
        digests[label] = md5_of(p)
        check('因子库 [%s] 存在' % label, True, p.name)
    if len(digests) >= 2:
        ok = len(set(digests.values())) == 1
        check('因子库三端 MD5 一致', ok, ' / '.join('%s=%s' % (k, v[:8]) for k, v in digests.items()))
    # 青蛙包 agent.md 必须内嵌因子数据块（write/polish/diagnose 阶段读不到 plan 提示词）
    agent_md = (BUILD_DIR / 'dist' / 'agent.md')
    if agent_md.exists():
        atext = agent_md.read_text(encoding='utf-8')
        check('agent.md 内嵌因子库数据块', '## 附：因子库数据' in atext and 'F-G-001' in atext and 'admission_factors' in atext)
    else:
        check('agent.md 内嵌因子库数据块', False, 'dist/agent.md 不存在，请先构建')

    print('校验结果：PASS —— 本地 / GitHub / 青蛙三端规则一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())
