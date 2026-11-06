#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容矩阵机械校验（geo-content-plan）。

读取 <项目目录>/plan/content_matrix.json，按 matrix-schema.md 与 SKILL.md 的约束
逐项核对：字段名、stage 合法性、资产类型、target_url、内链闭环、summary 统计、
预算截断、SKU source_page 关联、竞品口径。

用法：
  python3 scripts/check_matrix.py --project <项目目录>
  python3 scripts/check_matrix.py --project <项目目录> --competitors "Botslab,PawFlow" --budget 10

退出码：有 blocking 项返回 1，否则 0（warning 不影响退出码）。
"""
import argparse
import json
import re
import sys
from pathlib import Path

STAGE_VALUES = {'ai_exposure', 'pdp', 'conversion'}
INTENT_VALUES = {'informational', 'commercial', 'transactional', 'navigational',
                 'support', 'community', 'news', 'local'}
PRIORITY_VALUES = {'P0', 'P1', 'P2'}
FUNNEL_VALUES = {'TOFU', 'MOFU', 'BOFU', 'Retention'}
ASSET_TYPE_ALL = {'blog', 'landing', 'sku', 'category', 'thirdparty_pr',
                  'thirdparty_review', 'qna', 'social', 'ecommerce', 'faq'}
OFFICIAL_ASSETS = {'blog', 'landing', 'category', 'faq', 'sku'}
ASSET_ID_RE = re.compile(r'^(blog|landing|sku|category|pr|review|qna|social|ecom|faq)-\d{2}$')
WORD_COUNT_RANGE = {
    'blog': (700, 1500), 'landing': (300, 700), 'sku': (150, 400),
    'category': (600, 1000), 'faq': (300, 600), 'qna': (150, 350),
    'pr': (400, 700), 'social': (0, 150), 'ecommerce': (200, 500),
}
MIN_OUTLINE = {'sku': 2, 'faq': 2}  # 其余资产默认 3


def check(results, level, name, detail=''):
    """记录一条校验结果：detail 为空视为通过，非空视为问题并计入。"""
    if detail:
        results.append((level, name, detail))
        print('  [%s] %s  %s' % (level.upper(), name, detail))
    else:
        print('  [PASS] %s' % name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True, help='项目目录（含 plan/content_matrix.json）')
    parser.add_argument('--competitors', default='', help='竞品品牌名，逗号分隔（校验官网资产不点名竞品）')
    parser.add_argument('--budget', type=int, default=0, help='资产总数上限（覆盖矩阵内/package.json）')
    parser.add_argument('--asset-types', default='', help='启用资产类型，逗号分隔')
    args = parser.parse_args()

    root = Path(args.project)
    matrix_path = root / 'plan' / 'content_matrix.json'
    results = []
    if not matrix_path.exists():
        check(results, 'blocking', '缺少 plan/content_matrix.json', str(matrix_path))
        _finish(results)
    try:
        matrix = json.loads(matrix_path.read_text(encoding='utf-8'))
    except Exception as e:
        check(results, 'blocking', 'content_matrix.json 不是合法 JSON', str(e))
        _finish(results)

    items = matrix.get('items')
    if not isinstance(items, list):
        check(results, 'blocking', '缺少 items 数组')
        items = []
    gaps = matrix.get('gaps') if isinstance(matrix.get('gaps'), list) else []
    summary = matrix.get('summary') if isinstance(matrix.get('summary'), dict) else {}
    fields = matrix.get('fields') if isinstance(matrix.get('fields'), dict) else {}

    # 字段名与唯一性
    ids, pqs = [], []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            check(results, 'blocking', 'items[%d] 不是对象' % idx)
            continue
        aid = item.get('asset_id')
        pq = item.get('primary_query')
        if not aid:
            check(results, 'blocking', 'items[%d] 缺 asset_id（注意不是 id）' % idx)
        if not pq:
            check(results, 'blocking', 'items[%d] 缺 primary_query（注意不是 query）' % idx)
        ids.append(aid)
        pqs.append(pq)

    dup_ids = {x for x in ids if ids.count(x) > 1}
    dup_pq = {x for x in pqs if pqs.count(x) > 1}
    check(results, 'blocking', 'asset_id 唯一', '重复: %s' % sorted(dup_ids) if dup_ids else '')
    check(results, 'blocking', 'primary_query 唯一', '重复: %s' % sorted(dup_pq) if dup_pq else '')

    # 启用资产类型
    enabled = set()
    for source in (args.asset_types, fields.get('asset_types', '')):
        if isinstance(source, str):
            enabled |= {x.strip() for x in source.replace('，', ',').split(',') if x.strip()}
    if not enabled:
        enabled = set(ASSET_TYPE_ALL)

    # 预算
    budget = args.budget or fields.get('asset_budget') or 0
    budget = int(budget) if budget else 0
    if budget and len(items) > budget:
        check(results, 'blocking', '资产数超预算',
              'items=%d > asset_budget=%d，应对剩余 query 做 budget 截断进 gaps' % (len(items), budget))

    # target_url / 内链闭环
    official_missing_url = [it.get('asset_id') for it in items
                            if isinstance(it, dict) and it.get('asset_type') in OFFICIAL_ASSETS
                            and not it.get('target_url')]
    check(results, 'blocking', '官网类资产 target_url 必填',
          '缺失: %s' % official_missing_url if official_missing_url else '')
    urls = {it.get('target_url') for it in items
            if isinstance(it, dict) and it.get('target_url')}
    dead = []
    for it in items:
        if not isinstance(it, dict):
            continue
        for link in it.get('internal_links') or []:
            target = link.get('target') if isinstance(link, dict) else None
            if isinstance(target, str) and target.startswith('/') and target not in urls:
                dead.append('%s → %s' % (it.get('asset_id'), target))
    check(results, 'blocking', '站内内链 target_url 闭环', '死链: %s' % dead if dead else '')

    seen_secondary = {}
    for idx, it in enumerate(items):
        if not isinstance(it, dict):
            continue
        aid = it.get('asset_id')
        stage, sstage = it.get('stage'), it.get('secondary_stage')
        check(results, 'blocking', '%s stage 合法' % aid,
              'stage=%r' % stage if stage not in STAGE_VALUES else '')
        if sstage in (None, ''):
            pass
        elif sstage not in STAGE_VALUES:
            check(results, 'blocking', '%s secondary_stage 合法' % aid, '值=%r' % sstage)
        elif sstage == stage:
            check(results, 'blocking', '%s secondary_stage 不等于 stage' % aid)
        if it.get('intent') not in INTENT_VALUES:
            check(results, 'blocking', '%s intent 合法' % aid, '值=%r' % it.get('intent'))
        if it.get('priority') not in PRIORITY_VALUES:
            check(results, 'blocking', '%s priority 合法' % aid, '值=%r' % it.get('priority'))
        if it.get('funnel') not in FUNNEL_VALUES:
            check(results, 'warning', '%s funnel 合法' % aid, '值=%r' % it.get('funnel'))
        atype = it.get('asset_type')
        if atype not in enabled:
            check(results, 'blocking', '%s asset_type 已启用' % aid, '值=%r 不在启用列表' % atype)
        if aid and not ASSET_ID_RE.match(str(aid)):
            check(results, 'warning', '%s asset_id 命名规范' % aid,
                  '应为 ^(blog|landing|sku|category|pr|review|qna|social|ecom|faq)-\\d{2}$')

        # outline
        outline = it.get('outline') if isinstance(it.get('outline'), list) else []
        min_n = MIN_OUTLINE.get(atype, 3)
        if len(outline) < min_n:
            check(results, 'blocking', '%s outline 数量' % aid, '需要 ≥%d，实际 %d' % (min_n, len(outline)))
        for sec in outline:
            if not isinstance(sec, dict) or not sec.get('h2') or not sec.get('points'):
                check(results, 'blocking', '%s outline 结构' % aid, '每项需含 h2 与 points(≥1)')
                break

        # word_count 档位
        wc = it.get('word_count')
        if wc and atype in WORD_COUNT_RANGE:
            lo, hi = WORD_COUNT_RANGE[atype]
            if not (lo <= wc <= hi):
                check(results, 'warning', '%s word_count 档位' % aid, '%s=%d，建议 %d-%d' % (atype, wc, lo, hi))

        # confidence / needs_review
        conf = it.get('confidence')
        if isinstance(conf, (int, float)) and 0 <= conf < 0.70 and not it.get('needs_review'):
            check(results, 'warning', '%s 低置信需标记' % aid, 'confidence=%s 但 needs_review=false' % conf)

        # source_page 关联
        sp = it.get('source_page')
        if sp is not None:
            if atype != 'sku':
                check(results, 'blocking', '%s source_page 只用于 sku' % aid)
            if not it.get('source_url'):
                check(results, 'warning', '%s source_url 缺失' % aid)
            if it.get('rewrite_mode') != 'existing_page':
                check(results, 'blocking', '%s rewrite_mode=existing_page' % aid)
            su = it.get('source_url')
            if su and it.get('target_url') != su:
                check(results, 'blocking', '%s target_url 等于 source_url' % aid,
                      'target=%s source=%s' % (it.get('target_url'), su))

        # 竞品口径：官网资产不得点名竞品
        competitors = [c.strip().lower() for c in args.competitors.replace('，', ',').split(',') if c.strip()]
        if competitors and atype in OFFICIAL_ASSETS:
            hay = ' '.join(str(it.get(k) or '') for k in
                           ('title', 'angle', 'key_points', 'proof_points', 'cta', 'primary_query'))
            hit = [c for c in competitors if c and c.lower() in hay.lower()]
            if hit:
                check(results, 'blocking', '%s 官网资产不点名竞品' % aid, '命中: %s' % hit)

        # 次查询重复复用检查
        for sq in it.get('secondary_queries') or []:
            seen_secondary.setdefault(sq, []).append(aid)

    # summary 一致性
    if 'total_queries' in summary:
        total = len(items) + len(gaps)
        if summary['total_queries'] != total:
            check(results, 'blocking', 'summary.total_queries 一致',
                  '声明=%d 实际(items+gaps)=%d' % (summary['total_queries'], total))
    stage_count = {}
    for it in items:
        s = it.get('stage') if isinstance(it, dict) else None
        stage_count[s] = stage_count.get(s, 0) + 1
    bs = summary.get('by_stage')
    if isinstance(bs, dict):
        diff = {k: (v, stage_count.get(k, 0)) for k, v in bs.items() if v != stage_count.get(k, 0)}
        if diff:
            check(results, 'blocking', 'summary.by_stage 一致', str(diff))
    bat = summary.get('by_asset_type')
    if isinstance(bat, dict):
        at_count = {}
        for it in items:
            a = it.get('asset_type') if isinstance(it, dict) else None
            at_count[a] = at_count.get(a, 0) + 1
        diff = {k: (v, at_count.get(k, 0)) for k, v in bat.items() if v != at_count.get(k, 0)}
        if diff:
            check(results, 'blocking', 'summary.by_asset_type 一致', str(diff))

    # gaps
    bad_gap = [g for g in gaps if not isinstance(g, dict) or not g.get('reason')]
    check(results, 'blocking', 'gaps 每项有 reason', '缺失 %d 项' % len(bad_gap) if bad_gap else '')

    _finish(results)


def _finish(results):
    """输出汇总并退出。"""
    blocking = [r for r in results if r[0] == 'blocking']
    warnings = [r for r in results if r[0] == 'warning']
    print()
    print('校验结果：%s（blocking=%d warning=%d）' % ('FAIL' if blocking else 'PASS', len(blocking), len(warnings)))
    if blocking:
        for level, name, _ in blocking:
            print('  - ' + name)
    sys.exit(1 if blocking else 0)


if __name__ == '__main__':
    main()
