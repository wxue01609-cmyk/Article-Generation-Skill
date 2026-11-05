#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验商品 JSON-LD，并与 feed 交叉核对（只依赖标准库）。

用法：
  python3 scripts/check_product_schema.py --jsonld product.jsonld [--feed feed_openai.csv] [--page pdp.html]

检查：@context、Product/ProductGroup、name/image/brand/offers；Offer 的 price/priceCurrency/availability；
GTIN 校验位；aggregateRating 字段完整；--feed 时按 url/sku/gtin 匹配 feed 行比较价格、币种、库存、GTIN；
--page 时检查评分/评论数是否出现在页面正文中（schema 中的评分必须在页面可见）。
有 error 时退出码 1。
"""

import argparse
import csv
import html
import json
import re
import sys

AVAILABILITY = {
    "https://schema.org/InStock": "in_stock", "https://schema.org/OutOfStock": "out_of_stock",
    "https://schema.org/PreOrder": "pre_order", "https://schema.org/BackOrder": "backorder",
    "https://schema.org/SoldOut": "out_of_stock", "https://schema.org/LimitedAvailability": "in_stock",
    "https://schema.org/Discontinued": "out_of_stock", "https://schema.org/InStoreOnly": "in_stock",
    "https://schema.org/OnlineOnly": "in_stock", "https://schema.org/PreSale": "pre_order",
}
FEED_AVAILABILITY_ALIASES = {"preorder": "pre_order"}


def gtin_valid(value):
    digits = str(value or "").strip()
    if not digits.isdigit() or len(digits) not in (8, 12, 13, 14):
        return False
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def types_of(item):
    value = item.get("@type")
    return value if isinstance(value, list) else [value] if value else []


def products(data):
    stack = data if isinstance(data, list) else [data]
    found = []
    while stack:
        item = stack.pop(0)
        if isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, dict):
            if "@graph" in item:
                stack.extend(item["@graph"] if isinstance(item["@graph"], list) else [item["@graph"]])
            if set(types_of(item)) & {"Product", "ProductGroup"}:
                found.append(item)
                for variant in item.get("hasVariant") or []:
                    if isinstance(variant, dict):
                        found.append(variant)
    return found


def gtin_of(item):
    for key in ("gtin", "gtin8", "gtin12", "gtin13", "gtin14"):
        if item.get(key):
            return str(item[key])
    return None


def offers_of(item):
    offers = item.get("offers")
    if isinstance(offers, dict):
        return [offers]
    return [o for o in offers or [] if isinstance(o, dict)]


def read_feed(path):
    delimiter = "\t" if path.lower().endswith((".tsv", ".txt")) else ","
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def match_feed(rows, item, offer):
    url = (offer.get("url") or item.get("url") or "").split("#")[0]
    gtin = gtin_of(item)
    sku = item.get("sku")
    for row in rows:
        row_url = row.get("url") or row.get("link") or ""
        if gtin and (row.get("gtin") or "") == gtin:
            return row
        if sku and sku in (row.get("item_id"), row.get("id"), row.get("offer_id"), row.get("mpn")):
            return row
        if url and row_url.split("#")[0] == url:
            return row
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jsonld", required=True)
    parser.add_argument("--feed")
    parser.add_argument("--page")
    args = parser.parse_args()

    with open(args.jsonld, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    feed_rows = read_feed(args.feed) if args.feed else []
    page_text = ""
    if args.page:
        with open(args.page, "r", encoding="utf-8") as handle:
            page_text = html.unescape(re.sub(r"<[^>]+>", " ", handle.read()))

    issues = []

    def add(level, where, detail):
        issues.append({"level": level, "where": where, "detail": detail})

    roots = data if isinstance(data, list) else [data]
    if not any("schema.org" in str(r.get("@context", "")) for r in roots if isinstance(r, dict)):
        add("error", "@context", "missing schema.org @context")
    items = products(data)
    if not items:
        add("error", "@type", "no Product / ProductGroup found")

    for item in items:
        name = item.get("name") or "(unnamed)"
        is_group = "ProductGroup" in types_of(item)
        for field in ("name", "image"):
            if not item.get(field):
                add("error", name, "missing %s" % field)
        if not item.get("brand"):
            add("warn", name, "missing brand")
        gtin = gtin_of(item)
        if gtin and not gtin_valid(gtin):
            add("error", name, "invalid GTIN %s" % gtin)
        rating = item.get("aggregateRating")
        if rating:
            if not rating.get("ratingValue") or not (rating.get("reviewCount") or rating.get("ratingCount")):
                add("error", name, "aggregateRating needs ratingValue and reviewCount/ratingCount")
            elif args.page and (str(rating.get("ratingValue")) not in page_text or str(rating.get("reviewCount") or rating.get("ratingCount")) not in page_text):
                add("error", name, "rating %s / count %s not visible in page text" % (rating.get("ratingValue"), rating.get("reviewCount") or rating.get("ratingCount")))
        offers = offers_of(item)
        if not offers and not is_group:
            add("error", name, "missing offers")
        for offer in offers:
            price = offer.get("price") if "AggregateOffer" not in types_of(offer) else offer.get("lowPrice")
            if price in (None, ""):
                add("error", name, "offer missing price")
            if not offer.get("priceCurrency"):
                add("error", name, "offer missing priceCurrency")
            availability = offer.get("availability")
            if availability not in AVAILABILITY:
                add("error", name, "availability must be a schema.org URL, got %r" % availability)
            if not offer.get("hasMerchantReturnPolicy"):
                add("warn", name, "no hasMerchantReturnPolicy")
            if not offer.get("shippingDetails"):
                add("warn", name, "no shippingDetails")
            if feed_rows:
                row = match_feed(feed_rows, item, offer)
                if row is None:
                    add("warn", name, "no matching feed row (by gtin / sku / url)")
                    continue
                feed_price = (row.get("sale_price") or row.get("price") or "").split(" ")
                if len(feed_price) == 2:
                    try:
                        if abs(float(feed_price[0]) - float(price)) > 0.005:
                            add("error", name, "price %s differs from feed %s" % (price, " ".join(feed_price)))
                    except (TypeError, ValueError):
                        add("error", name, "price not numeric: %r" % price)
                    if offer.get("priceCurrency") and feed_price[1] != offer.get("priceCurrency"):
                        add("error", name, "currency %s differs from feed %s" % (offer.get("priceCurrency"), feed_price[1]))
                feed_av = FEED_AVAILABILITY_ALIASES.get(row.get("availability"), row.get("availability"))
                if availability in AVAILABILITY and feed_av and AVAILABILITY[availability] != feed_av:
                    add("error", name, "availability %s differs from feed %s" % (availability, row.get("availability")))
                if gtin and row.get("gtin") and row["gtin"] != gtin:
                    add("error", name, "GTIN %s differs from feed %s" % (gtin, row["gtin"]))

    print(json.dumps({"products": len(items), "issues": issues}, ensure_ascii=False, indent=2))
    return 1 if any(i["level"] == "error" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
