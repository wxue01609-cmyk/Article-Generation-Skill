#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Scrapeless 批量采集结果目录归一化成 answers.jsonl（统一采样契约）。

用法（在 geo-research 技能目录内运行）：
  python3 scripts/normalize_platform_answers.py --dir <结果根目录> --out answers.jsonl [--limit N]

结果目录结构（scrapeless-demo 输出）：
  <root>/scraper.chatgpt/US/0001.json
  <root>/scraper.gemini/US/0002.json
每个 JSON：
  {"status":"success","task_result":{"prompt":"...","result_text":"...","rawtext":"...",
    "citations":[{"title","url","website_name","snippet","highlights"}],
    "products":[{"brand","price_range","rating","reviews","about_the_product":{"link"},"stores":[...]}]}}

输出 answers.jsonl，每行一个 JSON：
  {"query","platform","country","answer","cited_urls","cited_sources","product_cards"}

platform 由目录名映射：scraper.chatgpt→chatgpt，scraper.gemini→gemini，scraper.perplexity→perplexity。
"""
import argparse
import json
import sys
from pathlib import Path

FALLBACK_PHRASES = (
    "encountering an error",
    "having a hard time fulfilling",
    "something went wrong",
    "please try your request again",
)

ACTOR_PLATFORM = {
    'scraper.chatgpt': 'chatgpt', 'chatgpt': 'chatgpt',
    'scraper.gemini': 'gemini', 'gemini': 'gemini',
    'scraper.perplexity': 'perplexity', 'perplexity': 'perplexity',
}


def platform_of(actor):
    key = str(actor or '').strip().lower()
    return ACTOR_PLATFORM.get(key, key or 'unknown')


def normalize_json(path, platform):
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or str(data.get('status', '')).lower() != 'success':
        return None
    tr = data.get('task_result') or {}
    answer = str(tr.get('result_text') or tr.get('rawtext') or '').strip()
    if not answer or any(p in answer.lower() for p in FALLBACK_PHRASES):
        return None
    # 引用来源两个字段都要收：Gemini 放在 citations，ChatGPT 放在 search_result
    sources = []
    for c in (tr.get('citations') or []):
        if not isinstance(c, dict) or not c.get('url'):
            continue
        sources.append({
            'title': str(c.get('title') or ''),
            'url': str(c.get('url')),
            'domain': str(c.get('website_name') or ''),
            'snippet': str(c.get('snippet') or (c.get('highlights') or [''])[0] or '')[:300],
        })
    for c in (tr.get('search_result') or []):
        if not isinstance(c, dict) or not c.get('url'):
            continue
        sources.append({
            'title': str(c.get('title') or ''),
            'url': str(c.get('url')),
            'domain': str(c.get('attribution') or ''),
            'snippet': str(c.get('snippet') or '')[:300],
        })
    seen, cited = set(), []
    for src in sources:
        if src['url'] in seen:
            continue
        seen.add(src['url'])
        cited.append(src)
    cards = []
    for p in (tr.get('products') or [])[:20]:
        if not isinstance(p, dict):
            continue
        cards.append({
            'brand': str(p.get('brand') or ''),
            'price_range': str(p.get('price_range') or ''),
            'rating': str(p.get('rating') or ''),
            'reviews': p.get('reviews') or 0,
            'link': str((p.get('about_the_product') or {}).get('link') or ''),
        })
    query = str(tr.get('prompt') or '').strip()
    if not query or not answer:
        return None
    return {
        'query': query,
        'platform': platform,
        'country': str(path.parent.name or ''),
        'answer': answer,
        'cited_urls': [c['url'] for c in cited[:10]],
        'cited_sources': cited[:10],
        'product_cards': cards,
    }


def normalize_dir(root, out_path, limit=0):
    root = Path(root)
    paths = sorted(p for p in root.rglob('*.json') if p.name != 'mention-summary.json')
    rows, skipped = [], 0
    for p in paths:
        rel = p.relative_to(root)
        actor = rel.parts[0] if len(rel.parts) > 1 else 'unknown'
        try:
            item = normalize_json(p, platform_of(actor))
        except Exception:
            skipped += 1
            continue
        if not item:
            skipped += 1
            continue
        rows.append(item)
        if limit and len(rows) >= limit:
            break
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    return rows, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(),
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dir', required=True, help='Scrapeless 结果根目录')
    parser.add_argument('--out', default='answers.jsonl', help='输出 answers.jsonl 路径')
    parser.add_argument('--limit', type=int, default=0, help='最多归一化条数（0 表示全部）')
    args = parser.parse_args()
    rows, skipped = normalize_dir(args.dir, args.out, args.limit)
    platforms = {}
    for r in rows:
        platforms[r['platform']] = platforms.get(r['platform'], 0) + 1
    print('已写入 %s，共 %d 条（跳过 %d 条失败/不可用）' % (args.out, len(rows), skipped))
    for p, n in sorted(platforms.items()):
        print('  %-12s %d 条' % (p, n))
    return 0 if rows else 1


if __name__ == '__main__':
    sys.exit(main())
