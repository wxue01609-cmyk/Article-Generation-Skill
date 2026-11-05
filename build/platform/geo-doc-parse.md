## 平台落位
- 调用工具 `geo_parse_doc`（文件名 + base64 内容）；把返回的 `suggestions` 回填到对应输入字段（topics / ent_kb_text / prod_kb_text / company_name / industry / known_competitors 等）。
- 只做提取与匹配，不改写事实；解析失败返回 `error` 不静默丢弃。