## 平台执行约定（青蛙平台适配，非规则；规则以「规则正文」为准）
- 本技能在青蛙平台运行：没有本地文件系统、不能执行 shell/脚本。下面规则正文中出现的 `python3 scripts/xxx.py`、`plan/xxx.json`、`assets/xxx.html`、`research/xxx.json` 等本地路径，一律理解为「按该文件的结构产出对应 JSON/内容」，不要调用脚本、不要声称已写文件。
- 最终只输出 agent.md 规定的单个 JSON 数组，技能产出放进对应输出字段（matrix / assets / sku_changes / polish_report / diagnosis / notes 等）。
- 输入字段以 agent.json 的 input_schema 为准：topics / keyword_pack / company_name / industry / target_market / article_language / asset_types / asset_budget / article_count / content_goal / site_inventory / primary_cta / known_competitors / source_urls / source_text / ent_kb_text / prod_kb_text / answers_json / samples_json / citations_json / selected_asset_ids / selected_stages / monitoring_json / plan_matrix_json / confirmed_facts_json 等。
- 可用工具：`geo_sample`、`geo_fetch_page`、`geo_parse_doc`、`geo_render_html`。需要分层采样、抓页面、解析上传文档、渲染 HTML 时，必须先调用对应工具，不能凭空生成结果。
- 字段名与最终输出格式以 agent.md 为准；与本文件冲突时，规则正文优先。