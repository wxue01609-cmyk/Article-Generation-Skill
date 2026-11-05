# -*- coding: utf-8 -*-
"""资产渲染工具：把正文文本或 SKU 改造 JSON 渲染成可发布 HTML。
支持三种模式：asset（整页）/ compare（改前改后对比页）/ modules（商品页模块片段）。
所有样式内联，无外链依赖，禁止 Markdown 语法残留。"""
import html as _html
import json
import re

CSS = """
:root{--ink:#111827;--muted:#5b6472;--line:#e5e7eb;--brand:#0f766e;--bg:#f8fafc;
--ok:#e8f5e9;--warn:#fff7ed}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:32px 20px 64px}
article{background:#fff;border:1px solid var(--line);border-radius:14px;padding:40px 36px;
box-shadow:0 8px 30px rgba(15,23,42,.05)}
h1{font-size:32px;line-height:1.3;margin:0 0 18px}
h2{font-size:24px;line-height:1.35;margin:36px 0 14px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:19px;margin:26px 0 10px}
p{margin:0 0 14px}
ul,ol{margin:0 0 16px;padding-left:22px}
li{margin:6px 0}
table{width:100%;border-collapse:collapse;margin:16px 0;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:10px 12px;text-align:left;font-size:15px}
th{background:#f3f4f6;font-weight:600}
blockquote{margin:18px 0;padding:12px 18px;border-left:4px solid var(--brand);background:#f0fdfa;color:var(--muted)}
.cta{display:inline-block;margin:24px 0 4px;padding:13px 26px;border-radius:999px;
background:var(--brand);color:#fff;text-decoration:none;font-weight:600}
.imgbox{margin:18px 0}
.imgbox img{max-width:100%;border-radius:12px}
.meta{color:var(--muted);font-size:14px;margin-bottom:6px}
.badge{display:inline-block;margin:0 8px 8px 0;padding:5px 12px;border-radius:999px;
background:#ecfdf5;color:#065f46;font-size:13px}
.compare{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.pane{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px}
.pane h4{margin:0 0 10px;font-size:15px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.after{border-color:#86efac;background:#f7fef9}
.chg{border:1px solid var(--line);border-radius:12px;margin:14px 0;overflow:hidden;background:#fff}
.chg summary{cursor:pointer;padding:14px 16px;font-weight:600;background:#f9fafb}
.chg .body{padding:0 16px 16px}
.diff-add{background:var(--ok)}
.diff-del{background:#fdecea;text-decoration:line-through;color:#7f1d1d}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin:0 0 18px;color:var(--muted);font-size:14px}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
.dot.before{background:#fdecea}.dot.after{background:#c8e6c9}
@media (max-width:760px){
 .wrap{padding:18px 12px 40px}article{padding:22px 16px}
 h1{font-size:26px}h2{font-size:20px}
 .compare{grid-template-columns:1fr}
}
"""

SKU_CSS = """
.sku{max-width:860px;margin:0 auto}
.sku-grid{display:grid;grid-template-columns:1.1fr 1fr;gap:28px;align-items:start}
.sku-img img{width:100%;border-radius:14px;border:1px solid var(--line)}
.sku-title{font-size:26px;margin:0 0 8px}
.sku-price{font-size:24px;font-weight:700;color:var(--brand);margin:8px 0}
.sku-meta{color:var(--muted);font-size:14px}
.block{margin:26px 0}
.faq-q{font-weight:650;margin:14px 0 4px}
.fit{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.fit div{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px}
@media (max-width:760px){.sku-grid,.fit{grid-template-columns:1fr}}
"""


def _esc(s):
    return _html.escape(str(s if s is not None else ""), quote=True)


def _inline(text):
    text = _esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
                  r'<a href="\2" rel="noopener">\1</a>', text)
    return text


def md_to_html(md):
    if not md:
        return ""
    if "<p" in md or "<h1" in md:
        return md
    lines = md.replace("\r\n", "\n").split("\n")
    out, buf, i = [], [], 0
    def flush():
        if buf:
            out.append("<p>" + "<br>".join(_inline(x) for x in buf) + "</p>")
            buf.clear()
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            flush(); i += 1; continue
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            flush()
            lvl = min(len(m.group(1)), 6)
            out.append("<h%d>%s</h%d>" % (lvl, _inline(m.group(2)), lvl))
            i += 1; continue
        if ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i+1]):
            flush()
            header = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ["<table><thead><tr>"] + ["<th>%s</th>" % _inline(c) for c in header] + ["</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>" + "".join("<td>%s</td>" % _inline(c) for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t)); continue
        if re.match(r"^[-*]\s+", ln):
            flush(); items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append("<li>%s</li>" % _inline(re.sub(r"^[-*]\s+", "", lines[i])))
                i += 1
            out.append("<ul>%s</ul>" % "".join(items)); continue
        if re.match(r"^\d+\.\s+", ln):
            flush(); items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                items.append("<li>%s</li>" % _inline(re.sub(r"^\d+\.\s+", "", lines[i])))
                i += 1
            out.append("<ol>%s</ol>" % "".join(items)); continue
        if ln.startswith(">"):
            flush(); out.append("<blockquote>%s</blockquote>" % _inline(ln.lstrip("> ")))
            i += 1; continue
        buf.append(ln.strip()); i += 1
    flush()
    return "\n".join(out)


def page(title, body, lang="en", extra_css=""):
    return ("<!doctype html>\n<html lang=\"%s\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            "<title>%s</title>\n<style>%s%s</style>\n</head>\n<body>\n<div class=\"wrap\">\n%s\n</div>\n</body>\n</html>"
            % (_esc(lang), _esc(title), CSS, extra_css, body))


def render_asset(p):
    title = p.get("title") or "Untitled"
    lang = p.get("lang") or "en"
    body = md_to_html(p.get("body_html") or p.get("body") or p.get("markdown") or "")
    img = p.get("image_url") or ""
    img_html = ('<div class="imgbox"><img src="%s" alt="%s"></div>'
                % (_esc(img), _esc(p.get("image_alt") or title))) if img else ""
    badges = "".join('<span class="badge">%s</span>' % _esc(b) for b in (p.get("badges") or []))
    cta = p.get("cta") or ""
    cta_html = ('<a class="cta" href="%s">%s</a>' % (_esc(p.get("cta_url") or "#"), _esc(cta))) if cta else ""
    meta = p.get("meta") or ""
    meta_html = '<div class="meta">%s</div>' % _esc(meta) if meta else ""
    return page(title, '<article>%s<h1>%s</h1>%s%s%s%s</article>' % (meta_html, _esc(title), badges, img_html, body, cta_html), lang)


def render_sku_modules(p):
    s = p.get("sku") or p
    prod = s.get("product") or {}
    title = prod.get("title") or p.get("title") or ""
    img = prod.get("image_url") or ""
    price = prod.get("price") or {}
    price_txt = ""
    if isinstance(price, dict) and price.get("amount"):
        price_txt = "%s %s" % (price.get("currency") or "", price.get("amount"))
    rating = prod.get("rating") or {}
    rating_txt = ""
    if isinstance(rating, dict) and rating.get("value"):
        rating_txt = "%s / 5 (%s reviews)" % (rating.get("value"), rating.get("count") or 0)
    parts = ['<!-- module: 商品卡 -->', '<section class="sku">', '<div class="sku-grid">']
    parts.append('<div class="sku-img">%s</div>' % (
        '<img src="%s" alt="%s">' % (_esc(img), _esc(prod.get("image_alt") or title)) if img else ""))
    meta_bits = [x for x in [prod.get("availability"), ("SKU: %s" % prod.get("sku")) if prod.get("sku") else "",
                             ("GTIN: %s" % prod.get("gtin")) if prod.get("gtin") else "", rating_txt] if x]
    parts.append('<div><h1 class="sku-title">%s</h1><div class="sku-price">%s</div><div class="sku-meta">%s</div></div>'
                 % (_esc(title), _esc(price_txt), _esc(" · ".join(meta_bits))))
    parts.append('</div>')
    if s.get("core_answer"):
        parts += ['<!-- module: 核心答案 -->', '<div class="block"><p>%s</p></div>' % _esc(s["core_answer"])]
    if s.get("trust_badges"):
        parts.append('<div class="block">%s</div>' % "".join('<span class="badge">%s</span>' % _esc(b) for b in s["trust_badges"]))
    if s.get("benefits"):
        parts.append('<div class="block"><h2>Why it works</h2><ul>%s</ul></div>' %
                     "".join("<li><strong>%s</strong> — %s</li>" % (_esc(b.get("feature")), _esc(b.get("meaning"))) for b in s["benefits"]))
    if s.get("fit"):
        fit = s["fit"]
        parts.append('<div class="block"><h2>Who it fits</h2><div class="fit"><div><h3>Good fit</h3><ul>%s</ul></div>'
                     '<div><h3>Not ideal for</h3><ul>%s</ul></div></div></div>' %
                     ("".join("<li>%s</li>" % _esc(x) for x in fit.get("good") or []),
                      "".join("<li>%s</li>" % _esc(x) for x in fit.get("not_good") or [])))
    if s.get("specs"):
        rows = "".join("<tr><th>%s</th><td>%s</td></tr>" % (_esc(x.get("name")), _esc(x.get("value"))) for x in s["specs"])
        parts.append('<!-- module: 参数表 --><div class="block"><h2>Specifications</h2><table>%s</table></div>' % rows)
    if s.get("faq"):
        qs = "".join('<div class="faq-q">%s</div><p>%s</p>' % (_esc(x.get("question")), _esc(x.get("answer"))) for x in s["faq"])
        parts.append('<!-- module: FAQ --><div class="block"><h2>FAQ</h2>%s</div>' % qs)
    if s.get("shipping_returns_warranty"):
        parts.append('<!-- module: 购买信息 --><div class="block"><h2>Shipping &amp; returns</h2><p>%s</p></div>' % _esc(s["shipping_returns_warranty"]))
    if s.get("cta"):
        parts.append('<div class="block"><a class="cta" href="%s">%s</a></div>' % (_esc(prod.get("url") or p.get("cta_url") or "#"), _esc(s["cta"])))
    parts.append('</section>')
    return "\n".join(parts)


def render_compare(p):
    title = p.get("title") or "Before / After"
    changes = p.get("changes") or []
    rows = []
    for i, c in enumerate(changes, 1):
        module = c.get("module") or ("Item %d" % i)
        before = c.get("before") or "（页面无此模块）"
        after = c.get("after") or ""
        problem = c.get("problem") or ""
        rows.append('<div class="chg"><details open><summary>%02d · %s</summary><div class="body">'
                    '<div class="compare"><div class="pane"><h4>改前</h4><p class="diff-del">%s</p></div>'
                    '<div class="pane after"><h4>改后</h4><p class="diff-add">%s</p></div></div>'
                    '%s</div></details></div>'
                    % (i, _esc(module), _esc(before), _esc(after),
                       ('<p class="meta">解决的问题：%s</p>' % _esc(problem)) if problem else ""))
    legend = ('<div class="legend"><span><i class="dot before"></i>改前原文</span>'
              '<span><i class="dot after"></i>改后文案</span></div>')
    intro = p.get("core_answer") or ""
    body = ('<article><h1>%s</h1>%s%s%s</article>'
            % (_esc(title), legend, ('<p class="meta">%s</p>' % _esc(intro)) if intro else "", "".join(rows)))
    return page(title, body, p.get("lang") or "zh")


def run(params):
    mode = (params.get("mode") or "asset").strip().lower()
    if mode == "compare":
        return {"status": "ok", "mode": mode, "html": render_compare(params)}
    if mode in ("modules", "sku", "sku_modules"):
        return {"status": "ok", "mode": "modules", "html": render_sku_modules(params)}
    return {"status": "ok", "mode": "asset", "html": render_asset(params)}
