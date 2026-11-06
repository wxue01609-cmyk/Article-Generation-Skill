#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验模型产出的 diagnosis/diagnosis.json（只依赖标准库）。

用法：
  python3 scripts/check_diagnosis.py --project ./acme-us-2026c1

检查：字段齐全；failure_layer 取值合法；topic_metrics 中每个 topic 都有判定；
判定与脚本建议层不同时必须写 layer_override_reason；问题文件未锁定或每题采样不足 3 次时
evidence_level 必须是 hypothesis。有 error 时退出码 1。
"""

import argparse
import json
import os
import sys

LAYERS = {"crawl_blocked", "not_in_product_pool", "not_selected", "cited_not_mentioned", "mentioned_inaccurate",
          "known_not_recommended", "recommended_not_converting", "strong", "insufficient_data"}
LOCKED = {"locked", "formal_baseline", "active"}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()

    project = args.project

    def load_required(path, label):
        """文件缺失时输出友好 JSON 错误并退出 1，不抛 traceback。"""
        if not os.path.exists(path):
            print(json.dumps({"status": "error", "message": "%s 缺失：%s" % (label, path)},
                             ensure_ascii=False, indent=2))
            sys.exit(1)
        try:
            return load_json(path)
        except Exception as exc:
            print(json.dumps({"status": "error", "message": "%s 解析失败：%s" % (label, exc)},
                             ensure_ascii=False, indent=2))
            sys.exit(1)

    contract = load_required(os.path.join(project, "contract.json"), "contract.json")
    bank_path = os.path.join(project, contract["inputs"]["question_bank"]["path"])
    bank = load_required(bank_path, "question_bank")
    tm_path = os.path.join(project, "diagnosis", "topic_metrics.json")
    metrics = {t["topic_id"]: t for t in load_required(tm_path, "topic_metrics.json")["topics"]}
    diagnosis = load_required(os.path.join(project, "diagnosis", "diagnosis.json"), "diagnosis.json")

    issues = []

    def add(level, detail):
        issues.append({"level": level, "detail": detail})

    status = diagnosis.get("data_status") or {}
    runs = min([m.get("runs_per_prompt") or 0 for m in contract["inputs"].get("monitoring_results") or []] or [0])
    bank_locked = (bank.get("config") or {}).get("lifecycle_status") in LOCKED
    if status.get("evidence_level") not in ("hypothesis", "baseline"):
        add("error", "data_status.evidence_level must be hypothesis or baseline")
    elif status.get("evidence_level") == "baseline" and (not bank_locked or runs < 3):
        add("error", "evidence_level=baseline requires a locked question bank and >=3 runs per prompt (bank locked=%s, runs=%s)" % (bank_locked, runs))

    seen = set()
    for topic in diagnosis.get("topics") or []:
        tid = topic.get("topic_id")
        seen.add(tid)
        if tid not in metrics:
            add("error", "%s not in topic_metrics.json" % tid)
            continue
        layer = topic.get("failure_layer")
        if layer not in LAYERS:
            add("error", "%s: invalid failure_layer %r" % (tid, layer))
        for field in ("line_id", "scenario", "business_value", "layer_confidence", "evidence"):
            if not topic.get(field):
                add("error", "%s: missing %s" % (tid, field))
        score = (topic.get("business_value") or {}).get("score")
        if not isinstance(score, (int, float)) or not 0 <= score <= 10:
            add("error", "%s: business_value.score must be 0-10" % tid)
        if layer != metrics[tid].get("suggested_layer") and not topic.get("layer_override_reason"):
            add("error", "%s: layer %s differs from suggested %s without layer_override_reason" % (tid, layer, metrics[tid].get("suggested_layer")))
        if layer == "recommended_not_converting" and not contract["inputs"].get("analytics"):
            add("error", "%s: recommended_not_converting needs analytics data in contract.inputs.analytics" % tid)
    for tid in metrics:
        if tid not in seen:
            add("error", "%s missing from diagnosis.topics" % tid)

    comp = diagnosis.get("competitors") or {}
    if comp.get("status") not in ("frozen", "verified", "missing"):
        add("warn", "competitors.status should be frozen / verified / missing")

    print(json.dumps({"topics": len(seen), "issues": issues}, ensure_ascii=False, indent=2))
    return 1 if any(i["level"] == "error" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
