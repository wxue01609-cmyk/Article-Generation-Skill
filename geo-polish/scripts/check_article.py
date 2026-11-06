#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英文 GEO 文章机械质检（geo-polish 步骤 5 使用，只依赖标准库）。

用法：
  python3 scripts/check_article.py --articles articles.json --channel blog
  python3 scripts/check_article.py --articles articles.json --channel social --keyword-pack keywords.txt
  python3 scripts/check_article.py --articles articles.json --length long

articles.json：文章对象数组（或含 all_articles 的对象），每篇至少有 title / content（HTML）。
--keyword-pack：词包文件，每行一个 query；与含 ? 的原问句完全相同的句子不判 best 违规。
--channel：blog / qna / social / ecommerce 等，决定档位与社交形态检查（social 与 qna 互斥）。
--length：standard（默认）/ long。

输出：JSON 数组，每篇含 index / title / word_count / band / issues；有 error 级问题时退出码 1。
"""

import argparse
import html
import json
import re
import sys

BANDS = {
    "standard": (700, 900),
    "long": (1000, 1500),
    "qna": (300, 450),
    "social": (0, 350),
}

SOCIAL_CHANNELS = {"social", "x", "facebook", "linkedin"}
QNA_CHANNELS = {"qna"}

PLACEHOLDER_RE = re.compile(
    r"\[_{2,}\]|\[待补充\]|\{[a-z_]+\}|\bTBD\b|\blorem ipsum\b|\[(?:insert|brand|company|keyword)[^\]]*\]",
    re.I,
)
INTERNAL_RE = re.compile(
    r"approx_words|content_brief|content_mode|compliance_mode|structure_dna|knowledge_refs|"
    r"geo_signals|title_template|faq_theme|content_focus|全文目标字数|约\s*\d+\s*(?:字|words)\)?|"
    r"\(about \d+ words\)|target word count",
    re.I,
)
SUPERLATIVE_RE = re.compile(
    r"\bbest\b(?! fit for| practices?\b)|#1\b|\bno\.\s?1\b|\bnumber one\b|\brevolutionary\b|\bultimate\b|\bunbeatable\b|"
    r"\bperfect choice\b|\bworld'?s (?:best|leading|first)\b|\btop[- ]rated\b|\btop[- ]ranked\b|"
    r"\bindustry[- ]leading\b|\bunmatched\b|\bunrivall?ed\b|\bguaranteed?\b|\b100% (?:safe|effective|guaranteed)\b",
    re.I,
)
CTA_RE = re.compile(
    r"\bbuy (?:it )?now\b|\border (?:it )?(?:now|today)\b|\bshop now\b|\bcontact us (?:now|today)\b|"
    r"\bcall (?:us )?(?:now|today)\b|\bbook (?:a|your) (?:demo|consultation|call) (?:now|today)\b|"
    r"\bsign up (?:now|today)\b|\bget (?:a )?(?:free )?(?:quote|trial) (?:now|today)\b|"
    r"\blimited[- ]time offer\b|\bdon'?t miss out\b|\bclick here\b|\bdm (?:us|me)\b|"
    r"\bwhatsapp\b|\bwechat\b|立即购买|立即预约|加微信|扫码关注",
    re.I,
)
PRICE_RE = re.compile(
    r"(?:[$€£¥]\s?\d[\d,]*(?:\.\d+)?)|(?:\b\d[\d,]*(?:\.\d+)?\s?(?:usd|eur|gbp|dollars?|euros?)\b)|"
    r"\bstarting (?:at|from) [$€£¥]?\d|\bfrom only\b|\bper month\b|/mo\b|\d+元起",
    re.I,
)
DISCLAIMER_RE = re.compile(
    r"this (?:article|post) is (?:not sponsored|for informational purposes only|not an advertisement)|"
    r"no commercial (?:intent|promotion)",
    re.I,
)
COMPETITOR_WEAKNESS_RE = re.compile(r"one-line weakness|\bweakness(?:es)?\s*</th>", re.I)


def strip_html(text):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def word_count(text):
    return len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", text))


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def load_articles(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("all_articles") or data.get("articles") or [data]
    return data


def load_questions(path):
    """词包里含 ? 的行：既用于 best 例外，也用于原问句覆盖检查。"""
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as handle:
        return [normalize(line) for line in handle if "?" in line and normalize(line)]


def pick_band(channel, length):
    if channel in SOCIAL_CHANNELS:
        return "social"
    if channel in QNA_CHANNELS:
        return "qna"
    return "long" if length == "long" else "standard"


def find_superlatives(plain, questions):
    hits = []
    for sentence in sentences(plain):
        sentence_norm = normalize(sentence)
        if any(q in sentence_norm for q in questions):
            continue
        for match in SUPERLATIVE_RE.finditer(sentence):
            hits.append(match.group(0))
    return hits


def check(article, channel, band, questions):
    issues = []

    def add(level, code, detail):
        issues.append({"level": level, "code": code, "detail": detail})

    title = (article.get("title") or "").strip()
    content = article.get("content") or ""
    plain = strip_html(content)
    words = word_count(plain)
    low, high = BANDS[band]

    if not (low <= words <= high):
        add("error", "word_count", "%d words, band %s is %d-%d" % (words, band, low, high))

    title_words = word_count(title)
    if not (8 <= title_words <= 14) or len(title) > 90:
        add("error", "title_length", "%d words / %d chars (need 8-14 words, <=90 chars)" % (title_words, len(title)))
    if re.search(r"[:,，：]\s*$", title):
        add("error", "title_truncated", title)

    for label, text in (("title", title), ("content", plain)):
        for pattern, code in ((PLACEHOLDER_RE, "placeholder"), (INTERNAL_RE, "internal_label")):
            match = pattern.search(text)
            if match:
                add("error", code, "%s: %s" % (label, match.group(0)))

    if "**" in content:
        add("error", "markdown_bold", "** found in content")

    superlatives = find_superlatives(title + "\n" + plain, questions)
    if superlatives:
        add("error", "superlative", ", ".join(sorted(set(s.lower() for s in superlatives))))

    for pattern, code in ((CTA_RE, "cta"), (DISCLAIMER_RE, "soft_ad_disclaimer"), (COMPETITOR_WEAKNESS_RE, "competitor_weakness")):
        match = pattern.search(plain if code != "competitor_weakness" else content)
        if match:
            add("error", code, match.group(0))

    if channel != "ecommerce":
        match = PRICE_RE.search(plain)
        if match:
            add("error", "price", match.group(0))

    if band in ("social", "qna"):
        if re.search(r"<a\s", content, re.I) or re.search(r"https?://", plain):
            add("error", "post_link", "links are not allowed in social/community posts")
        if re.search(r"<h[2-6][\s>]", content, re.I):
            add("error", "post_heading", "h2-h6 not allowed in social/community posts")
        if re.search(r"<table[\s>]", content, re.I):
            add("error", "post_table", "tables not allowed in social/community posts")
        if re.search(r"\btl;?dr\b", plain, re.I):
            add("error", "post_tldr", "TL;DR not allowed in social/community posts")
    else:
        if plain.count("?") < 2:
            add("warn", "few_questions", "fewer than 2 questions; keyword-pack questions may be missing")

    if questions:
        plain_norm = normalize(plain)
        missing = [q for q in questions if q not in plain_norm]
        if missing and band not in ("social", "qna"):
            add("warn", "query_not_verbatim", "%d keyword-pack questions not found verbatim: %s" % (len(missing), "; ".join(missing[:3])))

    return {"title": title, "word_count": words, "band": band, "issues": issues}


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--articles", required=True)
    parser.add_argument("--channel", default="blog")
    parser.add_argument("--length", default="standard", choices=["standard", "long"])
    parser.add_argument("--keyword-pack")
    args = parser.parse_args()

    channel = args.channel.strip().lower()
    band = pick_band(channel, args.length)
    questions = load_questions(args.keyword_pack)

    results = []
    for index, article in enumerate(load_articles(args.articles), 1):
        result = check(article, channel, band, questions)
        result["index"] = index
        results.append(result)

    print(json.dumps(results, ensure_ascii=False, indent=2))
    has_error = any(issue["level"] == "error" for r in results for issue in r["issues"])
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
