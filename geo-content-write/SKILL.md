---
name: geo-content-write
description: 海外内容建设第二阶段（成稿）。读取 plan/content_matrix.json 的资产 Brief，按资产类型（官网博客/落地页/SKU/类目页/三方PR/三方评测/社区问答/社交/电商Listing/帮助中心FAQ）生成英文成稿，输出可直接发布的完整 HTML：assets/<type>/<id>.html。当需要把已确认的内容矩阵写成可发布内容资产时使用。
---

# 海外内容建设成稿（geo-content-write）

## 任务
读取 `plan/content_matrix.json`，只生成任务指定 `selected_asset_ids` 中的资产成稿。每个资产是独立完整内容，直接面向发布。

## 输入
- `plan/content_matrix.json`：资产 Brief（title/angle/outline/key_points/proof_points/cta/internal_links/word_count）
- `package.json` 的 `fields`：article_language / target_market / primary_cta / company_name / industry
- `attachments/ent`、`attachments/prod` 知识库；`fields.ent_kb_text` / `prod_kb_text` 补充文本
- 若存在 `site_inventory`：已知 URL 只能用于 internal_links，禁止伪造站点结构
- `source/`：用户提供的待改造页面（`index.json` + `page-NN/page.html` / `page.txt` / `meta.json`），仅带 `source_page` 的 sku 资产使用

## 执行步骤
1. 读取矩阵，筛选 `selected_asset_ids`；无该字段时生成全部 item。
2. **先分流**：`asset_type=sku` 且 item 带 `source_page`（或 `rewrite_mode=existing_page`）的资产，**不写 HTML**，按 [references/source-rewrite.md](references/source-rewrite.md) 输出结构化改造 JSON；其余资产按下一条走普通成稿。
3. 每个资产按 [references/asset-specs.md](references/asset-specs.md) 的类型模板成稿，严格遵守 brief：
   - 标题、角度、H 结构、要点顺序、CTA、内链锚文本不得偏离 brief；确需调整时在 `asset_index.json` 的 `checks` 里说明。
   - `word_count` ±20% 内；FAQ 问题保留原问句。
4. 事实铁律：只能来自知识库/brief；brief 中 `待核验` 内容照写并保留标注；禁止编造参数、价格、案例、客户。
5. 品牌/渠道规则：
   - 官网资产（blog/landing/category/sku/faq）：不出现任何竞品品牌名、竞品对比表、A vs B。
   - 三方评测/对比：必须含披露声明，结论按“不同需求→不同方案”。
   - 社区问答：0 链接、0 促销、口语化、结尾真实问题。
6. 输出文件（普通资产唯一交付物是 HTML，不是 Markdown）：
   - 每个资产写 `assets/<asset_type>/<asset_id>.html`：完整可发布页面，必须包含 `<!doctype html>`、`<html>`、`<head><meta charset><meta name="viewport"><title><style>…</style></head>`、`<body>`。
   - 样式全部内联在 `<style>` 中，禁止外链 CSS/JS/字体；响应式，移动端可读；正文用语义化 `h1/h2/p/ul/ol/table/blockquote`，CTA 用可见按钮样式。
   - 不要用 ```html 代码块包裹；不要只输出 Markdown。可另写同名 `.md` 作为内部底稿，但不得作为交付物。
   - `asset_index.json` 的 `file` 字段必须指向 `.html`；全部完成后写 `assets/asset_index.json`：`[{asset_id, asset_type, title, file, word_count, checks: []}]`。
7. **SKU 改造资产**：每个写 `plan/sku_changes/<asset_id>.json`（合法 JSON，不要 Markdown 代码块），由平台渲染成四类成品：改后商品页 `assets/sku/<id>.html`、模块片段 `assets/sku/<id>-modules.html`（带 `{{...}}` 数据占位符，可直接粘贴进商品页后台）、整页模板 `assets/sku/<id>-template.html`（站点壳 + 占位符，接商品系统后发布）、改前改后对比页 `assets/sku/<id>-before-after.html`；不要在 `assets/sku/` 下重复写这些 SKU 的 HTML，`asset_index.json` 由平台补录。改后正文必须可直接发布：不得出现「待核验 / pending verification / 来源备注」等审核语，查不到的信息直接省略，核验项只写 `notes` 或 `changes`。
8. 每个资产独立完整、禁止截断；写完后输出 `::STAGE:polish::` 与一行 `asset_index.json` 路径；有 SKU 改造资产时额外输出 `::STAGE:sku_rewrite::`。

## 质量标准（每篇自检）
- 标题/首屏/结论都出现主推品牌与核心卖点（第三方内容除外）。
- 没有绝对化营销词（best/#1/revolutionary/ultimate/世界第一等）。
- 参数口径全文一致；未核验项带标注。
- 链接只使用可核验真实 URL；无一键堆链，内链锚文本具名。
- 语言全部为 `article_language`（缺省英文）；不出现中文正文。
- 字数达标；FAQ 原问句保留。
- HTML 完整闭合，浏览器直接打开即可发布；无外链依赖、无 Markdown 残留（`**`、`| 表格 |` 等）。
- 改造类 SKU：`changes` ≥6 条，`before` 必须引用抓取原文（缺失写“（页面无此模块）”），`after` 为实际改后文案，`problem` 说明解决的问题；参数表不得出现“待核验”行。

## 输出控制
- 内部推理 ≤6000 token，直接写作，不写草稿再改。
- 接近输出上限时先收尾闭合当前资产，保证每个文件完整。
