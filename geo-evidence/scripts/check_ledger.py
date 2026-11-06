#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验证据账本并计算每张改动卡的证据覆盖（只依赖标准库）。

用法：
  内容建设通道：python3 scripts/check_ledger.py --project ./acme-us-2026c1 --channel assets [--write]
  SKU 改造通道：python3 scripts/check_ledger.py --project ./acme-us-2026c1 --channel changes [--write]（默认）

检查：claim 字段与取值合法；verified 必须有原文摘录与来源；price 必须有 valid_until 且不超过 30 天；
禁用 claim（contract.constraints.forbidden_claims）不得 approved。
--channel assets：按 evidence/ledger.json 的 asset_coverage 核算（key=asset_id），--write 时回写
  evidence/evidence_map.json（asset_id → 可用 claim 列表），不需要 strategy/changes.json。
--channel changes（默认）：按选中卡的 change_coverage 核算，--write 时回写 changes.json：
  scores.evidence = covered/required，有缺口的卡 status 置为 evidence_blocked（已在 in_production 之后的状态不动）。
有 error 时退出码 1。
"""

import argparse
import datetime
import json
import os
import sys

CLAIM_TYPES = {"product_spec", "company_fact", "certification", "price", "policy", "performance", "customer_proof",
               "review_stat", "competitor_fact", "market_stat", "expert_opinion"}
SOURCE_TYPES = {"first_party_doc", "official_site", "kb", "client_input", "third_party", "review_platform", "regulator"}
STATUSES = {"verified", "needs_client_confirmation", "blocked"}
STRONG_SOURCES = {"first_party_doc", "official_site", "kb", "client_input", "review_platform", "regulator"}
LATE_STATUSES = {"in_production", "qa_failed", "qa_passed", "approved", "launched", "measured", "dropped"}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_date(value):
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    parser.add_argument("--channel", choices=("assets", "changes"), default="changes",
                        help="assets=内容建设矩阵资产；changes=SKU 改造改动卡（默认）")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD) for expiry checks")
    args = parser.parse_args()

    today = parse_date(args.today) if args.today else datetime.date.today()
    project = args.project
    contract_path = os.path.join(project, "contract.json")
    contract = load_json(contract_path) if os.path.exists(contract_path) else {"constraints": {}, "compliance_overlay": "none"}
    changes_path = os.path.join(project, "strategy", "changes.json")
    # 内容建设通道（assets）不依赖 changes.json
    changes_doc = load_json(changes_path) if args.channel == "changes" and os.path.exists(changes_path) else {"changes": []}
    ledger_path = os.path.join(project, "evidence", "ledger.json")
    ledger = load_json(ledger_path)

    forbidden = [f.lower() for f in (contract.get("constraints") or {}).get("forbidden_claims") or []]
    overlay = contract.get("compliance_overlay", "none")
    issues = []

    def add(level, where, detail):
        issues.append({"level": level, "where": where, "detail": detail})

    claims = {}
    for claim in ledger.get("claims") or []:
        cid = claim.get("claim_id")
        if not cid or cid in claims:
            add("error", cid, "missing or duplicate claim_id")
            continue
        claims[cid] = claim
        if claim.get("claim_type") not in CLAIM_TYPES:
            add("error", cid, "invalid claim_type %r" % claim.get("claim_type"))
        status = claim.get("status")
        if status not in STATUSES:
            add("error", cid, "invalid status %r" % status)
        evidence = claim.get("evidence") or []
        for item in evidence:
            if item.get("source_type") not in SOURCE_TYPES:
                add("error", cid, "invalid source_type %r" % item.get("source_type"))
        if status == "verified":
            if not evidence or not any(e.get("quote") and e.get("source_ref") for e in evidence):
                add("error", cid, "verified claim needs at least one evidence item with quote and source_ref")
            if claim.get("claim_type") in ("product_spec", "certification", "policy", "price") and not any(e.get("source_type") in STRONG_SOURCES for e in evidence):
                add("error", cid, "%s must rest on a first-party/official/regulator source" % claim.get("claim_type"))
            if claim.get("claim_type") in ("competitor_fact", "market_stat", "review_stat", "price") and not any(e.get("date") for e in evidence):
                add("error", cid, "%s evidence must carry a date" % claim.get("claim_type"))
        if claim.get("claim_type") == "price" and status == "verified":
            until = parse_date(claim.get("valid_until") or "")
            if not until:
                add("error", cid, "price claim needs valid_until")
            elif until < today:
                add("error", cid, "price claim expired on %s" % until)
            elif (until - today).days > 30:
                add("warn", cid, "price valid_until more than 30 days away")
        text = (claim.get("claim") or "").lower()
        hit = [f for f in forbidden if f and f in text]
        if hit and claim.get("approved_for_publication"):
            add("error", cid, "contains forbidden claim %s but approved_for_publication=true" % hit)
        if claim.get("approved_for_publication") and status != "verified":
            add("error", cid, "approved_for_publication requires status=verified")
        if overlay not in (None, "none") and claim.get("claim_type") in ("performance", "customer_proof") and claim.get("approved_for_publication") and not claim.get("human_reviewed_by"):
            add("error", cid, "compliance overlay %s: performance/customer_proof claims need human_reviewed_by" % overlay)

    if args.channel == 'assets':
        # 内容建设通道：按资产（asset_id）核算，不读取 strategy/changes.json
        coverage_by_asset = {item.get("asset_id"): item for item in ledger.get("asset_coverage") or []}
        new_coverage = []
        for asset_id, entry in coverage_by_asset.items():
            required = entry.get("required") or []
            covered = [c for c in entry.get("covered") or [] if c in claims]
            unknown = [c for c in entry.get("covered") or [] if c not in claims]
            if unknown:
                add("error", asset_id, "covered claim ids not in ledger: %s" % unknown)
            unusable = [c for c in covered if not (claims[c].get("status") == "verified" and claims[c].get("approved_for_publication"))]
            if unusable:
                add("error", asset_id, "covered claims not verified/approved: %s" % unusable)
            usable = [c for c in covered if c not in unusable]
            missing = entry.get("missing") or []
            if len(required) and len(usable) < len(required) and not missing:
                add("error", asset_id, "%d required claims but only %d usable and no missing list" % (len(required), len(usable)))
            status = "ok" if not missing and not unusable and len(usable) >= len(required) else "blocked"
            evidence_score = round(min(1.0, len(usable) / len(required)), 2) if required else 1.0
            for claim_id in usable:
                claims[claim_id].setdefault("used_by", [])
                if asset_id not in claims[claim_id]["used_by"]:
                    claims[claim_id]["used_by"].append(asset_id)
            new_coverage.append({"asset_id": asset_id, "required": required, "covered": usable,
                                 "missing": missing + unusable, "status": status, "evidence_score": evidence_score})
        if args.write:
            ledger["asset_coverage"] = new_coverage
            with open(ledger_path, "w", encoding="utf-8") as handle:
                json.dump(ledger, handle, ensure_ascii=False, indent=2)
            evidence_map = {c["asset_id"]: c["covered"] for c in new_coverage}
            map_path = os.path.join(project, "evidence", "evidence_map.json")
            with open(map_path, "w", encoding="utf-8") as handle:
                json.dump(evidence_map, handle, ensure_ascii=False, indent=2)
    else:
        selected = [c for c in changes_doc.get("changes") or [] if c.get("selected") and c.get("asset_type") != "tech_ticket"]
        coverage_by_change = {item.get("change_id"): item for item in ledger.get("change_coverage") or []}
        new_coverage = []
        for change in selected:
            cid = change["change_id"]
            entry = coverage_by_change.get(cid)
            if entry is None:
                add("error", cid, "selected change has no change_coverage entry")
                entry = {"change_id": cid, "required": change.get("claims_required") or [], "covered": [], "missing": change.get("claims_required") or []}
            required = entry.get("required") or change.get("claims_required") or []
            covered = [c for c in entry.get("covered") or [] if c in claims]
            unknown = [c for c in entry.get("covered") or [] if c not in claims]
            if unknown:
                add("error", cid, "covered claim ids not in ledger: %s" % unknown)
            unusable = [c for c in covered if not (claims[c].get("status") == "verified" and claims[c].get("approved_for_publication"))]
            if unusable:
                add("error", cid, "covered claims not verified/approved: %s" % unusable)
            usable = [c for c in covered if c not in unusable]
            missing = entry.get("missing") or []
            if len(required) and len(usable) < len(required) and not missing:
                add("error", cid, "%d required claims but only %d usable and no missing list" % (len(required), len(usable)))
            status = "ok" if not missing and not unusable and len(usable) >= len(required) else "blocked"
            evidence_score = round(min(1.0, len(usable) / len(required)), 2) if required else 1.0
            for claim_id in usable:
                claims[claim_id].setdefault("used_by", [])
                if cid not in claims[claim_id]["used_by"]:
                    claims[claim_id]["used_by"].append(cid)
            new_coverage.append({"change_id": cid, "required": required, "covered": usable, "missing": missing + unusable,
                                 "status": status, "evidence_score": evidence_score})

        if args.write:
            ledger["change_coverage"] = new_coverage
            with open(ledger_path, "w", encoding="utf-8") as handle:
                json.dump(ledger, handle, ensure_ascii=False, indent=2)
            by_id = {c["change_id"]: c for c in new_coverage}
            for change in changes_doc.get("changes") or []:
                entry = by_id.get(change.get("change_id"))
                if not entry:
                    continue
                change.setdefault("scores", {})["evidence"] = entry["evidence_score"]
                if change.get("status") not in LATE_STATUSES:
                    change["status"] = "planned" if entry["status"] == "ok" else "evidence_blocked"
            with open(changes_path, "w", encoding="utf-8") as handle:
                json.dump(changes_doc, handle, ensure_ascii=False, indent=2)

    summary = {
        "claims": len(claims),
        "by_status": {s: sum(1 for c in claims.values() if c.get("status") == s) for s in sorted(STATUSES)},
        "coverage": new_coverage,
        "issues": issues,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if any(i["level"] == "error" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
