# -*- coding: utf-8 -*-
"""文档解析工具：解析 xlsx/docx/pdf/txt/csv/md，提取纯文本并按模板字段给出回填建议。
只做提取与匹配，不改写原文事实；解析失败返回 error，不静默丢弃。"""
import base64
import io
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET

MAX_CHARS = 60000
NS_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS_S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

FIELD_HINTS = {
    "company_name": ["公司名称", "企业名称", "公司", "企业", "company", "brand", "品牌"],
    "industry": ["行业", "领域", "industry", "赛道"],
    "known_competitors": ["竞品", "竞争对手", "competitor", "对手"],
    "publish_media": ["发布媒体", "媒体", "渠道", "publish", "platform"],
    "article_language": ["语言", "language"],
    "article_length": ["篇幅", "字数", "length"],
    "engines": ["ai 平台", "ai平台", "目标平台", "引擎", "engine", "chatgpt", "gemini", "perplexity"],
    "task_name": ["任务名", "任务名称", "task"],
}


def _decode_file(params):
    raw_b64 = params.get("content_base64") or params.get("file_base64") or ""
    path = params.get("file_path") or params.get("path") or ""
    if raw_b64:
        data = base64.b64decode(raw_b64.split(",")[-1])
        name = params.get("filename") or params.get("file_name") or "upload.bin"
        return name, data
    if path and os.path.isfile(path):
        return os.path.basename(path), open(path, "rb").read()
    return "", b""


def _docx_text(data):
    out = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    for p in root.iter(NS_W + "p"):
        txt = "".join(t.text or "" for t in p.iter(NS_W + "t")).strip()
        if txt:
            out.append(txt)
    return "\n".join(out)


def _xlsx_text(data):
    out = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            sroot = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in sroot.iter(NS_S + "si"):
                shared.append("".join(t.text or "" for t in si.iter(NS_S + "t")))
        sheets = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet")]
        for sheet in sorted(sheets):
            root = ET.fromstring(z.read(sheet))
            out.append("[工作表] %s" % os.path.basename(sheet))
            for row in root.iter(NS_S + "row"):
                cells = []
                for c in row.iter(NS_S + "c"):
                    ctype = c.get("t") or ""
                    val = ""
                    if ctype == "inlineStr":
                        is_node = c.find(NS_S + "is")
                        if is_node is not None:
                            val = "".join(t.text or "" for t in is_node.iter(NS_S + "t"))
                    else:
                        v = c.find(NS_S + "v")
                        val = v.text if v is not None and v.text is not None else ""
                        if ctype == "s" and val.isdigit():
                            idx = int(val)
                            val = shared[idx] if idx < len(shared) else val
                    if val.strip():
                        cells.append(val.strip())
                if cells:
                    out.append("\t".join(cells))
    return "\n".join(out)


def _pdf_text(data):
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((pg.extract_text() or "") for pg in reader.pages)
    except Exception:
        pass
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        return "\n".join((pg.extract_text() or "") for pg in reader.pages)
    except Exception as e:
        raise RuntimeError("当前运行环境缺少 PDF 解析库（pypdf/PyPDF2）：%s" % e)


def _guess_fields(text):
    if not text:
        return {}
    sug = {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines[:200]:
        for field, hints in FIELD_HINTS.items():
            if field in sug:
                continue
            for h in hints:
                if h.lower() in ln.lower():
                    parts = re.split(r"[:：\t]", ln, maxsplit=1)
                    if len(parts) == 2 and parts[1].strip():
                        sug[field] = parts[1].strip()[:300]
                    break
    queries = []
    for ln in lines:
        if ln.startswith("[工作表]"):
            continue
        if 2 <= len(ln) <= 120 and not re.search(r"[:：\t]", ln) and not ln.startswith("#"):
            queries.append(ln)
        if len(queries) >= 200:
            break
    if queries:
        sug["topics"] = json.dumps([{"name": "WordPack", "queries": queries}], ensure_ascii=False)
    return sug


def run(params):
    filename, data = _decode_file(params)
    text_in = params.get("text") or ""
    if not data and not text_in:
        return {"status": "failed", "error": "缺少文件内容：content_base64 / file_path / text 至少提供一个"}
    ext = os.path.splitext(filename)[1].lower()
    note = ""
    try:
        if data:
            if ext in (".xlsx", ".xlsm"):
                text = _xlsx_text(data)
            elif ext == ".docx":
                text = _docx_text(data)
            elif ext == ".pdf":
                text = _pdf_text(data)
            elif ext in (".txt", ".md", ".csv", ".tsv", ""):
                for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
                    try:
                        text = data.decode(enc)
                        break
                    except Exception:
                        text = ""
            else:
                return {"status": "failed", "error": "暂不支持的文件类型：%s" % ext}
        else:
            text = text_in
    except Exception as e:
        return {"status": "failed", "filename": filename, "error": "解析失败：%s" % e}
    if len(text) > MAX_CHARS:
        note = "文本超过 %d 字符已截断" % MAX_CHARS
        text = text[:MAX_CHARS]
    dtype = "wordpack" if re.search(r"(?i)关键词|query|词包", text[:2000]) else "document"
    return {
        "status": "ok",
        "filename": filename,
        "type": dtype,
        "chars": len(text),
        "text": text,
        "suggestions": _guess_fields(text),
        "note": note,
    }
