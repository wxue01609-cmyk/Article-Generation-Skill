# 渠道落位决策树

## 资产类型与渠道
| asset_type | 渠道 | 适用意图 | 说明 |
|---|---|---|---|
| blog | 官网博客 | informational / commercial（类别级） | 长期资产，AI 引用权重高；禁竞品点名 |
| category | 官网类目页 | commercial（品类大词）/ informational（types of） | 品类导航 + 选购标准 + 自家产品对比 |
| landing | 官网落地页 | transactional（非品牌）/ commercial（方案型） | 单一转化目标，Hero + 证据 + CTA |
| sku | 官网产品/SKU 页 | navigational / transactional（品牌+型号） | 结构化参数、卖点、兼容、FAQ |
| faq | 帮助中心/FAQ | support / informational（短问句） | 直答 40-60 词 + 步骤 + schema |
| thirdparty_pr | 三方媒体/PR | news / commercial（行业观察） | 新闻稿/客座；品牌作案例，不吹嘘 |
| thirdparty_review | 三方评测/对比 | commercial / community | 只允许三方；必须披露关系；可点名竞品 |
| qna | 社区问答 | community | 问题式标题、0 链接、披露身份 |
| social | 社交平台 | news / 认知 | 短帖/线程，不承担排名 |
| ecommerce | 电商 Listing | transactional（平台内） | 标题/五点/描述/后台词/A+ 模块 |

## 决策树（逐条 query 执行）
1. 含品牌/型号 + 购买/价格/规格 → `sku`
2. 含 support 信号（install/troubleshoot/error/warranty/compatible）→ `faq`
3. 含 vs / alternatives / best / review / compare：
   - 若启用 `thirdparty_review` → `thirdparty_review`
   - 否则 → `blog`（只写类别级判断标准，不点名竞品），并在 `risk_notes` 注明“缺三方对比位”
4. 含 news 信号（launch/release/award/partnership）→ `thirdparty_pr`（未启用则 `blog` 新闻解读）
5. 含社区信号（reddit/forum/experience/legit）→ `qna`
6. 含 near me / 城市 + 服务 → `landing`（本地落地页；market 不覆盖则 gap）
7. 纯品类大词 / types of / how to choose → `category`（有类目页）或 `blog`（无类目页）
8. 其余 how/what/why/guide → `blog`
9. 交易型但无品牌、且启用 `landing` → `landing`；启用 `ecommerce` 且是平台内词 → `ecommerce`
10. 仍无法落位 → `gaps`

## 优先级
- `P0`：品牌/型号 + 交易意图；高商业价值的 comparison；核心品类大词；已有转化页缺失
- `P1`：品类教育、主要 informational 词、关键 support 词
- `P2`：长尾、低量、纯认知、可延后
- 同 cluster 内：pillar 先于 supporting；有内链依赖的按 `publish_order` 排序

## Cluster 与去重
- 同实体 + 同意图 + 同主题 → 一个 cluster；选搜索需求最宽的一条做 pillar，其余做 supporting。
- 一个 query 只能有一个 primary asset；其他资产可在 `secondary_queries` 中承接，但不得同标题、同角度。
- 若两个 query 语义等价（单复数/拼写/词序），合并为一条，另一个写入 `secondary_queries`。

## 渠道硬约束
- 官网 blog/landing/category/sku/faq：禁止竞品品牌名、竞品对比表、A vs B。
- 三方评测/对比：必须写披露声明；不得虚构测试；结论按“不同需求→不同方案”。
- 社区 qna：0 链接、0 促销、披露品牌关系；标题必须是真实问题口吻。
- PR：倒金字塔、5W、引语、Boilerplate；不写促销码。
- 电商：标题 ≤200 字符、5 条 bullet、后台关键词不堆砌。

## target_url 规则
- 官网类资产（blog/landing/category/sku/faq）：给站内相对路径，如 `/blog/xxx`；`site_inventory` 中有对应页面时直接复用。
- 三方类资产（thirdparty_pr / thirdparty_review / qna / social / ecommerce）：目标不是自有站点，`target_url` 必须写 `external:TBD`，并可用 `risk_notes` 说明建议媒体/平台；禁止编造第三方 URL。
