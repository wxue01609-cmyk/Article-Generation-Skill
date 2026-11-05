#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按问题族（topic）统计答案指标，并给出建议失败层（只依赖标准库）。

用法：
  python3 scripts/compute_topic_metrics.py --project ./acme-us-2026c1 [--low 0.2] [--high 0.5] [--min-responses 6]

输入：contract.json、问题文件、diagnosis/responses.jsonl、可选 diagnosis/site_audit.json。
输出：diagnosis/topic_metrics.json（字段见 geo-contract/references/artifact-contracts.md 第三节）。
建议失败层只是启发式规则（见 references/failure-layers.md），最终判定由模型在 diagnosis.json 中给出并说明理由。
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

MARKETPLACES = ("amazon.", "ebay.", "walmart.", "etsy.", "aliexpress.", "temu.", "target.com", "bestbuy.com", "alibaba.com", "made-in-china.com")
COMMUNITY = ("reddit.com", "quora.com", "youtube.com", "youtu.be", "facebook.com", "x.com", "twitter.com", "linkedin.com", "tiktok.com", "instagram.com", "pinterest.")
REFERENCE = ("wikipedia.org", "wikidata.org", "britannica.com")
REVIEW = ("trustpilot.com", "g2.com", "capterra.com", "getapp.com", "softwareadvice.com", "clutch.co", "yelp.com",
          "tripadvisor.", "rtings.com", "wirecutter", "cnet.com", "pcmag.com", "techradar.com", "tomsguide.com",
          "theverge.com", "zdnet.com", "consumerreports.org", "forbes.com", "businessinsider.com")
DTC_SCENARIOS = {"dtc_ecommerce", "marketplace_seller"}
PRIORITY_ORDER = {"P1": 1, "P2": 2, "P3": 3}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def strip_www(domain):
    domain = (domain or "").lower()
    return domain[4:] if domain.startswith("www.") else domain


def domain_matches(domain, patterns):
    """'amazon.' 匹配任意后缀（amazon.com / amazon.co.uk）；含点的模式按域名后缀匹配；不含点的按子串匹配。"""
    for pattern in patterns:
        if pattern.endswith("."):
            if domain.startswith(pattern) or ("." + pattern) in domain:
                return True
        elif "." in pattern:
            if domain == pattern or domain.endswith("." + pattern):
                return True
        elif pattern in domain:
            return True
    return False


def classify_domain(domain, owned, competitor_domains, overrides):
    if domain in overrides:
        return overrides[domain]
    if any(domain == d or domain.endswith("." + d) for d in owned):
        return "owned"
    if any(domain == d or domain.endswith("." + d) for d in competitor_domains):
        return "competitor"
    for patterns, label in ((MARKETPLACES, "marketplace"), (COMMUNITY, "community"), (REFERENCE, "reference"), (REVIEW, "media_review")):
        if domain_matches(domain, patterns):
            return label
    return "other"


def rate(numerator, denominator):
    return round(numerator / denominator, 3) if denominator else None


def is_validation_type(prompt_type):
    text = (prompt_type or "").lower()
    return "verif" in text or "brand" in text or "验证" in text


def suggest_layer(m, scenario, blocked_urls, thresholds, min_responses):
    low, high = thresholds
    reasons = []
    if m["response_count"] < min_responses:
        return "insufficient_data", ["only %d responses (< %d)" % (m["response_count"], min_responses)]
    if blocked_urls:
        return "crawl_blocked", ["target pages blocked or unreadable: " + ", ".join(blocked_urls[:3])]
    cards = m.get("product_cards") or {}
    if scenario in DTC_SCENARIOS and (cards.get("card_rate") or 0) >= 0.3 and (cards.get("brand_card_rate") or 0) == 0:
        return "not_in_product_pool", ["product cards in %d%% of answers, brand in 0%%" % round(cards["card_rate"] * 100)]
    mentions = m["mentioned_count"]
    negative = m["sentiment"]["negative"]
    if m["response_count"] and m["accuracy_flag_count"] / m["response_count"] >= 0.1:
        return "mentioned_inaccurate", ["accuracy flags on %d responses" % m["accuracy_flag_count"]]
    if mentions and negative / mentions >= 0.2:
        return "mentioned_inaccurate", ["negative sentiment in %d of %d brand mentions" % (negative, mentions)]
    mention = m["unbranded_mention_rate"] if m["unbranded_mention_rate"] is not None else (m["mention_rate"] or 0)
    if mention >= high:
        return "strong", ["unbranded mention rate %.2f >= %.2f; check AI-referral conversion before treating as strong" % (mention, high)]
    owned_cited = m["owned_cited_rate"] or 0
    if owned_cited >= 0.2 and mention < low:
        return "cited_not_mentioned", ["owned pages cited in %d%% of answers but brand mentioned in %d%%" % (round(owned_cited * 100), round(mention * 100))]
    by_type = m["mention_rate_by_type"]
    discovery = by_type.get("Discovery")
    validation = [v for k, v in by_type.items() if is_validation_type(k) and v is not None]
    if discovery is not None and discovery < low and validation and max(validation) >= high:
        return "known_not_recommended", ["discovery mention %.2f vs validation mention %.2f" % (discovery, max(validation))]
    if mention < low and owned_cited < 0.05:
        return "not_selected", ["mention rate %.2f and owned citation rate %.2f" % (mention, owned_cited)]
    top = (m["top_competitors"] or [{}])[0].get("mention_rate") or 0
    if top > mention * 1.5:
        reasons.append("brand %.2f vs top competitor %.2f" % (mention, top))
        return "known_not_recommended", reasons
    return "strong", ["mention rate %.2f with no dominant competitor" % mention]


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    parser.add_argument("--low", type=float, default=0.2)
    parser.add_argument("--high", type=float, default=0.5)
    parser.add_argument("--min-responses", type=int, default=6)
    parser.add_argument("--responses", help="答案记录路径（相对项目目录），默认 diagnosis/responses.jsonl")
    parser.add_argument("--out", help="输出路径（相对项目目录），默认 diagnosis/topic_metrics.json")
    args = parser.parse_args()

    project = args.project
    contract = load_json(os.path.join(project, "contract.json"))
    bank = load_json(os.path.join(project, contract["inputs"]["question_bank"]["path"]))

    brand = contract.get("brand") or {}
    owned = [strip_www(d) for d in [brand.get("official_domain")] + list(brand.get("other_owned_domains") or []) if d]
    competitors = (contract.get("competitors") or {}).get("list") or []
    competitor_domains = [strip_www(c["domain"]) for c in competitors if c.get("domain")]
    overrides = {k.lower(): v for k, v in (contract.get("domain_types") or {}).items()}
    brand_names = {n.lower() for n in [brand.get("name")] + list(brand.get("aliases") or []) if n}

    lines = {line["line_id"]: line for line in contract.get("business_lines") or []}
    topic_map = {item["topic_id"]: item for item in contract.get("topic_object_map") or []}
    default_line = next(iter(lines.values()), {})

    questions = {q.get("question_id"): q for q in bank.get("questions") or []}
    topic_names = {t.get("topic_id"): t.get("topic") for t in (bank.get("config") or {}).get("topics") or [] if isinstance(t, dict)}
    prompts_per_topic = defaultdict(set)
    for q in questions.values():
        if q.get("topic_id"):
            prompts_per_topic[q["topic_id"]].add(q.get("question_id"))

    audit = {}
    audit_path = os.path.join(project, "diagnosis", "site_audit.json")
    if os.path.exists(audit_path):
        for page in load_json(audit_path).get("pages") or []:
            audit[page.get("url")] = page

    responses = defaultdict(list)
    dates = []
    with open(os.path.join(project, args.responses or os.path.join("diagnosis", "responses.jsonl")), "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rec = json.loads(line)
                responses[rec.get("topic_id") or "__unmatched__"].append(rec)
                if rec.get("collected_at"):
                    dates.append(str(rec["collected_at"])[:10])

    topics_out = []
    for topic_id in sorted(set(prompts_per_topic) | set(k for k in responses if k != "__unmatched__")):
        recs = responses.get(topic_id, [])
        mapping = topic_map.get(topic_id, {})
        line = lines.get(mapping.get("line_id"), default_line)
        scenario = line.get("scenario")
        object_ids = mapping.get("object_ids") or []
        object_urls = [o.get("url") for o in line.get("objects") or [] if o.get("object_id") in object_ids and o.get("url")]

        n = len(recs)
        mentioned = [r for r in recs if r.get("brand_mentioned")]
        positions = [r["brand_position"] for r in mentioned if r.get("brand_position")]

        by_type_total, by_type_hit = Counter(), Counter()
        for r in recs:
            ptype = (questions.get(r.get("question_id")) or {}).get("prompt_type") or "Unknown"
            by_type_total[ptype] += 1
            by_type_hit[ptype] += 1 if r.get("brand_mentioned") else 0

        comp_counter = Counter()
        brand_mentions_total = len(mentioned)
        for r in recs:
            for b in r.get("brands_mentioned") or []:
                name = b.get("name") if isinstance(b, dict) else b
                if name and name.lower() not in brand_names:
                    comp_counter[name] += 1
        all_mentions = brand_mentions_total + sum(comp_counter.values())

        domain_counter, type_counter = Counter(), Counter()
        owned_cited = 0
        for r in recs:
            cited_owned = False
            for c in r.get("citations") or []:
                domain = strip_www(c.get("domain"))
                kind = classify_domain(domain, owned, competitor_domains, overrides)
                domain_counter[(domain, kind)] += 1
                type_counter[kind] += 1
                cited_owned = cited_owned or kind == "owned"
            owned_cited += 1 if cited_owned else 0
        total_citations = sum(type_counter.values())

        card_answers = [r for r in recs if r.get("product_cards")]
        brand_card_answers, brand_card_positions = 0, []
        for r in card_answers:
            hits = [c for c in r["product_cards"] if (c.get("brand") or "").lower() in brand_names
                    or any(name in (c.get("title") or "").lower() for name in brand_names)]
            if hits:
                brand_card_answers += 1
                brand_card_positions.append(min(c.get("position") or 99 for c in hits))

        sentiment = Counter((r.get("sentiment") or "unknown") for r in mentioned)
        by_engine = defaultdict(lambda: [0, 0])
        for r in recs:
            by_engine[r.get("engine") or "other"][0] += 1
            by_engine[r.get("engine") or "other"][1] += 1 if r.get("brand_mentioned") else 0

        priorities = [(questions.get(q) or {}).get("business_priority") for q in prompts_per_topic.get(topic_id, [])]
        priorities = sorted({p for p in priorities if p}, key=lambda p: PRIORITY_ORDER.get(p, 9))
        stages = sorted({(questions.get(q) or {}).get("journey_stage") for q in prompts_per_topic.get(topic_id, [])} - {None})

        metrics = {
            "topic_id": topic_id,
            "topic": topic_names.get(topic_id, ""),
            "line_id": line.get("line_id"),
            "scenario": scenario,
            "object_ids": object_ids,
            "prompt_count": len(prompts_per_topic.get(topic_id, [])),
            "response_count": n,
            "engines": sorted(by_engine),
            "mentioned_count": len(mentioned),
            "mention_rate": rate(len(mentioned), n),
            "unbranded_mention_rate": rate(sum(by_type_hit[k] for k in by_type_total if not is_validation_type(k)),
                                           sum(v for k, v in by_type_total.items() if not is_validation_type(k))),
            "mention_rate_by_type": {k: rate(by_type_hit[k], v) for k, v in by_type_total.items()},
            "avg_position": round(sum(positions) / len(positions), 2) if positions else None,
            "share_of_voice": rate(brand_mentions_total, all_mentions),
            "top_competitors": [{"name": name, "mention_rate": rate(count, n)} for name, count in comp_counter.most_common(5)],
            "owned_cited_rate": rate(owned_cited, n),
            "citations": {
                "total": total_citations,
                "owned_share": rate(type_counter["owned"], total_citations),
                "top_domains": [{"domain": d, "count": c, "type": k} for (d, k), c in domain_counter.most_common(10)],
            },
            "source_mix": {k: rate(type_counter[k], total_citations) for k in
                           ("owned", "competitor", "marketplace", "media_review", "community", "reference", "other")},
            "product_cards": {
                "card_rate": rate(len(card_answers), n),
                "brand_card_rate": rate(brand_card_answers, len(card_answers)) if card_answers else None,
                "avg_brand_card_position": round(sum(brand_card_positions) / len(brand_card_positions), 2) if brand_card_positions else None,
            },
            "sentiment": {k: sentiment.get(k, 0) for k in ("positive", "neutral", "negative", "unknown")},
            "accuracy_flag_count": sum(1 for r in recs if r.get("accuracy_flags")),
            "by_engine": {e: {"response_count": v[0], "mention_rate": rate(v[1], v[0])} for e, v in by_engine.items()},
            "business_priority": priorities[0] if priorities else None,
            "journey_stages": stages,
        }
        blocked = [u for u in object_urls if (audit.get(u) or {}).get("blocked")]
        layer, reasons = suggest_layer(metrics, scenario, blocked, (args.low, args.high), args.min_responses)
        metrics["suggested_layer"] = layer
        metrics["suggested_layer_reasons"] = reasons
        topics_out.append(metrics)

    result = {
        "schema_version": "geo-topic-metrics/v1",
        "project_id": contract.get("project_id"),
        "window": {"from": min(dates) if dates else None, "to": max(dates) if dates else None},
        "thresholds": {"low": args.low, "high": args.high, "min_responses": args.min_responses},
        "unmatched_response_count": len(responses.get("__unmatched__", [])),
        "topics": topics_out,
    }
    out_path = os.path.join(project, args.out or os.path.join("diagnosis", "topic_metrics.json"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    layers = Counter(t["suggested_layer"] for t in topics_out)
    print(json.dumps({"output": out_path, "topics": len(topics_out), "suggested_layers": layers}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
