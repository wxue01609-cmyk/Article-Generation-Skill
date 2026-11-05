#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验商品 feed 文件（只依赖标准库）。

用法：
  python3 scripts/check_feed.py --feed feed_openai.csv --spec openai
  python3 scripts/check_feed.py --feed feed_google.tsv --spec google

openai：按 OpenAI Commerce Product Feed Spec（2026-11-02 查阅）检查 9 个必填字段、price 格式、
        availability 枚举、title/description 长度、GTIN 校验位、sale_price、资格标记别名冲突。
google：按 Merchant Center 常用字段做基础检查（以 Google 官方规范为准）。
输出逐行问题 JSON；有 error 时退出码 1。
"""

import argparse
import csv
import json
import re
import sys

SPECS = {
    "openai": {
        "id": "item_id",
        "required": ["item_id", "title", "description", "url", "brand", "seller_name", "image_url", "price", "availability"],
        "availability": {"in_stock", "out_of_stock", "pre_order", "backorder", "unknown"},
        "url": "url",
        "image": "image_url",
        "group": "group_id",
    },
    "google": {
        "id": "id",
        "required": ["id", "title", "description", "link", "image_link", "availability", "price"],
        "availability": {"in_stock", "out_of_stock", "preorder", "backorder"},
        "url": "link",
        "image": "image_link",
        "group": "item_group_id",
    },
}
PRICE_RE = re.compile(r"^\d+(?:\.\d{1,2})? [A-Z]{3}$")
PLACEHOLDER_BRANDS = {"n/a", "na", "none", "unknown", "generic", "brand", "test", "-"}


def read_feed(path):
    delimiter = "\t" if path.lower().endswith((".tsv", ".txt")) else ","
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def gtin_valid(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) not in (8, 12, 13, 14) or digits != (value or "").strip():
        return False
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def parse_price(value):
    if not value or not PRICE_RE.match(value.strip()):
        return None
    amount, currency = value.strip().split(" ")
    return float(amount), currency


def check_row(row, spec, name):
    issues = []

    def add(level, field, detail):
        issues.append({"level": level, "field": field, "detail": detail})

    for field in spec["required"]:
        if not (row.get(field) or "").strip():
            add("error", field, "required field empty")

    title = row.get("title") or ""
    if len(title) > 150:
        add("error" if name == "google" else "warn", "title", "%d chars (> 150)" % len(title))
    if len(title) > 15 and title.isupper():
        add("warn", "title", "all caps")
    description = row.get("description") or ""
    if len(description) > 5000:
        add("error" if name == "google" else "warn", "description", "%d chars (> 5000)" % len(description))
    if re.search(r"<[a-z][^>]*>", description, re.I) and name == "openai":
        add("warn", "description", "HTML tags found; spec expects plain text")

    price = parse_price(row.get("price"))
    if row.get("price") and not price:
        add("error", "price", "format must be like '79.99 USD'")
    sale = row.get("sale_price")
    if sale:
        sale_price = parse_price(sale)
        if not sale_price:
            add("error", "sale_price", "format must be like '59.99 USD'")
        elif price and (sale_price[1] != price[1] or not 0 < sale_price[0] < price[0]):
            add("error", "sale_price", "must be positive, below price, same currency")

    availability = (row.get("availability") or "").strip()
    if availability and availability not in spec["availability"]:
        add("error", "availability", "%r not in %s" % (availability, sorted(spec["availability"])))

    for field in (spec["url"], spec["image"]):
        value = row.get(field) or ""
        if value and not value.startswith(("http://", "https://")):
            add("error", field, "must be an absolute http(s) URL")
    image = row.get(spec["image"]) or ""
    if name == "openai" and image and not re.search(r"\.(jpe?g|png)(\?|$)", image, re.I):
        add("warn", spec["image"], "spec expects a direct JPEG/PNG link")

    brand = (row.get("brand") or "").strip().lower()
    if brand in PLACEHOLDER_BRANDS:
        add("error", "brand", "placeholder brand value")

    gtin = (row.get("gtin") or "").strip()
    if gtin and not gtin_valid(gtin):
        add("error", "gtin", "invalid GTIN (length 8/12/13/14 digits with valid check digit)")
    if not gtin and not (row.get("mpn") or "").strip():
        add("warn", "gtin", "no GTIN or MPN; identity matching will be weaker (do not invent an MPN)")

    rating = row.get("star_rating")
    if rating:
        try:
            if not 0 <= float(rating) <= 5:
                add("error", "star_rating", "must be 0-5")
        except ValueError:
            add("error", "star_rating", "not a number")
        if not row.get("review_count"):
            add("warn", "review_count", "star_rating without review_count")

    if name == "openai":
        for flag in ("search", "checkout"):
            if row.get("enable_" + flag) and row.get("is_eligible_" + flag):
                add("warn", "enable_" + flag, "both enable_%s and is_eligible_%s sent; send only one" % (flag, flag))
        checkout = (row.get("enable_checkout") or row.get("is_eligible_checkout") or "").lower() == "true"
        if checkout and not (row.get("seller_privacy_policy") and row.get("seller_tos")):
            add("error", "is_eligible_checkout", "checkout needs seller_privacy_policy and seller_tos")
        if row.get("shipping_price") and row.get("shipping"):
            add("warn", "shipping", "both shipping_price and shipping sent; do not send both for the same charge")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feed", required=True)
    parser.add_argument("--spec", required=True, choices=sorted(SPECS))
    args = parser.parse_args()

    spec = SPECS[args.spec]
    rows = read_feed(args.feed)
    results, ids = [], {}
    for index, row in enumerate(rows, 2):
        issues = check_row(row, spec, args.spec)
        item_id = (row.get(spec["id"]) or "").strip()
        if item_id:
            if item_id in ids:
                issues.append({"level": "error", "field": spec["id"], "detail": "duplicate of row %d" % ids[item_id]})
            ids[item_id] = index
        if issues:
            results.append({"row": index, "id": item_id, "issues": issues})
    errors = sum(1 for r in results for i in r["issues"] if i["level"] == "error")
    print(json.dumps({"spec": args.spec, "rows": len(rows), "rows_with_issues": len(results), "errors": errors,
                      "results": results}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
