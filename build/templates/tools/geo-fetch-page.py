# -*- coding: utf-8 -*-
"""网页抓取工具：抓取商品页 URL，提取标题/描述/正文/标题层级/参数表/JSON-LD 商品/图片/价格。
所有字段只来自页面真实内容，抓不到返回空值，禁止编造。"""
import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.og_image = ""
        self.headings = []
        self.tables = []
        self.images = []
        self.jsonld = []
        self.text_parts = []
        self._in_title = False
        self._in_jsonld = False
        self._jsonld_buf = []
        self._skip_depth = 0
        self._text_buf = []
        self._cur_table = None
        self._cur_row = None
        self._cur_cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            if tag == "script" and a.get("type", "").strip().lower() == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_buf = []
            else:
                self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
            self._text_buf = []
            return
        if tag in ("h1", "h2", "h3"):
            self._text_buf = []
            self._cur_heading = tag
            return
        if tag == "table":
            self._cur_table = []
            return
        if tag == "tr" and self._cur_table is not None:
            self._cur_row = []
            return
        if tag in ("td", "th") and self._cur_row is not None:
            self._cur_cell = []
            self._text_buf = self._cur_cell
            return
        if tag == "img":
            src = a.get("src") or ""
            if src:
                self.images.append(src)
            return
        if tag == "meta":
            name = (a.get("name") or a.get("property") or "").strip().lower()
            content = (a.get("content") or "").strip()
            if name == "description" and not self.description:
                self.description = content
            if name == "og:image" and not self.og_image:
                self.og_image = content
        if tag in ("p", "li", "blockquote", "div", "section", "article", "span", "td", "th"):
            self._text_buf = self._text_buf if tag in ("td", "th") else []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            if self._in_jsonld:
                try:
                    raw = "".join(self._jsonld_buf).strip()
                    if raw:
                        data = json.loads(raw)
                        self.jsonld.append(data)
                except Exception:
                    pass
                self._in_jsonld = False
            elif self._skip_depth > 0:
                self._skip_depth -= 1
            return
        if tag == "title" and self._in_title:
            self.title = "".join(self._text_buf).strip()
            self._in_title = False
            return
        if tag in ("h1", "h2", "h3"):
            txt = " ".join("".join(self._text_buf).split())
            if txt:
                self.headings.append({"level": tag, "text": txt})
            self._text_buf = []
            return
        if tag == "table":
            self.tables.append(self._cur_table or [])
            self._cur_table = None
            return
        if tag == "tr" and self._cur_row is not None:
            if self._cur_table is not None:
                self._cur_table.append(self._cur_row)
            self._cur_row = None
            return
        if tag in ("td", "th") and self._cur_cell is not None:
            txt = " ".join("".join(self._cur_cell).split())
            self._cur_row.append(txt)
            self._cur_cell = None
            self._text_buf = []
            return

    def handle_data(self, data):
        if self._in_jsonld:
            self._jsonld_buf.append(data)
            return
        self._text_buf.append(data)


def _walk_jsonld(obj, out, path=""):
    if isinstance(obj, dict):
        if obj.get("@type") or obj.get("name") or obj.get("price") or obj.get("sku"):
            if any(k in obj for k in ("name", "price", "sku", "aggregateRating", "offers")):
                out.append(obj)
        for k, v in obj.items():
            _walk_jsonld(v, out, path + "/" + str(k))
    elif isinstance(obj, list):
        for it in obj:
            _walk_jsonld(it, out, path)


def _clean_text(parts):
    return re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip()


def run(params):
    url = (params.get("url") or "").strip()
    timeout = int(params.get("timeout") or 20)
    if not url:
        return {"status": "failed", "error": "缺少 url 参数"}
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            final_url = resp.geturl()
            ctype = resp.headers.get("Content-Type", "")
            if "text/html" not in ctype and "xhtml" not in ctype:
                return {"page": params.get("page", 1), "status": "failed",
                        "final_url": final_url, "error": "非 HTML 页面: " + ctype}
    except Exception as e:
        return {"page": params.get("page", 1), "status": "failed",
                "final_url": url, "error": "抓取失败: %s" % e}
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            html = raw.decode(enc)
            break
        except Exception:
            continue
    ex = _Extractor()
    try:
        ex.feed(html)
    except Exception:
        pass
    text = _clean_text(ex.text_parts)
    products = []
    for ld in ex.jsonld:
        _walk_jsonld(ld, products)
    product = {}
    if products:
        p = products[0]
        product = {
            "name": p.get("name", ""),
            "sku": p.get("sku", ""),
            "gtin": p.get("gtin") or p.get("gtin13") or p.get("gtin8") or "",
            "price": {"amount": "", "currency": ""},
            "availability": "",
            "rating": {"value": "", "count": ""},
            "image": "",
        }
        offers = p.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if isinstance(offers, dict):
            price = offers.get("price")
            cur = offers.get("priceCurrency")
            product["price"] = {"amount": str(price) if price is not None else "",
                                "currency": cur or ""}
            product["availability"] = str(offers.get("availability") or "")
        rating = p.get("aggregateRating") or {}
        if isinstance(rating, dict):
            product["rating"] = {"value": rating.get("ratingValue") or "",
                                 "count": rating.get("reviewCount") or ""}
        img = p.get("image")
        if isinstance(img, list):
            img = img[0] if img else ""
        product["image"] = img or ex.og_image or (ex.images[0] if ex.images else "")
    prices = re.findall(r"([A-Z$€£¥]{1,3})\s?(\d{1,3}(?:[.,]\d{2,3})?)", text)
    prices_out = []
    seen = set()
    for cur, amount in prices:
        key = (cur, amount)
        if key not in seen:
            seen.add(key)
            prices_out.append({"amount": amount, "currency": cur})
        if len(prices_out) >= 10:
            break
    issues = []
    if not ex.tables:
        issues.append("缺参数表")
    if not ex.jsonld:
        issues.append("无 JSON-LD 结构化数据")
    if not products or not products[0].get("aggregateRating"):
        issues.append("无评分/库存信息")
    if not ex.title or len(ex.title) > 80:
        issues.append("标题为空或过长")
    faq_scan = re.search(r"(?i)faq|frequently asked", text[:3000])
    if not faq_scan:
        issues.append("缺 FAQ 模块")
    return {
        "page": params.get("page", 1),
        "status": "ok",
        "final_url": final_url,
        "title": ex.title,
        "description": ex.description,
        "issues": issues,
        "product": product,
        "tables": ex.tables,
        "prices": prices_out,
        "headings": ex.headings,
        "images": ex.images[:30],
        "og_image": ex.og_image,
        "text": text[:60000],
        "jsonld_products": products,
    }
