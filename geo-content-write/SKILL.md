---
name: geo-content-write
description: 海外内容建设第二阶段（成稿）。读取 plan/content_matrix.json 的资产 Brief，按资产类型（官网博客/落地页/SKU/类目页/三方PR/三方评测/社区问答/社交/电商Listing/帮助中心FAQ）生成英文成稿：普通资产输出完整可发布 HTML（assets/<type>/<id>.html），SKU 改造资产输出改造 JSON，由平台渲染成品页、模块片段、整页模板与改前改后对比页。当需要把已确认的内容矩阵写成可发布内容资产时使用。
---

# 海外内容建设成稿（geo-content-write）

## 任务
读取 `plan/content_matrix.json`，只生成任务指定 `selected_asset_ids` 中的资产成稿。每个资产是独立完整内容，直接面向发布。

## 输入
- `plan/content_matrix.json`：资产 Brief（title/angle/outline/key_points/proof_points/cta/internal_links/word_count）
- 矩阵 item 的 `stage` / `secondary_stage`：决定资产归到哪一层（`ai_exposure` / `pdp` / `conversion`）
- `selected_stages`（可选）：只跑指定层，缺省三层全跑；用于「改一层只重跑一层」
- `package.json` 的 `fields`：article_language / target_market / primary_cta / company_name / industry
- `attachments/ent`、`attachments/prod` 知识库；`fields.ent_kb_text` / `prod_kb_text` 补充文本
- 若存在 `site_inventory`：已知 URL 只能用于 internal_links，禁止伪造站点结构
- `source/`：用户提供的待改造页面（`index.json` + `page-NN/page.html` / `page.txt` / `meta.json`），仅带 `source_page` 的 sku 资产使用
- 矩阵 item 的 `reference_citations`：AI 实际引用的同层页面摘要（结构/证据参考，禁止照抄原文句子；官网资产不由此引入竞品品牌名）

## 执行步骤
1. 读取矩阵，筛选 `selected_asset_ids`；无该字段时生成全部 item。**再按 `selected_stages` 过滤**：只保留 `stage` 命中的 item（其 `secondary_stage` 不另起资产，只在该资产正文里带一句 + 内链）。
2. **先分流**：`asset_type=sku` 且 item 带 `source_page`（或 `rewrite_mode=existing_page`）的资产，**不写 HTML**，按 [references/source-rewrite.md](references/source-rewrite.md) 输出结构化改造 JSON；其余资产按下一条走普通成稿。
3. 每个资产按 [references/asset-specs.md](references/asset-specs.md) 的类型模板成稿，严格遵守 brief：
   - 标题、角度、H 结构、要点顺序、CTA、内链锚文本不得偏离 brief；确需调整时在 `asset_index.json` 的 `checks` 里说明。
   - `word_count` ±20% 内；FAQ 问题保留原问句。
4. 事实铁律：只能来自知识库/brief；普通资产 brief 中 `待核验` 内容照写并保留标注；SKU 改造资产按 [references/source-rewrite.md](references/source-rewrite.md) 的发布规则，正文不写 `待核验`，查不到就省略；禁止编造参数、价格、案例、客户。
5. 品牌/渠道规则：
   - 官网资产（blog/landing/category/sku/faq）：不出现任何竞品品牌名、竞品对比表、A vs B。
   - 三方评测/对比：必须含披露声明，结论按“不同需求→不同方案”。
   - 社区问答：0 链接、0 促销、口语化、结尾真实问题。
6. 输出文件（普通资产唯一交付物是 HTML，不是 Markdown）：
   - 每个资产写 `assets/<asset_type>/<asset_id>.html`：完整可发布页面，必须包含 `<!doctype html>`、`<html>`、`<head><meta charset><meta name="viewport"><title><style>…</style></head>`、`<body>`。
   - 样式全部内联在 `<style>` 中，禁止外链 CSS/JS/字体；响应式，移动端可读；正文用语义化 `h1/h2/p/ul/ol/table/blockquote`，CTA 用可见按钮样式。
   - 不要用 ```html 代码块包裹；不要只输出 Markdown。可另写同名 `.md` 作为内部底稿，但不得作为交付物。
   - `asset_index.json` 的 `file` 字段必须指向 `.html`；全部完成后写 `assets/asset_index.json`：`[{asset_id, asset_type, stage, title, file, word_count, checks: []}]`。
   - **合并写，不整份覆盖**：已有 `asset_index.json` 时，同 `asset_id` 覆盖、其它层条目原样保留，写前按 `stage` 排序；这样只重跑一层不会丢其它层。
   - 另写 `assets/stage_index.json`（每次整份重写，只统计磁盘上真实存在的产物）：`{"ai_exposure": {"count": 3, "assets": ["blog-01", ...]}, "pdp": {...}, "conversion": {...}}`。
   - **发布提示（强制）**：若本资产的 `target_url` 是站内相对路径（以 `/` 开头），必须在 `<body>` 内第一行插入一段中文高亮提示，说明「本文档需发布到官网路径 `<target_url>`，否则引用本文的其他文章内链会失效，发布前请删除本提示」。这段提示属于运营标注、不属于正文，用 `<!-- GEO-PUBLISH-NOTE -->` 标记包裹，样式内联（浅黄底 + 橙色边框），并注明发布前删除；`target_url` 为空时改为红色提示「尚未指定发布路径，若被内链引用需先补路径」；`target_url` 为 `http(s)://` 或 `external:TBD` 时不加提示。
   - **CTA 链接（强制，禁止自链）**：CTA 按钮的 `href` 只能取 `brief.cta_url`（真实地址）。**严禁**把 `href` 写成本资产自己的 `target_url`——自链点击必然 404，是最常见的线上事故。
     - `cta_url` 为真实 `http(s)://`：正常渲染 `<a class="cta" href="…" target="_blank" rel="noopener">…</a>`；
     - `cta_url` 为空或为 `待填真实链接`：渲染成占位按钮 `<a class="cta cta-pending" href="#" data-pending-link="1">…</a>`（样式用虚边框 + 灰色底），并在按钮上方插入一行中文高亮提示「⚠️ 待填真实链接：请把 CTA 换成官网真实落地页后删除本提示」，用 `<!-- GEO-CTA-NOTE -->` 标记包裹，发布前删除；
     - 顶部导航、页脚链接同理：只能写 `site_inventory` 中的真实 URL；矩阵里尚未发布的规划路径不得进入导航/页脚。
   - 交付包按层分组出清单：`packs/<stage>/manifest.json`（`{stage, assets:[{asset_id, asset_type, file, title}]}`），文件仍留在 `assets/<asset_type>/`，不搬家（平台按 `asset_index.json` 的 `file` 取文件）。规则见 [references/stage-packaging.md](references/stage-packaging.md)。
7. **SKU 改造资产**：每个写 `plan/sku_changes/<asset_id>.json`（合法 JSON，不要 Markdown 代码块），由平台渲染成四类成品：改后商品页 `assets/sku/<id>.html`、模块片段 `assets/sku/<id>-modules.html`（带 `{{...}}` 数据占位符，可直接粘贴进商品页后台）、整页模板 `assets/sku/<id>-template.html`（站点壳 + 占位符，接商品系统后发布）、改前改后对比页 `assets/sku/<id>-before-after.html`；不要在 `assets/sku/` 下重复写这些 SKU 的 HTML，`asset_index.json` 由平台补录。改后正文必须可直接发布：不得出现「待核验 / pending verification / 来源备注」等审核语，查不到的信息直接省略，核验项只写 `notes` 或 `changes`。feed/JSON-LD 等商品数据交付属于 `geo-pdp`：它只写 `plan/sku_deliverables/<asset_id>/` 目录，不碰这里的 `<asset_id>.json`。
8. 每个资产独立完整、禁止截断；写完后输出 `::STAGE:polish::` 与一行 `asset_index.json` 路径；有 SKU 改造资产时额外输出 `::STAGE:sku_rewrite::`。
9. **质检与回流**：内容建设成稿必须走 geo-polish 的「全链路质检」模式（见 `geo-polish`），产出 `polish_report.json`；blocking 项清零后再交 `geo-diagnose` 做回流比对，规则见 [references/reflow.md](references/reflow.md)。

## 质量标准（每篇自检）
- 标题/首屏/结论都出现主推品牌与核心卖点（第三方内容除外）。
- 没有绝对化营销词（best/#1/revolutionary/ultimate/世界第一等）。
- 参数口径全文一致；普通资产未核验项带标注（SKU 改造资产按发布规则省略，不写进正文）。
- 链接只使用可核验真实 URL；无一键堆链，内链锚文本具名；CTA/导航不得链接到本资产自身 `target_url`，无真实地址时用占位按钮 + 中文提示。
- 站外链接（CTA 按钮、商品页、政策页、来源）一律写成 `<a href="…" target="_blank" rel="noopener">`，避免成稿在预览 iframe 里被目标站点以 X-Frame-Options 拒绝嵌入；站内内链保持默认 target。
- 语言全部为 `article_language`（缺省英文）；不出现中文正文。
- 字数达标；FAQ 原问句保留。新建 SKU 页（无 `source_page`）：正文（不含导航/页脚/规格表）按 brief 的 `word_count` ±20%，建议 ≤400 词；不要写成 700+ 词的落地页。字数超限视为未达标，写完后回读 brief 核对。
- HTML 完整闭合，浏览器直接打开即可发布；无外链依赖、无 Markdown 残留（`**`、`| 表格 |` 等）。
- 改造类 SKU：`changes` ≥6 条，`before` 必须引用抓取原文（缺失写“（页面无此模块）”），`after` 为实际改后文案，`problem` 说明解决的问题；参数表不得出现“待核验”行。
- 带 `reference_citations` 的资产：正文可借鉴其标题层级组织与证据点类型（让文章更贴近 AI 正在引用的形态），但任何句子、列表、段落不得照搬引用页原文；与知识库冲突时以知识库为准。

## 输出控制
- 内部推理 ≤6000 token，直接写作，不写草稿再改。
- 接近输出上限时先收尾闭合当前资产，保证每个文件完整。
