#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分层采样工具：把词包 query 按转化路径（AI 曝光 / 商品详情页 / 购买转化）分层，
统计每层的样本数、品牌提及率、来源引用率、商品卡率，输出平台×层基线表与 query→stage 映射。

三种模式（按优先级）：
  1. samples_json：直接使用已算好的采样结果（本地平台 research/sampling.json 结构），只做解析与格式化，不联网；
  2. answers_json：传入真实平台答案数组（query/platform/answer/cited_sources/product_cards），内置聚合；
  3. 离线分层：只对 topics 逐条打标（内置规则），不调接口，输出会注明「离线分层，非真实采样」。
  可选 API 采样：同时提供 api_base/api_key/model 时，可对每条 query 调用 OpenAI 兼容接口做问答采样（真实模型回答）。

输出（JSON）：
  {status, source, sample_count, query_stage: {query: stage}, stages: {...}, markdown: 基线表文本}
"""
import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict

STAGE_ORDER = ('ai_exposure', 'pdp', 'conversion')
TIE_PRIORITY = ('ai_exposure', 'conversion', 'pdp')
STAGE_LABELS = {'ai_exposure': 'AI 曝光', 'pdp': '商品详情页', 'conversion': '购买转化'}
PLATFORM_LABELS = {'chatgpt': 'ChatGPT', 'gemini': 'Gemini', 'perplexity': 'Perplexity', 'api': 'API 问答'}

STAGE_SIGNALS = {
    'ai_exposure': [
        (r'\b(best|top|#1|number one|recommend|首选|推荐)\b', 3),
        (r'\b(review|reviews|hands-on|评测|测评)\b', 3),
        (r'\b(vs|versus|compared|alternative|or better|对比)\b', 2),
        (r'\b(guide|how to choose|选购|教程)\b', 2),
        (r'\bhow to\b', 3),
        (r'\bworth it\b', 1),
    ],
    'pdp': [
        (r'\b(price|cost|cheap|deal|buy|purchase|多少钱|价格)\b', 3),
        (r'\b(specs?|specification|dimensions|included|what is|what\'s|参数|规格)\b', 2),
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
CONVERSION_HOWTO = (r'\bhow to\b.*\b(return|cancel|exchange|claim|refund|warranty)\b', 'conversion')


def classify_stage(query, brand='', model=''):
    """打分确定主层级与次层级；how to 售后词强制归转化"""
    q = query.lower()
    scores = {s: 0 for s in STAGE_ORDER}
    for stage, rules in STAGE_SIGNALS.items():
        for pat, weight in rules:
            if re.search(pat, q):
                scores[stage] += weight
    if re.search(r'\b(best|top|number one|recommend)\b.*\b(buy|purchase)\b', q):
        scores['pdp'] = max(0, scores['pdp'] - 2)
        scores['ai_exposure'] += 3
    if model and model.lower() in q:
        scores['pdp'] += 2
        scores['ai_exposure'] += 1
    if brand and brand.lower() in q:
        scores['pdp'] += 1
        scores['ai_exposure'] += 1
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
    一条 query 只认真写一篇（主节点），次节点只做「带一句 + 内链」，可为 None。"""
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


def domain_of(url):
    return re.sub(r'^https?://(www\.)?', '', str(url or '')).split('/')[0].lower()


def normalize_sources(cited_sources):
    """引用来兼容三种写法：对象数组（title/url/snippet）、URL 字符串数组、单个字符串"""
    if not cited_sources:
        return []
    if isinstance(cited_sources, str):
        return [{'url': u} for u in re.findall(r'https?://[^\s)\]，,]+', cited_sources)]
    if isinstance(cited_sources, dict):
        cited_sources = [cited_sources]
    rows = []
    for item in cited_sources:
        if isinstance(item, dict):
            rows.append(item)
        elif isinstance(item, str) and item.strip():
            text = item.strip()
            rows.append({'url': text} if text.startswith('http') else {'title': text})
    return rows


def analyze_answer(answer, brand, model, competitors, cited_sources=None, client_domains=None):
    ans = answer or ''
    src = normalize_sources(cited_sources)
    src_text = ' '.join('%s %s' % (c.get('title') or '', c.get('snippet') or '') for c in src)
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
    cards = cards or []
    if isinstance(cards, dict):
        cards = [cards]
    mentioned = False
    low_brand = str(brand or '').lower()
    low_model = str(model or '').lower()
    for c in cards:
        if isinstance(c, str):
            c = {'name': c}
        blob = (' '.join(str(c.get('brand') or '') + ' ' + str(c.get('price_range') or '') + ' ' + str(c.get('name') or '')).lower())
        if (low_brand and low_brand in blob) or (low_model and low_model in blob):
            mentioned = True
            break
    return {'product_cards': len(cards), 'products_mention_client': mentioned}


def aggregate(items):
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
            by_platform[it.get('platform') or 'unknown'].append(it)
        base['platforms'] = {p: metrics(part) for p, part in by_platform.items()}
        stages[stage] = base
    return stages


def make_markdown(result):
    """平台×层基线的 Markdown 表格"""
    lines = []
    for stage in STAGE_ORDER:
        info = result.get('stages', {}).get(stage) or {}
        if not info.get('count'):
            continue
        subs = info.get('platforms') or {}
        for pl, m in subs.items():
            lines.append('| %s | %s | %s | %s | %s | %s |' % (
                STAGE_LABELS.get(stage, stage), PLATFORM_LABELS.get(pl, pl),
                m.get('count', 0),
                ('%.1f%%' % ((m.get('mention_rate') or 0) * 100)),
                ('%.1f%%' % ((m.get('cite_rate') or 0) * 100)),
                ('%.1f%%' % ((m.get('product_card_rate') or 0) * 100)) if 'product_card_rate' in m else '-'))
        lines.append('| **%s 合计** | 全部 | %s | %s | %s | %s |' % (
            STAGE_LABELS.get(stage, stage), info.get('count', 0),
            ('%.1f%%' % ((info.get('mention_rate') or 0) * 100)),
            ('%.1f%%' % ((info.get('cite_rate') or 0) * 100)),
            ('%.1f%%' % ((info.get('product_card_rate') or 0) * 100)) if 'product_card_rate' in info else '-'))
    head = '| 转化层 | 平台 | 样本数 | 品牌提及率 | 来源引用率 | 商品卡率 |\n|---|---|---|---|---|---|\n'
    text = ('分层采样基线（%s，共 %s 条样本）\n\n' % (result.get('source_label') or result.get('source') or '',
                                                 result.get('sample_count') or 0)) + head + '\n'.join(lines)
    cites = result.get('citations') or []
    if cites:
        text += '\n\n### 引用内容参考（AI 实际引用的页面）\n\n| 层级 | 标题 | 来源 | 状态 |\n|---|---|---|---|\n'
        for c in cites:
            status = '已抓取' if c.get('status') == 'ok' else ('抓取失败' if c.get('status') == 'error' else '解析为空')
            text += '| %s | %s | %s | %s |\n' % (
                STAGE_LABELS.get(c.get('stage') or '', c.get('stage') or ''),
                (c.get('title') or c.get('url') or '')[:60].replace('|', '/'),
                c.get('domain') or '-', status)
    return text


def parse_topics(topics):
    """topics 字符串 → query 列表"""
    qs = []
    try:
        tp = json.loads(topics or '[]')
        for t in (tp if isinstance(tp, list) else []):
            if not isinstance(t, dict):
                continue
            for q in (t.get('queries') or []):
                v = str(q).strip()
                if v and v not in qs:
                    qs.append(v)
    except Exception:
        pass
    if not qs and topics:
        for ln in str(topics).splitlines():
            v = ln.strip()
            if v and v not in qs:
                qs.append(v)
    return qs


def ask_once(api_key, base, model, question, timeout=120):
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': (
                '你是海外市场研究助手。请直接、完整地回答用户问题，先给结论再给理由；'
                '回答中如引用外部资料，必须注明来源链接；涉及商品时给出价格、评分、库存等可核验信息，'
                '拿不准的明确说无法确认。回答语言与问题一致。')},
            {'role': 'user', 'content': question},
        ],
        'temperature': 0.2,
        'max_tokens': 3000,
    }
    req = urllib.request.Request(
        base.rstrip('/') + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + api_key},
        method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    try:
        return data['choices'][0]['message']['content']
    except (KeyError, IndexError):
        raise RuntimeError('接口返回格式异常: ' + json.dumps(data, ensure_ascii=False)[:300])


def run(params):
    """执行采样，返回结果 dict。异常时返回 status=error 的结果，不抛给上层"""
    topics = str(params.get('topics') or '')
    brand = str(params.get('brand') or '')
    model = str(params.get('model') or '')
    competitors = [c.strip() for c in re.split(r'[\n,，、;；]', str(params.get('competitors') or '')) if c.strip()]
    client_domains = [d.strip() for d in str(params.get('client_domains') or '').replace('\n', ',').split(',') if d.strip()]
    queries = parse_topics(topics)
    if not queries:
        return {'status': 'error', 'message': 'topics 为空，无法分层采样', 'query_stage': {}, 'stages': {}}
    max_q = int(params.get('max_queries') or '20')
    queries = queries[:max_q]
    result = {
        'status': 'ok',
        'source': '',
        'source_label': '',
        'brand': brand,
        'sample_count': 0,
        'query_stage': {},
        'query_secondary_stage': {},
        'stages': {},
        'citations': [],
        'markdown': '',
        'items': [],
    }
    # 引用内容参考：平台随任务带来的「AI 实际引用的第三方页面」摘要（可为空）
    try:
        raw_cj = str(params.get('citations_json') or '').strip()
        if raw_cj:
            parsed_cj = json.loads(raw_cj)
            if isinstance(parsed_cj, list):
                result['citations'] = parsed_cj
            elif isinstance(parsed_cj, dict) and parsed_cj.get('items'):
                result['citations'] = parsed_cj['items']
    except Exception as exc:
        result['message'] = 'citations_json 解析失败：%s' % exc
    # 模式 1：直接用现成采样结果
    samples_json = params.get('samples_json') or ''
    if samples_json and samples_json.strip():
        try:
            data = json.loads(samples_json)
        except Exception as exc:
            data = None
            result['message'] = 'samples_json 解析失败：%s' % exc
        if isinstance(data, dict) and data.get('stages'):
            result['source'] = str(data.get('source') or 'samples')
            result['source_label'] = ('已有采样结果' + ('（%s）' % result['source']))
            result['sample_count'] = len(data.get('items') or [])
            result['stages'] = data.get('stages') or {}
            if not result['citations']:
                result['citations'] = data.get('citations') or []
            for it in data.get('items') or []:
                q = str(it.get('query') or '').strip()
                if q:
                    result['query_stage'][q] = it.get('stage') or ''
                    result['query_secondary_stage'][q] = it.get('secondary_stage') or ''
            result['markdown'] = make_markdown(result)
            return result
    # 模式 2：API 问答采样（有 api_base/api_key 时）
    api_key = str(params.get('api_key') or '')
    base = str(params.get('api_base') or '')
    api_model = str(params.get('api_model') or 'gpt-4o-mini')
    if api_key and base:
        items = []
        errors = 0
        for q in queries:
            cls = classify_stage(q, brand, model)
            try:
                answer = ask_once(api_key, base, api_model, q + '?' if not q.endswith('?') else q)
            except Exception as exc:
                errors += 1
                answer = ''
                error = str(exc)[:200]
            else:
                error = ''
            analyzed = analyze_answer(answer, brand, model, competitors,
                                      None, client_domains) if answer else {}
            items.append({'query': q, 'platform': 'api', 'stage': cls['stage'],
                          'secondary_stage': cls['secondary_stage'], 'error': error, **analyzed})
        ok = [it for it in items if not it.get('error')]
        result['source'] = 'api'
        result['source_label'] = 'API 问答采样（%s）' % api_model
        result['sample_count'] = len(ok)
        result['items'] = [{'query': x['query'], 'stage': x['stage']} for x in ok]
        for x in ok:
            result['query_stage'][x['query']] = x['stage']
            result['query_secondary_stage'][x['query']] = x.get('secondary_stage') or ''
        result['stages'] = aggregate(items)
        result['markdown'] = make_markdown(result)
        return result
    # 模式 3：给答案数组直接聚合（爬虫/平台已采集的真实答案）
    raw_answers = params.get('answers_json') or ''
    if isinstance(raw_answers, (list, dict)):
        rows = raw_answers
    elif isinstance(raw_answers, str) and raw_answers.strip():
        try:
            rows = json.loads(raw_answers)
        except Exception as exc:
            return {'status': 'error', 'message': 'answers_json 解析失败：%s' % exc,
                    'query_stage': {}, 'stages': {}, 'markdown': ''}
    else:
        rows = None
    if rows is not None:
        if isinstance(rows, dict):
            rows = [rows]
        if isinstance(rows, list):
            items = []
            for row in rows:
                q = str(row.get('query') or '')
                if not q:
                    continue
                cls = classify_stage(q, brand, model)
                analyzed = analyze_answer(row.get('answer') or '', brand, model, competitors,
                                          row.get('cited_sources') or [], client_domains)
                analyzed.update(analyze_products(row.get('product_cards') or [], brand, model))
                items.append({'query': q, 'platform': str(row.get('platform') or 'unknown'),
                              'stage': cls['stage'], 'secondary_stage': cls['secondary_stage'],
                              'error': '', **analyzed})
            ok = [it for it in items if not it.get('error')]
            result['source'] = 'answers'
            result['source_label'] = '答案数组聚合（真实采集数据）'
            result['sample_count'] = len(ok)
            result['items'] = [{'query': x['query'], 'stage': x['stage']} for x in ok]
            for x in ok:
                result['query_stage'][x['query']] = x['stage']
                result['query_secondary_stage'][x['query']] = x.get('secondary_stage') or ''
            result['stages'] = aggregate(items)
            result['markdown'] = make_markdown(result)
            return result
    # 模式 4：离线分层（不给任何数据/接口时）
    items = []
    for q in queries:
        cls = classify_stage(q, brand, model)
        items.append({'query': q, 'platform': 'offline', 'stage': cls['stage'],
                      'secondary_stage': cls['secondary_stage'], 'error': '',
                      'mentions_client': False, 'client_cited': False})
    result['source'] = 'offline'
    result['source_label'] = '离线分层（未采样，仅规则打标）'
    result['sample_count'] = len(items)
    result['items'] = [{'query': x['query'], 'stage': x['stage'],
                        'secondary_stage': x.get('secondary_stage')} for x in items]
    for x in items:
        result['query_stage'][x['query']] = x['stage']
        result['query_secondary_stage'][x['query']] = x.get('secondary_stage') or ''
    result['stages'] = aggregate(items)
    result['markdown'] = make_markdown(result)
    return result


def main():
    """命令行模式：读取 JSON 文件或 stdin，输出 JSON"""
    try:
        if len(sys.argv) > 1:
            with open(sys.argv[1], encoding='utf-8') as f:
                params = json.load(f)
        else:
            params = json.load(sys.stdin)
    except Exception as exc:
        print(json.dumps({'status': 'error', 'message': '参数解析失败：%s' % exc}, ensure_ascii=False))
        return 1
    out = run(params)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out.get('status') == 'ok' else 2


if __name__ == '__main__':
    sys.exit(main())
