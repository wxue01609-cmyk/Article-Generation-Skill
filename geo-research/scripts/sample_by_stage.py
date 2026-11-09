#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按转化路径分层采样：把词包 query 分到 ai_exposure / pdp / conversion 三层，
逐条向 ChatGPT（或任意 OpenAI 兼容接口）提问，统计每层的品牌提及、引用链接与信号。

用法（在 geo-research 技能目录内运行）：
  python3 scripts/sample_by_stage.py --queries-file queries.txt \
      --brand Botslab --model G980H --competitors "70mai,Vantrue" \
      --out research/sampling.json

环境变量（与 ask_chatgpt.py 一致）：
  CHATGPT_API_KEY 必填；CHATGPT_API_BASE / CHATGPT_MODEL / CHATGPT_TIMEOUT 可选。

输出：research/sampling.json
  - stages：每层的 query 数、客户端品牌提及率、引用域名 Top、竞品提及 Top
  - items：逐条 query 的分层结果（打标、打分、回答摘要、引用链接、信号）
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from collections import Counter, defaultdict

try:
    from normalize_platform_answers import normalize_dir
except ImportError:
    normalize_dir = None

# ---------- 分层打标（转化路径：AI 曝光 / 转化层 / 对比决策） ----------
STAGE_ORDER = ('ai_exposure', 'pdp', 'conversion')
TIE_PRIORITY = ('ai_exposure', 'conversion', 'pdp')  # 并列时 AI 曝光 > 对比决策 > 转化层

STAGE_SIGNALS = {
    'ai_exposure': [
        (r'\b(best|top|#1|number one|recommend|首选|推荐)\b', 3),
        (r'\b(review|reviews|hands-on|评测|测评)\b', 3),
        (r'\b(vs|versus|compared|alternative|or better|对比)\b', 2),
        (r'\b(guide|how to choose|选购|教程)\b', 2),
        (r'\bhow to\b.*\b(choose|buy|select|pick|compare|evaluate)\b', 3),
        (r'\b(what is|what are|what\'s|what does|definition|什么是)\b', 2),
        (r'\bhow to\b', 1),
        (r'\bworth it\b', 1),
    ],
    'pdp': [
        (r'\b(price|cost|cheap|deal|buy|purchase|多少钱|价格)\b', 3),
        (r'\b(specs?|specification|dimensions|included|参数|规格)\b', 2),
        (r'\b(difference|differs)\b', 2),
    ],
    'conversion': [
        (r'\b(return|refund|cancel|exchange|退货|退款)\b', 3),
        (r'\b(warranty|guarantee|保修)\b', 3),
        (r'\b(shipping|delivery|ship|运费|发货)\b', 3),
        (r'\b(support|contact|customer service|客服)\b', 3),
        (r'\b(is it good for|does it work with|compatible|fit|能装|兼容)\b', 2),
        (r'\b(policy|policies)\b', 3),
        (r'\b(safe|reliable|legit|靠谱|安全)\b', 2),
    ],
}

CONVERSION_HOWTO = (r'\bhow to\b.*\b(return|cancel|exchange|claim|refund|warranty|install|set up|setup|troubleshoot|fix|repair|clean|use|replace|not working|doesn\'?t work|won\'?t work|stop working|用法|安装|清洗|设置)\b', 'conversion')


def classify_stage(query, brand='', model=''):
    """打分确定主层级与次层级；how to 售后词强制归转化，避免串台"""
    q = query.lower()
    scores = {s: 0 for s in STAGE_ORDER}
    for stage, rules in STAGE_SIGNALS.items():
        for pat, weight in rules:
            if re.search(pat, q):
                scores[stage] += weight
    # best/top/recommend + to buy → 榜单意图（exposure），抵消 pdp 的 buy 权重
    if re.search(r'\b(best|top|number one|recommend)\b.*\b(buy|purchase)\b', q):
        scores['pdp'] = max(0, scores['pdp'] - 2)
        scores['ai_exposure'] += 3
    # 品牌+型号加成：只证明「产品相关」，不决定层级
    qq = q
    if model and model.lower() in qq:
        scores['pdp'] += 2
        scores['ai_exposure'] += 1
    if brand and brand.lower() in qq:
        scores['pdp'] += 1
        scores['ai_exposure'] += 1
    # how to + 售后/操作词（install/setup/clean/use/not working…，与 geo-path-plan 的 stage-map 一致）→ 对比决策层
    if re.search(CONVERSION_HOWTO[0], q):
        scores['conversion'] += 4
        scores['ai_exposure'] = max(0, scores['ai_exposure'] - 3)
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], TIE_PRIORITY.index(kv[0])))
    primary = ranked[0][0]
    secondary = _secondary_stage(q, brand, model, primary)
    if secondary is None:
        # 规则没给出次节点时，退回到分数兜底：另一个层有明显信号（≥2）就做内链位
        for stage, score in ranked[1:]:
            if score >= 2 and stage != primary:
                secondary = stage
                break
    return {'stage': primary, 'secondary_stage': secondary, 'scores': scores}


def _secondary_stage(q, brand, model, primary):
    """次节点规则（与 geo-path-plan 的 01-stage-map.md 对齐）：
    一条 query 只认真写一篇（主节点），次节点只做「带一句 + 内链」，可为 None。
    优先级高于分数兜底，避免「品牌名 + 意图词」时该带的内链位丢失。"""
    has_brand = bool(brand and brand.lower() in q)
    has_model = bool(model and model.lower() in q)
    if primary == 'ai_exposure':
        if has_brand or has_model:
            return 'pdp'
        if re.search(r'\b(buy|price|cost|where to buy|purchase|多少钱|价格)\b', q):
            return 'conversion'
    elif primary == 'pdp':
        if re.search(r'\b(review|best|vs|versus|worth it|评测|对比)\b', q):
            return 'ai_exposure'
        if re.search(r'\b(return|refund|warranty|shipping|退货|退款|保修)\b', q):
            return 'conversion'
    elif primary == 'conversion':
        if has_brand or has_model:
            return 'pdp'
    return None


def build_question(query, brand='', model=''):
    """把 query 整理成自然问句；已是问句（含 ? 或疑问词开头）则原样使用"""
    q = query.strip()
    if '?' in q:
        return q
    low = q.lower()
    if re.match(r'^(what|which|how|is|are|does|do|can|should|where|why|best)\b', low):
        return q if q.endswith('?') else q + '?'
    if brand and model and re.search(r'(price|cost|return|warranty|shipping|policy|specs?|review)s?$', low):
        return 'What is the %s %s %s?' % (brand, model, q.replace(brand, '').replace(model, '').strip().strip(':,'))
    if brand and model:
        return 'Is the %s %s right for me? Give an honest answer with alternatives.' % (brand, model)
    return 'Tell me about "%s".' % q


SYSTEM_PROMPT = (
    "你是海外市场研究助手。请直接、完整地回答用户问题，先给结论再给理由；"
    "回答中如引用外部资料，必须注明来源链接；涉及商品时给出价格、评分、库存等可核验信息，"
    "拿不准的明确说无法确认。回答语言与问题一致。"
)


def ask_once(api_key, base, model, question, timeout):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "temperature": 0.2,
        "max_tokens": 3000,
    }
    request = urllib.request.Request(
        base.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError("接口返回格式异常: " + json.dumps(data, ensure_ascii=False)[:300])


def domain_of(url):
    return re.sub(r'^https?://(www\.)?', '', str(url or '')).split('/')[0].lower()


def analyze_answer(answer, brand, model, competitors, cited_sources=None, client_domains=None):
    ans = answer or ''
    # 引用来源的标题/摘要也算「AI 输出里出现」，否则只会看正文会漏掉品牌被引用的情况
    src = cited_sources or []
    src_text = ' '.join('%s %s' % (c.get('title') or '', c.get('snippet') or '') for c in src)
    low = ans.lower()
    both = (ans + ' ' + src_text).lower()
    cited_urls = [c.get('url') for c in src if c.get('url')] or re.findall(r'https?://[^\s)\]]+', ans)
    cited_domains = list(dict.fromkeys(domain_of(u) for u in cited_urls if u))
    brands_mentioned = []
    for name in competitors or []:
        name = name.strip()
        if name and name.lower() in both and name.lower() not in (brand or '').lower():
            brands_mentioned.append(name)
    signals = {
        'price_mentioned': bool(re.search(r'\$\s?\d|\b\d+(?:\.\d+)?\s*(usd|eur|gbp)\b', ans, re.I)),
        'rating_mentioned': bool(re.search(r'\b\d(?:\.\d)?/5\b|\b\d+\s*(reviews?|ratings?)\b', ans, re.I)),
        'availability_mentioned': bool(re.search(r'\b(in stock|out of stock|available)\b', ans, re.I)),
        'policy_mentioned': bool(re.search(r'\b(return|refund|warranty|shipping)\b', ans, re.I)),
    }
    # 客户官网是否被 AI 作为来源引用（GEO 核心指标，与「提及」分开统计）
    keys = [d.lower() for d in (client_domains or []) if d]
    if not keys and brand:
        keys = [re.sub(r'[^a-z0-9]', '', brand.lower())]
    client_cited_urls = [u for u in cited_urls
                         if any(k and k in re.sub(r'[^a-z0-9.]', '', domain_of(u)) for k in keys)]
    return {
        'mentions_client': bool(brand and brand.lower() in both) or bool(model and model.lower() in both),
        'client_cited': bool(client_cited_urls),
        'client_cited_urls': client_cited_urls[:5],
        'brands_mentioned': sorted(set(brands_mentioned)),
        'cited_urls': cited_urls[:10],
        'cited_domains': list(dict.fromkeys(cited_domains))[:10],
        'signals': signals,
    }


def analyze_products(cards, brand, model):
    """商品卡（爬虫产物）：统计出现数量、是否出现客户品牌/型号"""
    cards = cards or []
    mentioned = False
    low_brand = str(brand or '').lower()
    low_model = str(model or '').lower()
    for c in cards:
        blob = (' '.join(str(c.get('brand') or '') + ' ' + str(c.get('price_range') or '')).lower())
        if (low_brand and low_brand in blob) or (low_model and low_model in blob):
            mentioned = True
            break
    return {'product_cards': len(cards), 'products_mention_client': mentioned}


def aggregate(items):
    """按层级聚合，并细分平台子层（chatgpt / gemini / perplexity / api）"""
    stages = {}
    for stage in STAGE_ORDER:
        sub = [it for it in items if it['stage'] == stage and not it.get('error')]
        if not sub:
            stages[stage] = {'count': 0}
            continue

        def metrics(part):
            m = {
                'count': len(part),
                'mention_rate': round(sum(1 for it in part if it.get('mentions_client')) / len(part), 3),
                'cite_rate': round(sum(1 for it in part if it.get('client_cited')) / len(part), 3),
                'cited_domains': [d for d, _ in Counter(
                    d for it in part for d in it.get('cited_domains') or []).most_common(8)],
                'brands_mentioned': [b for b, _ in Counter(
                    b for it in part for b in it.get('brands_mentioned') or []).most_common(8)],
            }
            if any('product_cards' in it for it in part):
                m['product_card_rate'] = round(
                    sum(1 for it in part if it.get('product_cards', 0) > 0) / len(part), 3)
                m['products_mention_client'] = round(
                    sum(1 for it in part if it.get('products_mention_client')) / len(part), 3)
            return m

        base = metrics(sub)
        by_platform = defaultdict(list)
        for it in sub:
            by_platform[it.get('platform') or 'api'].append(it)
        base['platforms'] = {p: metrics(part) for p, part in sorted(by_platform.items())}
        stages[stage] = base
    return stages


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(),
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--queries-file', help='词包文件，每行一个 query（API 模式必填）')
    parser.add_argument('--answers', help='归一化答案：answers.jsonl 路径，或 Scrapeless 结果目录（自动归一化后分析）')
    parser.add_argument('--brand', default='', help='客户品牌，用于提及检测与打标加成')
    parser.add_argument('--model', default='', help='主力型号，用于提及检测与打标加成')
    parser.add_argument('--competitors', default='', help='竞品白名单，逗号分隔，用于提及统计')
    parser.add_argument('--client-domain', default='', help='客户域名（逗号分隔，如 botslab.com），用于统计官网被引用率；缺省用品牌名推断')
    parser.add_argument('--out', default='research/sampling.json', help='输出路径')
    parser.add_argument('--limit', type=int, default=0, help='最多采样条数（0 表示全部）')
    args = parser.parse_args()

    competitors = [c.strip() for c in args.competitors.split(',') if c.strip()]
    out_path = args.out
    items, errors = [], 0

    if args.answers:
        # 爬虫采集模式：读 Scrapeless 结果目录或答案文件，不调 API
        tmp_answers = os.path.join(os.path.dirname(out_path) or '.', '_answers.tmp.jsonl')
        if os.path.isdir(args.answers):
            if normalize_dir is None:
                print('错误：无法导入 normalize_platform_answers（需与 sample_by_stage.py 同目录）', file=sys.stderr)
                return 2
            rows, _ = normalize_dir(args.answers, tmp_answers, args.limit)
        else:
            rows = [json.loads(ln) for ln in open(args.answers, encoding='utf-8') if ln.strip()]
            if args.limit:
                rows = rows[:args.limit]
        for row in rows:
            query = str(row.get('query') or '')
            if not query:
                continue
            classified = classify_stage(query, args.brand, args.model)
            analyzed = analyze_answer(row.get('answer') or '', args.brand, args.model, competitors,
                                       row.get('cited_sources') or [],
                                       [d.strip() for d in args.client_domain.split(',') if d.strip()])
            analyzed.update(analyze_products(row.get('product_cards') or [], args.brand, args.model))
            items.append({
                'query': query,
                'platform': str(row.get('platform') or 'unknown'),
                'country': str(row.get('country') or ''),
                'stage': classified['stage'],
                'secondary_stage': classified['secondary_stage'],
                'scores': classified['scores'],
                'answer_summary': re.sub(r'\s+', ' ', str(row.get('answer') or ''))[:500],
                'error': '',
                **analyzed,
            })
        model = 'scrapeless(爬虫采集)'
        mode_note = 'answers'
        if os.path.exists(tmp_answers):
            os.remove(tmp_answers)
    else:
        # API 模式：逐条问接口
        if not args.queries_file:
            parser.error('需要 --queries-file（API 模式）或 --answers')
        queries = [ln.strip() for ln in open(args.queries_file, encoding='utf-8') if ln.strip()]
        if args.limit:
            queries = queries[:args.limit]
        api_key = os.environ.get('CHATGPT_API_KEY', '').strip()
        if not api_key:
            print('错误：未配置 CHATGPT_API_KEY', file=sys.stderr)
            return 1
        base = os.environ.get('CHATGPT_API_BASE', 'https://api.openai.com/v1').strip()
        model = os.environ.get('CHATGPT_MODEL', 'gpt-4o-mini').strip()
        timeout = float(os.environ.get('CHATGPT_TIMEOUT', '120').strip())
        for query in queries:
            classified = classify_stage(query, args.brand, args.model)
            question = build_question(query, args.brand, args.model)
            try:
                answer = ask_once(api_key, base, model, question, timeout)
            except Exception as exc:
                answer, errors = '', errors + 1
                error = str(exc)
            else:
                error = ''
            analyzed = analyze_answer(answer, args.brand, args.model, competitors) if answer else {}
            items.append({
                'query': query,
                'platform': 'api',
                'question': question,
                'stage': classified['stage'],
                'secondary_stage': classified['secondary_stage'],
                'scores': classified['scores'],
                'answer_summary': re.sub(r'\s+', ' ', answer)[:500],
                'error': error,
                **analyzed,
            })
        mode_note = 'api'

    ok_items = [it for it in items if not it.get('error')]
    stages = aggregate(items)
    result = {
        'generated_at': __import__('time').strftime('%Y-%m-%d %H:%M:%S'),
        'sampler': 'sample_by_stage.py',
        'source': mode_note,
        'model': model,
        'brand': args.brand,
        'competitors': competitors,
        'errors': errors,
        'platforms': sorted({it.get('platform') or 'api' for it in ok_items}),
        'stages': stages,
        'items': items,
    }
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print('已写入 %s，分析 %d 条 / 失败 %d 条，来源 %s' % (out_path, len(ok_items), errors, mode_note))
    for stage in STAGE_ORDER:
        info = stages[stage]
        if info.get('count'):
            line = '  %-12s %d 条 | 提及率 %s | 引用率 %s' % (stage, info['count'], info.get('mention_rate'), info.get('cite_rate'))
            if 'product_card_rate' in info:
                line += ' | 商品卡率 %s' % info['product_card_rate']
            line += ' | 平台: '
            line += ','.join(
                '%s(提及%s%%/引用%s%%)' % (p, int((v.get('mention_rate') or 0) * 100), int((v.get('cite_rate') or 0) * 100))
                for p, v in info.get('platforms', {}).items())
            print(line)
    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
