#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实际请求文章中的链接，判断是否可用（geo-polish 步骤 3 L-verify 使用，只依赖标准库）。

用法：
  python3 scripts/check_links.py --articles articles.json
  python3 scripts/check_links.py --url https://example.com/a --url https://example.com/b

判定：
  ok                最终状态码 2xx，且页面不是软 404，跳转后仍在同一站点
  redirect_offsite  跳转到了另一个注册域名（常见于域名过期、停放页），需人工或替代
  dead              4xx/5xx，或页面标题/正文呈现 not found 等软 404 信号
  unreachable       DNS/连接/超时/网络受限，或 401/403/429 反爬拦截——无法下结论，不得当作 ok

输出：JSON {"results": [{url, status, http_status, final_url, reason}]}；存在 dead/redirect_offsite/unreachable 时退出码 1。
"""

import argparse
import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
SOFT_404_RE = re.compile(
    r"<title>[^<]*(?:404|not found|page not found|page doesn'?t exist|no longer available)[^<]*</title>|"
    r"\b(?:404 (?:error|page)|page (?:you requested )?(?:was )?not found|this page (?:does not|doesn'?t) exist|"
    r"domain (?:is )?for sale|buy this domain)\b",
    re.I,
)
BLOCKED_CODES = {401, 403, 405, 429, 999}


def extract_urls(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("all_articles") or data.get("articles") or [data]
    urls = []
    for article in data:
        content = article.get("content") or ""
        urls.extend(re.findall(r"""href\s*=\s*['"](https?://[^'"\s]+)['"]""", content, re.I))
        urls.extend(article.get("source_urls") or [])
    seen, unique = set(), []
    for url in urls:
        if url.startswith(("http://", "https://")) and url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def site_of(url):
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    parts = host.split(".")
    if len(parts) >= 3 and len(parts[-1]) == 2 and parts[-2] in {"co", "com", "org", "net", "gov", "edu", "ac"}:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def fetch(url, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        body = response.read(200000).decode("utf-8", errors="replace")
        return response.status, response.geturl(), body


def check(url, timeout):
    result = {"url": url, "status": "", "http_status": None, "final_url": "", "reason": ""}
    try:
        code, final_url, body = fetch(url, timeout)
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        result["final_url"] = getattr(exc, "filename", None) or url
        if exc.code in BLOCKED_CODES:
            result["status"] = "unreachable"
            result["reason"] = "HTTP %d: blocked or rate-limited, verify manually" % exc.code
        else:
            result["status"] = "dead"
            result["reason"] = "HTTP %d" % exc.code
        return result
    except (urllib.error.URLError, socket.timeout, ssl.SSLError, ConnectionError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        result["status"] = "unreachable"
        result["reason"] = "network error: %s" % reason
        return result

    result["http_status"] = code
    result["final_url"] = final_url
    if site_of(final_url) != site_of(url):
        result["status"] = "redirect_offsite"
        result["reason"] = "redirected to %s" % site_of(final_url)
    elif SOFT_404_RE.search(body):
        result["status"] = "dead"
        result["reason"] = "soft 404: page content says not found"
    else:
        result["status"] = "ok"
        result["reason"] = "HTTP %d" % code
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--articles", help="文章 JSON（数组或含 all_articles 的对象）")
    parser.add_argument("--url", action="append", help="单独校验的 URL，可重复传入")
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()

    urls = list(args.url or [])
    if args.articles:
        urls.extend(u for u in extract_urls(args.articles) if u not in urls)
    if not urls:
        parser.error("至少需要 --articles 或 --url")

    results = [check(url, args.timeout) for url in urls]
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0 if all(r["status"] == "ok" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
