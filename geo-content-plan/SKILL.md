---
name: geo-content-plan
description: 海外内容建设第一阶段（策略规划）。读取 query 词包与知识库，按搜索意图逐条分类，判断每个关键词应发布在哪个渠道、生产哪类内容资产（官网博客/落地页/SKU/类目页/三方媒体/社区/FAQ/电商），输出可确认的内容矩阵 JSON 与逐项 Brief。当需要回答“这个关键词该发在哪、写什么内容”时使用。
---

# 海外内容建设规划（geo-content-plan）

## 任务
输入 query 列表 + 企业/产品知识库，输出每个 query 的意图判定、渠道落位、资产类型、优先级与内容 Brief。**只做方案，不写正文**。

## 输入
- `package.json` 的 `fields`：`topics` / `keyword_pack` / `company_name` / `industry` / `article_language` / `target_market` / `asset_types` / `asset_budget` / `article_count` / `content_goal` / `site_inventory` / `primary_cta` / `known_competitors`
- `plan/path_plan.json`（geo-path-plan 的转化路径编排，存在时直接采用；缺失且无采样时按 [references/stage-map.md](references/stage-map.md) 就地打标）
- `fields.source_urls`：用户提供的待改造页面 URL（换行或逗号分隔，最多 5 个）；`fields.source_text`：抓取失败时手动粘贴的页面正文
- `source/index.json`：抓取页面索引（`page` 序号、`status`、`final_url`、`title`、`issues`、`product`）；每个页面目录含 `page.txt`（可读正文 + 诊断）与 `meta.json`（参数表 / JSON-LD / 问题清单）
- `attachments/ent/` 企业知识库、`attachments/prod/` 产品知识库；`fields.ent_kb_text` / `prod_kb_text` 为补充文本
- `research/sampling.json` + `research/citations.json`：分层采样基线（平台已跑）与「AI 实际引用的第三方页面摘要」（标题层级 + 正文节选；可为空）
   - 运行环境若提供 `geo_sample` 工具（青蛙平台通道），可直接调用它拿 `query_stage`；本地通道由平台预先生成 `research/sampling.json`，直接读取，不要自行发起采样请求

## 输出（唯一交付物）
`plan/content_matrix.json`，严格遵循 [references/matrix-schema.md](references/matrix-schema.md)。
终端最多输出 10 行摘要，禁止把整份 JSON 打印到对话里。

## 执行步骤
1. **清洗 query**：`keyword_pack` 每行一条；`topics` 提供主题归属；按大小写/单复数/标点归一后去重，问句保留原始问法。
2. **意图分类**：逐条按 [references/intent-map.md](references/intent-map.md) 判定，必须写 `intent_signals`（词面证据）与 `confidence`。
3. **节点归属（stage）**：逐条把 query 归到三层（`ai_exposure` AI曝光 / `pdp` 商品详情页 / `conversion` 购买转化）。存在 `plan/path_plan.json` 时直接用其 `stage` / `secondary_stage`；缺失时按 [references/stage-map.md](references/stage-map.md) 就地打标（1 主节点 + 1 次节点，次节点可 null）。stage 只决定「在哪层发力」，不替代渠道落位。
4. **聚合 cluster**：同实体 + 同意图 + 同主题合并；一个 query 只能有一个 `primary_query` 归属。
5. **渠道落位**：按 [references/channel-map.md](references/channel-map.md) 的决策树选择 `channel` / `asset_type`；只允许使用 `fields.asset_types` 里启用的类型；无法落位的进 `gaps`。
6. **匹配待改造页面**：读取 `source/index.json`。当某条 query 被判为 `asset_type=sku`、且可用页面与 query 指向同一型号/品类时，按下面规则挂载改造信息：
   - item 增加 `source_page`（可用页面的 `page` 序号）、`source_url`（页面 `final_url`）、`rewrite_mode: "existing_page"`；
   - `target_url` 直接用页面 `final_url`，保留原路径，不要另造新 URL；
   - `angle` 写成「改造现有商品页」，`outline` 中加入「修正页面对 AI 不可读的问题」；
   - 把 `meta.json` 的 `issues` 摘要写入 `source_issues`（数组）；
- 多条 query 可复用同一 `source_page`；有多个商品页时按型号/品类匹配，不得张冠李戴；挂在 `pdp` 层优先；
   - 无匹配页面（或未给 URL）时按**新建 SKU 页**规划，禁止虚构 `source_page`。
6.9 **目标 URL（必填）**：每个官网类资产（blog / landing / category / faq / sku）都必须给 `target_url`：
   - sku 有匹配的 `source/index.json` 页面时用该页 `final_url`（完整 https），不得另造；
   - 其余站内资产写以 `/` 开头的相对路径（全小写、连字符分词，如 `/blog/how-to-choose-dash-cam`、`/faq/return-policy`），同一路径不得挂两个资产；
   - 任何出现在其他资产 `internal_links` 里的目标，都必须能在本矩阵找到对应的 `target_url`（否则就是死链）；
   - 三方资产写 `external:TBD`，不编造站内路径。

7. **优先级**：按购买意图强度、品牌/型号相关度、流量价值给 `P0/P1/P2`（`conversion` 层购买信号强，通常不低于 P1）。
8. **生成 Brief**：按 [references/asset-specs.md](references/asset-specs.md) 对应类型的骨架，填 `title` / `angle` / `outline` / `key_points` / `proof_points` / `cta` / `internal_links` / `word_count` / `publish_order` / `dependencies`；带 `source_page` 的 sku Brief 以「改造清单」形式写，不写改后正文。每个 item 必须带 `stage` / `secondary_stage`。
8.5 **引用内容参考**：`research/citations.json`（或 `sampling.json.citations`）存在且有 `status=ok` 条目时，把与 item `stage` **同层**的引用条目写入该 item 的 `reference_citations`（`[{title, url, domain, headings, excerpt 前 200 字}]`），并把「AI 正在引用这类结构」的可借鉴点落进 `key_points`。使用规则严格按 [references/citation-usage.md](references/citation-usage.md)：只借鉴结构与证据点，禁止照抄原文句子；官网资产不因引用内容引入竞品品牌名。
9. **自检**（必须全部通过）：
   - 字段名必须与 schema 完全一致：`asset_id`（不是 id）、`primary_query`（不是 query）、`secondary_queries`、`intent`、`stage`、`secondary_stage`、`channel`、`asset_type`；字段名写错会导致平台勾选成稿失败，写完后逐项核对。
   - `summary.total_queries == len(items) + len(gaps)`
   - 每个 `primary_query` 在 items 中唯一
   - `asset_id` 唯一，格式 `<type>-NN`（如 `blog-01`、`sku-03`）
- 每个 item 都有 `stage`；`secondary_stage != stage` 或为 null；`by_stage` 与 items 统计一致
   - 官网类资产（blog/landing/category/sku/faq）brief 中不出现竞品品牌名
   - 无编造参数；不确定的事实写 `待核验`
   - `title` 语言跟随 `article_language`（缺省英文）
   - `source_page` 只能指向 `status` 为 `ok` / `manual` 的页面；抓取失败的页面一律不得分配
   - 带 `source_page` 的 item 必须同时有 `source_url`、`rewrite_mode=existing_page`，且 `target_url` 等于 `source_url`
- 没有 `source_page` 的 sku item 不得出现 `rewrite_mode`
10. **写文件**：用 apply_patch 写入 `plan/content_matrix.json`。

## 硬性规则
- 方案阶段禁止写正文、段落草稿、完整文案；`outline` 只写小标题与要点，`key_points` 用短句。
- `asset_budget` 是资产总数上限；超预算按 P0→P2 截断，剩余 query 进 `gaps`，`reason` 写 `budget`。
- `article_count` 是可发布文章数量下限：只有文章类资产（blog / landing / category / pr / review / community / social / listing / faq）计入文章数，SKU 改造不计；规划时先保证文章类资产数 ≥ `article_count`（不足时把低价值非文章 query 改落为文章类；启用类型中没有文章类可用的，在 `risk_notes` 说明），再在预算内补其它资产。
- 对比/替代/review 类只允许落三方媒体；官网只能写类别级判断标准，不点名竞品。
- query 含问号或疑问词时，原问句必须进入对应 Brief 的 `query_text` 或 FAQ 问题列表。
- 给了 URL 不等于必须改造：只有页面与 query 的产品/型号匹配时才挂 `source_page`；不匹配就在 `risk_notes` 说明并放弃使用该页面。
- JSON 必须闭合、可被 `json.load` 解析；不要用 markdown 代码块包裹，不要写注释。
- 不输出正文样例，不生成 HTML。
