## 平台落位
- 普通资产输出进 `assets`：`{asset_id, asset_type, channel, title, html, word_count}`；html 必须是完整可发布页面（含 `<!doctype html>`、内联 style、语义化标签），禁止 Markdown 代码块包裹。
- SKU 资产不写 HTML：按 `geo-sku-rewrite` 输出 `sku_changes`（Python 的 `geo_render_html` 渲染模块片段与改前改后页），不要输出 assets/sku/*.html。
- 带 `selected_stages` 时只生成指定层资产；全部生成后输出 `stage_index`（ai_exposure/pdp/conversion → assets 列表）。
- 正文/模块/模板里指向站外的链接一律 `target="_blank" rel="noopener"`；正文语言用 article_language，禁止审核语/占位符进正文。