#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 geo-monitoring / 监测平台导出的结果文件归一化为 diagnosis/responses.jsonl（只依赖标准库）。

用法：
  python3 scripts/normalize_monitoring.py --project ./acme-us-2026c1

读取 contract.inputs.monitoring_results[] 中的每个文件（.jsonl / .json / .csv / .tsv），
按其 mapping 文件把字段映射成 references/monitoring-input.md 定义的标准字段，
用问题文件补 topic_id，缺失的品牌提及/排位从 answer_text 推断（标记在 derived 字段）。
不采样、不调用任何 AI 接口。输出摘要 JSON；存在无法匹配到问题文件的记录时退出码 1（记录仍写出）。
"""

import argparse
import csv
import json
import os
import re
import sys
import urllib.parse

CANONICAL = [
    "response_id", "question_id", "question_text", "engine", "market", "run_index",
    "collected_at", "answer_text", "brand_mentioned", "brand_position", "sentiment",
]
ENGINE_ALIASES = {
    "chatgpt": "chatgpt", "openai": "chatgpt", "gpt": "chatgpt", "searchgpt": "chatgpt",
    "perplexity": "perplexity", "gemini": "gemini", "google ai overview": "google_aio",
    "google_aio": "google_aio", "ai overview": "google_aio", "aio": "google_aio",
    "ai mode": "google_ai_mode", "google_ai_mode": "google_ai_mode", "copilot": "copilot",
    "bing copilot": "copilot", "claude": "claude", "grok": "grok",
}
TRUE_VALUES = {"true", "yes", "y", "1", "mentioned", "visible"}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_rows(path):
    lower = path.lower()
    if lower.endswith(".jsonl"):
        with open(path, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    if lower.endswith(".json"):
        data = load_json(path)
        if isinstance(data, dict):
            for key in ("results", "responses", "data", "items", "records"):
                if isinstance(data.get(key), list):
                    return data[key]
            return [data]
        return data
    delimiter = "\t" if lower.endswith(".tsv") else ","
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def norm_text(text):
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def domain_of(url):
    host = (urllib.parse.urlsplit(url if "://" in url else "https://" + url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def parse_list(value, spec):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    fmt = (spec or {}).get("format", "json")
    if fmt == "json":
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except (TypeError, ValueError):
            pass
    delimiter = (spec or {}).get("delimiter", "|")
    return [part.strip() for part in str(value).split(delimiter) if part.strip()]


def to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def to_bool(value, true_values):
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return None
    return str(value).strip().lower() in true_values


def build_matchers(names):
    matchers = []
    for name in names:
        if name:
            matchers.append(re.compile(r"(?<![A-Za-z0-9])" + re.escape(name) + r"(?![A-Za-z0-9])", re.I))
    return matchers


def first_hit(text, matchers):
    hits = [m.search(text) for m in matchers]
    hits = [h.start() for h in hits if h]
    return min(hits) if hits else None


def derive_mentions(text, brand_matchers, competitor_matchers):
    """返回 (brand_mentioned, brand_position, brands_mentioned)，按首次出现顺序排位。"""
    found = []
    brand_at = first_hit(text, brand_matchers)
    if brand_at is not None:
        found.append(("__brand__", brand_at))
    for name, matchers in competitor_matchers:
        at = first_hit(text, matchers)
        if at is not None:
            found.append((name, at))
    found.sort(key=lambda item: item[1])
    brands, position = [], None
    for rank, (name, _) in enumerate(found, 1):
        if name == "__brand__":
            position = rank
        else:
            brands.append({"name": name, "position": rank})
    return brand_at is not None, position, brands


def normalize_citations(items):
    result = []
    for rank, item in enumerate(items, 1):
        if isinstance(item, str):
            item = {"url": item}
        url = item.get("url") or item.get("link") or item.get("href") or ""
        if not url:
            continue
        result.append({
            "url": url,
            "domain": item.get("domain") or domain_of(url),
            "title": item.get("title", ""),
            "position": to_int(item.get("position")) or rank,
        })
    return result


def normalize_cards(items):
    result = []
    for rank, item in enumerate(items, 1):
        if isinstance(item, str):
            item = {"title": item}
        result.append({
            "title": item.get("title", ""),
            "brand": item.get("brand", ""),
            "merchant": item.get("merchant") or item.get("seller") or "",
            "url": item.get("url", ""),
            "price": item.get("price", ""),
            "position": to_int(item.get("position")) or rank,
        })
    return result


def bank_index(bank):
    by_id, by_text = {}, {}
    for question in bank.get("questions") or []:
        qid = question.get("question_id")
        if qid:
            by_id[qid] = question
        for key in ("monitoring_prompt", "user_question"):
            if question.get(key):
                by_text[norm_text(question[key])] = question
    return by_id, by_text


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    parser.add_argument("--only", help="只处理 path 中包含该字符串的结果文件（用于区分基线期/观察期导出）")
    parser.add_argument("--out", help="输出路径（相对项目目录），默认 diagnosis/responses.jsonl")
    args = parser.parse_args()

    project = args.project
    contract = load_json(os.path.join(project, "contract.json"))
    bank = load_json(os.path.join(project, contract["inputs"]["question_bank"]["path"]))
    by_id, by_text = bank_index(bank)

    brand = contract.get("brand") or {}
    brand_matchers = build_matchers([brand.get("name")] + list(brand.get("aliases") or []))
    competitor_matchers = []
    for comp in (contract.get("competitors") or {}).get("list") or []:
        competitor_matchers.append((comp["name"], build_matchers([comp["name"]] + list(comp.get("aliases") or []))))
    default_market = (contract.get("markets") or [{}])[0].get("market", "")

    out_path = os.path.join(project, args.out or os.path.join("diagnosis", "responses.jsonl"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    summary = {"files": [], "records": 0, "unmatched_questions": [], "engines": {}, "derived_mentions": 0}
    unmatched = set()
    counter = 0

    with open(out_path, "w", encoding="utf-8") as out:
        for source in contract["inputs"].get("monitoring_results") or []:
            if args.only and args.only not in (source.get("path") or ""):
                continue
            mapping = load_json(os.path.join(project, source["mapping"])) if source.get("mapping") else {}
            fields = mapping.get("fields") or {}
            engine_values = {k.lower(): v for k, v in (mapping.get("engine_values") or {}).items()}
            true_values = {v.lower() for v in (mapping.get("brand_mentioned") or {}).get("true_values", [])} or TRUE_VALUES
            rows = read_rows(os.path.join(project, source["path"]))
            summary["files"].append({"path": source["path"], "rows": len(rows)})

            for row in rows:
                counter += 1
                rec = {name: row.get(fields.get(name, name)) for name in CANONICAL}

                raw_engine = str(rec["engine"] or (source.get("engines") or ["other"])[0]).strip()
                engine = engine_values.get(raw_engine.lower()) or ENGINE_ALIASES.get(raw_engine.lower(), raw_engine.lower() or "other")

                question = by_id.get(rec["question_id"]) if rec["question_id"] else None
                if question is None and rec["question_text"]:
                    question = by_text.get(norm_text(rec["question_text"]))
                if question is None:
                    unmatched.add(str(rec["question_id"] or rec["question_text"])[:80])

                def list_field(name):
                    spec = mapping.get(name) or {}
                    return parse_list(row.get(spec.get("field", name)), spec)

                answer = rec["answer_text"] or ""
                record = {
                    "response_id": rec["response_id"] or "r-%06d" % counter,
                    "question_id": (question or {}).get("question_id") or rec["question_id"],
                    "topic_id": (question or {}).get("topic_id"),
                    "engine": engine,
                    "market": rec["market"] or (question or {}).get("region") or default_market,
                    "run_index": to_int(rec["run_index"]),
                    "collected_at": rec["collected_at"],
                    "answer_text": answer,
                    "citations": normalize_citations(list_field("citations")),
                    "product_cards": normalize_cards(list_field("product_cards")),
                    "sentiment": (str(rec["sentiment"]).lower() if rec["sentiment"] not in (None, "") else None),
                    "accuracy_flags": list_field("accuracy_flags"),
                }

                mentioned = to_bool(row.get((mapping.get("brand_mentioned") or {}).get("field", fields.get("brand_mentioned", "brand_mentioned"))), true_values)
                position = to_int(rec["brand_position"])
                brands = [b if isinstance(b, dict) else {"name": b, "position": None} for b in list_field("brands_mentioned")]
                derived = []
                if mentioned is None or (not brands and competitor_matchers) or (mentioned and position is None):
                    d_mentioned, d_position, d_brands = derive_mentions(answer, brand_matchers, competitor_matchers)
                    if mentioned is None:
                        mentioned = d_mentioned
                        derived.append("brand_mentioned")
                    if position is None and mentioned:
                        position = d_position
                        derived.append("brand_position")
                    if not brands:
                        brands = d_brands
                        derived.append("brands_mentioned")
                record["brand_mentioned"] = bool(mentioned)
                record["brand_position"] = position if mentioned else None
                record["brands_mentioned"] = brands
                if derived:
                    record["derived"] = derived
                    summary["derived_mentions"] += 1

                summary["engines"][engine] = summary["engines"].get(engine, 0) + 1
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                summary["records"] += 1

    summary["unmatched_questions"] = sorted(unmatched)
    summary["output"] = out_path
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
