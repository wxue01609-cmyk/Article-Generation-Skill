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
3. **节点归属（stage）**：逐条把 query 归到三层（`ai_exposure` AI曝光 / `pdp` 转化层 / `conversion` 对比决策）。存在 `plan/path_plan.json` 时直接用其 `stage` / `secondary_stage`；缺失时按 [references/stage-map.md](references/stage-map.md) 就地打标（1 主节点 + 1 次节点，次节点可 null）。stage 只决定「在哪层发力」，不替代渠道落位。
4. **聚合 cluster**：同实体 + 同意图 + 同主题合并；一个 query 只能有一个 `primary_query` 归属。
5. **渠道落位**：按 [references/channel-map.md](references/channel-map.md) 的决策树选择 `channel` / `asset_type`；只允许使用 `fields.asset_types` 里启用的类型；无法落位的进 `gaps`。
5.5 **因子库（决定 Brief 的重点与排序）**：读取 `factor_library.json`（优先平台根目录实时库；skill 内 `assets/factor_library.json` 为 v1 草案兜底）。
   - 每个资产按 `stage` 选 2-4 个重点因子：全局因子（`category=global`）+ 本层因子（`category=stage` 且 `stage` 匹配），写入 item 的 `factors`（因子 id 数组）。
   - 按所选因子的 `action` 写 `authority_actions`（权威建设动作，字符串数组），并让 `key_points` 能逐条对应到所选因子。
   - 因子只决定“重点写什么、按什么顺序写”，不改写事实与证据规则；自定义因子权重只影响排序，不改变判定逻辑。
   - 若运行中发现新规律或需调整既有因子（权重/检查口径/适用资产），追加写 `plan/factor_updates.json`；平台在任务收尾时自动合并入库并标“新增”，方案或成稿引用后自动取消标注。没有新规律不要生成该文件。
- 若 `item.factors` 引用了库中不存在的因子名，必须把该名称也写进 `plan/factor_updates.json`（`action=add`，`name` 用该名称，`category`/`stage` 按资产层级填），平台会自动建条目并标“新增”；`item.factors` 只允许写库中已存在的 id 或本次 `factor_updates` 里的 name。

5.6 **本地化词库（按目标市场落地，只改说法不改事实）**：读取 `locale_profiles.json`（优先平台根目录实时库；skill 内 `assets/locale_profiles.json` 为同版本兜底）。按 `fields.target_market` 解析市场代码（美国/US、新加坡/SG、英国/UK、澳大利亚/AU、加拿大/CA，映射见 `market_aliases`）；解析不到就跳过本节。命中市场时：
   - 该市场 `terms` 里 `level=hard` 的 wrong 词禁止出现在 Brief 与后续正文，一律用 right 词（如新加坡用 MRT 不用 railway、car park 不用 parking lot；英式拼写 colour/centre）；`soft` 词条同样必须采用 right 词（soft 与 hard 同权必改）；
   - 拼写变体：整篇统一用该市场 `spelling`（en-US 或 en-GB），不许混用 color/colour、center/centre、-ize/-ise；
   - 本地习惯落到 Brief：`units` 单位、`currency` 货币、`payment` 支付方式、`logistics` 物流与售后表述、`regulatory` 监管机构、`authority_sources` 权威引用源、`calendar` 本地节点；
   - 输出语言为中文时用 `zh_terms`（新加坡中文写「德士」不写「的士/出租车」）；
   - `whitelist`（白名单词）是该市场允许出现的固定搭配或专有说法（如 `executive condominium`）：白名单短语命中时不按 wrong 词报错；备注方括号里的中文含义（如【共管公寓】）出现在成稿里、但白名单词没出现时，必须改用 `whitelist` 里的词；
   - 本地化只改说法、单位、案例与本地引用源；产品事实、参数、价格与证据规则一律保持不变。

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

6.95 **CTA 与导航链接（强制，禁止自链）**：每个 item 额外给 `cta_url`（CTA 按钮要跳转的真实地址）：
   - 优先级：`site_inventory` 里的真实页面 URL → `source_urls` 中抓取成功的真实页面 URL → 知识库/客户明确提供的 URL；
   - **禁止** `cta_url` 等于本资产自己的 `target_url`（自链点击必然 404），也禁止指向矩阵里尚未发布的规划路径；
   - 找不到真实地址时写 `待填真实链接`，并在 `risk_notes` 注明「CTA 需客户补真实落地页」；
   - 顶部导航与页脚链接同理：只能使用 `site_inventory` 中的真实 URL；矩阵内未发布的规划路径不得进入导航/页脚，最多作为正文内链锚文本；
   - `cta` 只写按钮文案（沿用 `primary_cta`，缺省 `Check it out`），URL 一律放 `cta_url`。

7. **优先级**：按购买意图强度、品牌/型号相关度、流量价值给 `P0/P1/P2`（`conversion` 层购买信号强，通常不低于 P1）。
8. **生成 Brief**：按 [references/asset-specs.md](references/asset-specs.md) 对应类型的骨架，填 `title` / `angle` / `outline` / `key_points` / `proof_points` / `cta` / `cta_url` / `internal_links` / `word_count` / `publish_order` / `dependencies`；带 `source_page` 的 sku Brief 以「改造清单」形式写，不写改后正文。每个 item 必须带 `stage` / `secondary_stage`。
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
11. **机械自检（有 python 时必须跑）**：写完矩阵后执行
    `python3 scripts/check_matrix.py --project <项目目录> --competitors "<已知竞品，逗号分隔>" --budget <asset_budget>`
    - 退出码非 0 时，按报出的 blocking 逐条修矩阵并重跑，直到 PASS；warning 记进 `risk_notes` 后放行。
    - 脚本覆盖：字段名（`asset_id`/`primary_query`）、`stage`/`secondary_stage` 合法性、`intent`/`priority`、`asset_type` 启用范围、官网类 `target_url` 必填、站内内链闭环（防死链）、`outline` 结构与条数、`word_count` 档位、`confidence<0.70` 需 `needs_review`、`source_page`/`source_url`/`rewrite_mode` 关联、`summary` 三项统计、`gaps.reason`、`asset_budget` 截断、官网资产不点名竞品。
    - 平台（青蛙）环境无 python 时，按上面的清单人工逐条核对并在 `summary` 后注明「未跑 check_matrix.py」。

## 硬性规则
- 方案阶段禁止写正文、段落草稿、完整文案；`outline` 只写小标题与要点，`key_points` 用短句。
- `asset_budget` 是资产总数上限；超预算按 P0→P2 截断，剩余 query 进 `gaps`，`reason` 写 `budget`。
- `article_count` 是可发布文章数量下限：只有文章类资产（blog / landing / category / pr / review / community / social / listing / faq）计入文章数，SKU 改造不计；规划时先保证文章类资产数 ≥ `article_count`（不足时把低价值非文章 query 改落为文章类；启用类型中没有文章类可用的，在 `risk_notes` 说明），再在预算内补其它资产。
- 对比/替代/review 类只允许落三方媒体；官网只能写类别级判断标准，不点名竞品。**官网不做任何形式的竞品对比页——包括有证据的客观对比（即使逐项参数有真实来源，也不允许在官网点名竞品）**；坚持该口径，避免官网对比内容被 AI 当作竞品对比来源。
- query 含问号或疑问词时，原问句必须进入对应 Brief 的 `query_text` 或 FAQ 问题列表。
- 给了 URL 不等于必须改造：只有页面与 query 的产品/型号匹配时才挂 `source_page`；不匹配就在 `risk_notes` 说明并放弃使用该页面。
- JSON 必须闭合、可被 `json.load` 解析；不要用 markdown 代码块包裹，不要写注释。
- 不输出正文样例，不生成 HTML。
