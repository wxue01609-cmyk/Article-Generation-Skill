---
name: geo-doc-parse
description: 文档解析回填。解析用户上传的文档（Excel / CSV / Word / PDF / TXT / Markdown），提取文本并识别内容类型，自动匹配回填平台表单字段（词包/企业资料/产品资料/字段资料）；只做提取与匹配，不改写事实。
---

# 文档解析回填（geo-doc-parse）

## 任务
解析用户上传的文档（Excel / CSV / Word / PDF / TXT / Markdown），提取文本；识别内容类型并自动匹配回填平台表单字段。只做提取与匹配，不改写事实。

## 输入
- 上传文件字节流 + 文件名（扩展名判断类型）
- 模板字段清单：topics（词包）/ task_name / company_name / industry / known_competitors / publish_media / article_language / article_length / engines / ent_kb_text / prod_kb_text

## 执行步骤
1. 按扩展名选择解析方式：
   - xlsx/csv：按单元格读，两列优先视为「名称+内容」
   - docx/doc：读段落文本
   - pdf：逐页提取文本
   - txt/md：直接读取
2. 识别内容类型：
   - **词包**：单列、每行一个关键词 → 填入 `topics`（JSON：`[{"name":"WordPack","queries":[...]}]`）
   - **企业资料**：两列（名称+内容），匹配公司介绍/资质/团队 → `ent_kb_text`
   - **产品资料**：匹配产品名/参数/卖点 → `prod_kb_text`
   - **字段资料**：含「任务名/企业/行业/竞品/媒体/语言」等关键词 → 按模板字段匹配回填
3. 输出：
```json
{
  "filename": "词包.xlsx",
  "type": "wordpack",
  "chars": 2340,
  "text": "提取的完整文本",
  "suggestions": {"topics": "[{\"name\":\"WordPack\",\"queries\":[\"…\"]}]", "company_name": "…"}
}
```

## 硬性规则
- 文本原样提取，禁止归纳、改写、补全缺失内容。
- 匹配字段必须依据文档中的明确信息；不明确就不建议（suggestions 里省略）。
- 解析失败的文档返回 `error`，不静默丢弃。
- 超出 60000 字符截断时在 `note` 里说明。
