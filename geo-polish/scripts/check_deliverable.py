#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按渠道质检单张改动卡的交付物，生成 qa/<change_id>.json（只依赖标准库）。

用法：
  python3 scripts/check_deliverable.py --project ./acme-us-2026c1 --change C-002 [--write] [--today YYYY-MM-DD]

五个关卡（见 references/06-channel-gates.md）：
  fact            claims_used 全部存在且 verified + approved；正文中的金额/百分比能追溯到所用 claim
  evidence        证据账本中该卡覆盖为 ok；所用 claim 未过期
  extractability  页面/文章/PDP：core_answer 存在、长度合理、包含主体名称且出现在正文中；单一 H1；JSON-LD 可解析
  channel         绝对化词、占位符、内部标签、CTA；第三方简报的披露要求；对比页的竞品点名许可
  distribution    目标 URL、内链、KPI、对照组
--write：写 qa/<change_id>.json，并把改动卡 status 置为 qa_passed / qa_failed。
有 error 时退出码 1。人工审批（human_approval）始终为必需，脚本不会置为 approved。
"""

import argparse
import datetime
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_article import CTA_RE, INTERNAL_RE, PLACEHOLDER_RE, SUPERLATIVE_RE  # noqa: E402

PAGE_EXECUTORS = {"geo-pdp", "geo-landing", "geo-write"}
DISCLOSURE_ASSETS = {"creator_brief", "affiliate_kit", "listicle_outreach", "community_brief", "review_site_profile"}
COMPARISON_ASSETS = {"comparison_page", "alternatives_page"}
TEXT_ROLES = {"before_after", "page_html", "article_json", "brief", "fact_sheet", "ticket"}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def strip_html(text):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%$.\s]", " ", (text or "").lower())).strip()


def words(text):
    return len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", text or ""))


def read_deliverable_text(folder, manifest):
    """返回 (正文文本, 原始 HTML 列表, jsonld 文件列表)。before_after 只用于人工审阅，不计入正文。"""
    body_parts, raw_html, jsonld = [], [], []
    for item in manifest.get("files") or []:
        path = os.path.join(folder, item.get("path", ""))
        role = item.get("role")
        if not os.path.exists(path):
            continue
        if role == "jsonld":
            jsonld.append(path)
            continue
        if role not in TEXT_ROLES or role == "before_after":
            continue
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
        if role == "article_json":
            try:
                article = json.loads(raw)
                article = article[0] if isinstance(article, list) else article
                raw = (article.get("title") or "") + "\n" + (article.get("content") or "")
            except ValueError:
                pass
        if "<" in raw and ">" in raw:
            raw_html.append(raw)
            body_parts.append(strip_html(raw))
        else:
            body_parts.append(raw)
    return "\n".join(body_parts), raw_html, jsonld


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    parser.add_argument("--change", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--today")
    args = parser.parse_args()

    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    project = args.project
    contract = load_json(os.path.join(project, "contract.json"))
    changes_path = os.path.join(project, "strategy", "changes.json")
    changes_doc = load_json(changes_path)
    change = next((c for c in changes_doc.get("changes") or [] if c.get("change_id") == args.change), None)
    if change is None:
        print(json.dumps({"error": "change %s not found" % args.change}))
        return 1
    folder = os.path.join(project, "deliverables", args.change)
    manifest = load_json(os.path.join(folder, "manifest.json"))
    ledger_path = os.path.join(project, "evidence", "ledger.json")
    ledger = load_json(ledger_path) if os.path.exists(ledger_path) else {"claims": [], "change_coverage": []}
    claims = {c["claim_id"]: c for c in ledger.get("claims") or []}

    issues = []

    def add(gate, level, detail):
        issues.append({"gate": gate, "level": level, "detail": detail})

    asset = change.get("asset_type")
    executor = change.get("executor")
    text, raw_html, jsonld_files = read_deliverable_text(folder, manifest)
    if manifest.get("change_id") != args.change:
        add("distribution", "error", "manifest.change_id does not match")
    for item in manifest.get("files") or []:
        if not os.path.exists(os.path.join(folder, item.get("path", ""))):
            add("distribution", "error", "file listed in manifest is missing: %s" % item.get("path"))

    # fact
    used = manifest.get("claims_used") or []
    if asset != "tech_ticket":
        if not used:
            add("fact", "error", "claims_used is empty")
        for cid in used:
            claim = claims.get(cid)
            if not claim:
                add("fact", "error", "claim %s not in ledger" % cid)
            elif claim.get("status") != "verified" or not claim.get("approved_for_publication"):
                add("fact", "error", "claim %s is not verified/approved" % cid)
        traceable = norm(" ".join(
            " ".join([c.get("claim", ""), str(c.get("value", ""))] + [e.get("quote", "") for e in c.get("evidence") or []])
            for cid, c in claims.items() if cid in used))
        for match in set(re.findall(r"[$€£]\s?\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s?%", text)):
            token = norm(match).replace(" ", "")
            if token not in traceable.replace(" ", ""):
                add("fact", "error", "amount/percentage %r not found in any claim used" % match.strip())
        for match in set(re.findall(r"\b\d{2,}(?:[.,]\d+)?\b", text)):
            if match not in traceable and not re.fullmatch(r"20\d\d", match):
                add("fact", "warn", "number %s not found in claims used; confirm it is not a hard fact" % match)

    # evidence
    if asset != "tech_ticket":
        coverage = next((c for c in ledger.get("change_coverage") or [] if c.get("change_id") == args.change), None)
        if not coverage:
            add("evidence", "error", "no change_coverage entry in ledger")
        elif coverage.get("status") != "ok":
            add("evidence", "error", "ledger coverage is %s (missing: %s)" % (coverage.get("status"), coverage.get("missing")))
        for cid in used:
            until = (claims.get(cid) or {}).get("valid_until")
            if until:
                try:
                    if datetime.date.fromisoformat(until[:10]) < today:
                        add("evidence", "error", "claim %s expired on %s" % (cid, until))
                except ValueError:
                    add("evidence", "warn", "claim %s has unparsable valid_until" % cid)

    # extractability
    if executor in PAGE_EXECUTORS and asset not in ("product_feed",):
        core = manifest.get("core_answer") or ""
        if not core:
            add("extractability", "error", "core_answer missing")
        else:
            n = words(core)
            if not 20 <= n <= 120:
                add("extractability", "warn", "core_answer has %d words (expected 20-120)" % n)
            names = [contract["brand"]["name"]] + list(contract["brand"].get("aliases") or [])
            for line in contract.get("business_lines") or []:
                names += [o.get("name") for o in line.get("objects") or [] if o.get("object_id") in (change.get("target") or {}).get("object_ids", [])]
            if not any(name and name.lower() in core.lower() for name in names):
                add("extractability", "warn", "core_answer does not name the brand or target object")
            if raw_html and norm(core)[:80] not in norm(text):
                add("extractability", "error", "core_answer text does not appear in the deliverable body")
        for raw in raw_html:
            h1 = len(re.findall(r"<h1[\s>]", raw, re.I))
            if asset in ("pdp_rewrite",) and h1 == 0:
                continue
            if h1 != 1:
                add("extractability", "warn", "%d <h1> tags in page body" % h1)
    for path in jsonld_files:
        try:
            load_json(path)
        except ValueError as exc:
            add("extractability", "error", "%s is not valid JSON-LD: %s" % (os.path.basename(path), exc))

    # channel
    for pattern, code in ((PLACEHOLDER_RE, "placeholder"), (INTERNAL_RE, "internal label")):
        match = pattern.search(text)
        if match:
            add("channel", "error", "%s leaked: %s" % (code, match.group(0)))
    if executor in PAGE_EXECUTORS:
        hits = sorted({m.group(0).lower() for m in SUPERLATIVE_RE.finditer(text)})
        if hits:
            add("channel", "warn", "absolute/marketing terms: %s (allowed only inside verbatim question-bank questions)" % ", ".join(hits))
        match = CTA_RE.search(text)
        if match and executor == "geo-write":
            add("channel", "warn", "hard CTA in article: %s" % match.group(0))
    if asset in DISCLOSURE_ASSETS and not re.search(r"disclos|披露", text, re.I):
        add("channel", "error", "%s must state disclosure requirements" % asset)
    if executor == "geo-offsite" and not manifest.get("notes"):
        add("channel", "error", "geo-offsite manifest.notes must record the disclosure/platform-rule self-check")
    constraints = contract.get("constraints") or {}
    if asset in COMPARISON_ASSETS:
        named = [c["name"] for c in (contract.get("competitors") or {}).get("list") or [] if c["name"].lower() in text.lower()]
        if named and not constraints.get("competitor_naming_allowed"):
            add("channel", "error", "competitors named (%s) but competitor_naming_allowed is false" % ", ".join(named))
        if named and not any((claims.get(c) or {}).get("claim_type") == "competitor_fact" for c in used):
            add("fact", "error", "competitors named but no competitor_fact claims used")
    for phrase in constraints.get("forbidden_claims") or []:
        if phrase and phrase.lower() in text.lower():
            add("channel", "error", "forbidden claim appears: %s" % phrase)

    # distribution
    if executor in PAGE_EXECUTORS and not (manifest.get("target_url") or (change.get("target") or {}).get("url")):
        add("distribution", "error", "no target URL (existing page or proposed URL)")
    if executor in ("geo-landing", "geo-write") and not manifest.get("internal_links"):
        add("distribution", "warn", "no internal_links planned")
    if not (change.get("kpis") or {}).get("business"):
        add("distribution", "error", "change has no business KPI")
    if not change.get("control_topic_ids"):
        add("distribution", "warn", "no control topics; measurement will be observational")

    gates = {}
    for gate in ("fact", "evidence", "extractability", "channel", "distribution"):
        levels = [i["level"] for i in issues if i["gate"] == gate]
        gates[gate] = "fail" if "error" in levels else ("warn" if "warn" in levels else "pass")
    needs_legal = bool(constraints.get("legal_review_required")) or contract.get("compliance_overlay") not in (None, "none") or asset in COMPARISON_ASSETS
    report = {
        "change_id": args.change,
        "checked_at": today.isoformat(),
        "gates": gates,
        "issues": issues,
        "human_approval": {"required": True, "legal_review_required": needs_legal, "approved_by": None, "approved_at": None},
    }
    failed = any(v == "fail" for v in gates.values())
    if args.write:
        qa_dir = os.path.join(project, "qa")
        os.makedirs(qa_dir, exist_ok=True)
        with open(os.path.join(qa_dir, args.change + ".json"), "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        if change.get("status") not in ("approved", "launched", "measured", "dropped"):
            change["status"] = "qa_failed" if failed else "qa_passed"
            with open(changes_path, "w", encoding="utf-8") as handle:
                json.dump(changes_doc, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
