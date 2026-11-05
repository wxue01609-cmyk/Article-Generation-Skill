#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""站点与页面的 AI 可读性审计（只依赖标准库）。

用法：
  python3 scripts/audit_site.py --project ./acme-us-2026c1 [--bot-check] [--timeout 15]

审计对象：contract.inputs.site.target_urls + 全部业务对象 URL。
站点级：robots.txt 对主要 AI 爬虫是否放行、sitemap 是否可访问、llms.txt 是否存在（仅记录，不作为排名依据）。
页面级：状态码、跳转、noindex（meta / X-Robots-Tag）、canonical、title、meta description、H1、
       原始 HTML 正文词数（不执行 JS）、JSON-LD 类型、Product 的 Offer 价格与库存。
--bot-check：再用 AI 爬虫 UA 请求一次，识别 WAF/CDN 对爬虫的拦截。
网络不可达时记为 unreachable，不当作通过。输出 diagnosis/site_audit.json。
"""

import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
# 搜索/引用类爬虫是 GEO 的关键；训练类爬虫（GPTBot、ClaudeBot、CCBot）单独列出，是否放行由客户决定。
AI_BOTS = {
    "OAI-SearchBot": "search",
    "ChatGPT-User": "user_fetch",
    "GPTBot": "training",
    "PerplexityBot": "search",
    "Perplexity-User": "user_fetch",
    "Claude-SearchBot": "search",
    "Claude-User": "user_fetch",
    "ClaudeBot": "training",
    "Googlebot": "search",
    "Google-Extended": "training_control",
    "Bingbot": "search",
    "Applebot-Extended": "training_control",
    "CCBot": "training",
}
BOT_CHECK_UA = {
    "OAI-SearchBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch(url, timeout, ua=BROWSER_UA):
    request = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,*/*"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(3000000).decode("utf-8", errors="replace")
            return {"status": response.status, "final_url": response.geturl(), "headers": dict(response.headers), "body": body}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "final_url": url, "headers": dict(exc.headers or {}), "body": "", "error": "HTTP %d" % exc.code}
    except Exception as exc:  # 网络受限、DNS、超时、TLS
        return {"status": None, "final_url": url, "headers": {}, "body": "", "error": "unreachable: %s" % getattr(exc, "reason", exc)}


def text_words(body):
    body = re.sub(r"<(script|style|noscript|template)[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    return len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", html.unescape(body)))


def meta(body, name):
    pattern = r"<meta[^>]+(?:name|property)=['\"]%s['\"][^>]*>" % re.escape(name)
    tag = re.search(pattern, body, re.I)
    if not tag:
        return None
    content = re.search(r"content=['\"]([^'\"]*)['\"]", tag.group(0), re.I)
    return html.unescape(content.group(1)).strip() if content else ""


def jsonld_blocks(body):
    blocks, errors = [], 0
    for raw in re.findall(r"<script[^>]+type=['\"]application/ld\+json['\"][^>]*>(.*?)</script>", body, re.S | re.I):
        try:
            data = json.loads(raw.strip())
        except ValueError:
            errors += 1
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                if "@graph" in item:
                    stack.extend(item["@graph"] if isinstance(item["@graph"], list) else [item["@graph"]])
                blocks.append(item)
            elif isinstance(item, list):
                stack.extend(item)
    return blocks, errors


def types_of(item):
    value = item.get("@type")
    return value if isinstance(value, list) else [value] if value else []


def product_offer(blocks):
    for item in blocks:
        if "Product" in types_of(item) or "ProductGroup" in types_of(item):
            offers = item.get("offers")
            offers = offers[0] if isinstance(offers, list) and offers else offers
            if isinstance(offers, dict) and "AggregateOffer" in types_of(offers):
                price = offers.get("lowPrice")
            else:
                price = (offers or {}).get("price") if isinstance(offers, dict) else None
            return {
                "has_product": True,
                "has_offer": bool(offers),
                "price": price,
                "price_currency": (offers or {}).get("priceCurrency") if isinstance(offers, dict) else None,
                "availability": (offers or {}).get("availability") if isinstance(offers, dict) else None,
                "gtin": next((item.get(k) for k in ("gtin", "gtin8", "gtin12", "gtin13", "gtin14") if item.get(k)), None),
                "has_rating": bool(item.get("aggregateRating")),
            }
    return {"has_product": False}


def audit_page(url, timeout, robots, bot_check):
    result = {"url": url, "issues": [], "blocked": False}
    response = fetch(url, timeout)
    result["status"] = response["status"]
    result["final_url"] = response["final_url"]
    if response.get("error") and response["status"] is None:
        result["error"] = response["error"]
        result["issues"].append({"severity": "unknown", "issue": "page unreachable from audit environment; verify manually"})
        return result
    if not response["status"] or response["status"] >= 400:
        result["blocked"] = True
        result["issues"].append({"severity": "block", "issue": "HTTP %s" % response["status"]})
        return result

    body = response["body"]
    headers = {k.lower(): v for k, v in response["headers"].items()}
    robots_meta = (meta(body, "robots") or "") + " " + headers.get("x-robots-tag", "")
    result["noindex"] = "noindex" in robots_meta.lower()
    canonical = re.search(r"<link[^>]+rel=['\"]canonical['\"][^>]*href=['\"]([^'\"]+)['\"]", body, re.I)
    title = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
    result["title"] = html.unescape(title.group(1)).strip() if title else None
    result["meta_description"] = meta(body, "description")
    result["canonical"] = canonical.group(1) if canonical else None
    result["h1_count"] = len(re.findall(r"<h1[\s>]", body, re.I))
    result["raw_text_words"] = text_words(body)
    blocks, errors = jsonld_blocks(body)
    result["jsonld_types"] = sorted({t for b in blocks for t in types_of(b) if t})
    result["jsonld_parse_errors"] = errors
    result["product"] = product_offer(blocks)

    disallowed = []
    if robots is not None:
        for bot, kind in AI_BOTS.items():
            if kind in ("search", "user_fetch") and not robots.can_fetch(bot, url):
                disallowed.append(bot)
    result["robots_disallowed_search_bots"] = disallowed

    if result["noindex"]:
        result["blocked"] = True
        result["issues"].append({"severity": "block", "issue": "noindex on page"})
    if disallowed:
        result["blocked"] = True
        result["issues"].append({"severity": "block", "issue": "robots.txt disallows " + ", ".join(disallowed)})
    if result["raw_text_words"] < 150:
        result["issues"].append({"severity": "high", "issue": "only %d words in raw HTML; content may depend on JS rendering" % result["raw_text_words"]})
    if result["canonical"] and urllib.parse.urlsplit(result["canonical"]).path.rstrip("/") != urllib.parse.urlsplit(response["final_url"]).path.rstrip("/"):
        result["issues"].append({"severity": "medium", "issue": "canonical points elsewhere: " + result["canonical"]})
    if not result["title"]:
        result["issues"].append({"severity": "medium", "issue": "missing <title>"})
    if result["h1_count"] != 1:
        result["issues"].append({"severity": "low", "issue": "%d <h1> tags" % result["h1_count"]})
    if errors:
        result["issues"].append({"severity": "medium", "issue": "%d JSON-LD blocks fail to parse" % errors})

    if bot_check:
        result["bot_check"] = {}
        for bot, ua in BOT_CHECK_UA.items():
            bot_response = fetch(url, timeout, ua)
            result["bot_check"][bot] = bot_response["status"]
            if bot_response["status"] and bot_response["status"] >= 400:
                result["blocked"] = True
                result["issues"].append({"severity": "block", "issue": "%s user-agent receives HTTP %s (WAF/CDN)" % (bot, bot_response["status"])})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--bot-check", action="store_true")
    args = parser.parse_args()

    contract = load_json(os.path.join(args.project, "contract.json"))
    site = (contract.get("inputs") or {}).get("site") or {}
    urls = list(site.get("target_urls") or [])
    for line in contract.get("business_lines") or []:
        for obj in line.get("objects") or []:
            if obj.get("url") and obj["url"] not in urls:
                urls.append(obj["url"])

    domain = contract["brand"]["official_domain"]
    origin = domain if domain.startswith("http") else "https://" + domain
    origin = origin.rstrip("/")

    site_level = {"origin": origin}
    robots_response = fetch(origin + "/robots.txt", args.timeout)
    robots = None
    if robots_response["status"] == 200:
        robots = urllib.robotparser.RobotFileParser()
        robots.parse(robots_response["body"].splitlines())
        site_level["robots_txt"] = "ok"
        site_level["robots_by_bot"] = {bot: robots.can_fetch(bot, origin + "/") for bot in AI_BOTS}
    else:
        site_level["robots_txt"] = robots_response.get("error") or "HTTP %s" % robots_response["status"]
    sitemap_url = site.get("sitemap_url") or origin + "/sitemap.xml"
    sitemap_response = fetch(sitemap_url, args.timeout)
    site_level["sitemap"] = {"url": sitemap_url, "status": sitemap_response["status"], "error": sitemap_response.get("error")}
    llms = fetch(origin + "/llms.txt", args.timeout)
    site_level["llms_txt_present"] = llms["status"] == 200

    pages = [audit_page(url, args.timeout, robots, args.bot_check) for url in urls]
    result = {
        "schema_version": "geo-site-audit/v1",
        "project_id": contract.get("project_id"),
        "audited_at": datetime.date.today().isoformat(),
        "site": site_level,
        "pages": pages,
        "unreachable_count": sum(1 for p in pages if p.get("error")),
    }
    out_path = os.path.join(args.project, "diagnosis", "site_audit.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"output": out_path, "pages": len(pages), "blocked": sum(1 for p in pages if p.get("blocked")),
                      "unreachable": result["unreachable_count"], "robots_txt": site_level["robots_txt"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
