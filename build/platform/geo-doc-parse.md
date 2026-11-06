## 平台落位
- 平台会把上传附件解析成 `ent_kb_text` / `prod_kb_text` 文本传给本 Agent，通常不再需要调用本技能。
- 只有任务直接携带原始文档（文件名 + base64 或文档正文）且 kb 文本为空时，才调用工具 `geo_parse_doc`；把返回的 `suggestions` 回填到对应输入字段（topics / ent_kb_text / prod_kb_text / company_name / industry / known_competitors 等）。
- 只做提取与匹配，不改写事实；解析失败返回 `error` 不静默丢弃。