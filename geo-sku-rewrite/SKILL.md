---
name: geo-sku-rewrite
description: SKU 商品页改造（geo-sku-rewrite）。把已有商品页改造成「AI 可引用、可直接发布」的商品详情页：输出结构化改造 JSON（product/core_answer/benefits/specs/fit/faq/购买信息/ref_links/changes），由平台渲染改后商品页、模块片段、整页模板与改前改后对比页；只填真实抓取值，禁止编造。当 SKU 需要 1:1 复刻原页只改文字、或按证据账本改造时使用。
---

# SKU 商品页改造（geo-sku-rewrite）

## 任务
把已有商品页改造成「AI 可引用、可直接发布」的商品详情页。不直接写最终 HTML，而是输出结构化改造 JSON，由平台渲染成品页、模块片段、整页模板与改前改后对比页。

## 输入
- 方案矩阵中 `asset_type=sku` 且带 `source_page` 的资产
- 抓取快照：`source/page-NN/page.txt`、`source/page-NN/meta.json`、`source/index.json`
- 证据账本：`evidence/ledger.json` + `evidence/evidence_map.json`（geo-evidence 产出；无账本时在 `notes` 说明，只写抓取可见事实）
- `product` 字段优先来自抓取 JSON-LD / 图片列表 / 参数表
- 因子库：`factor_library.json`（优先平台根目录实时库；青蛙端读系统提示词 agent.md 末尾内置的「因子库数据」块（与本地实时库同源，全阶段可读）；本地无独立文件时直接读平台根目录实时库，禁止自造因子定义），取 `stage=pdp` 的转化层因子（F-P-*）与本资产 Brief `factors`；Brief/矩阵带 `factor_details` 时直接用它，不必再找文件

## AI 购物助手适配策略（借鉴 Azoma 商品数据优化 · 5C 框架）
每个 SKU 改造前先回答一个问题：**为什么 AI 购物助手（ChatGPT / Amazon Rufus / Walmart Sparky 等）不理解、不推荐这个商品**；再按「信息缺口 → 消费者购物需求 → 竞品表现」重写商品数据，目标是让 AI 准确理解 SKU：知道它适合什么人、满足什么需求、相比竞品有什么优势。优化对象覆盖商品标题、五点描述、详情描述、规格/功能/材质/尺寸/适用场景、图片及 SKU/ASIN、品牌指南、卖点与已确认的产品声明。

### 0. 购物问题集与信息缺口（先诊断）
0.0 **先读平台画像与问题集产物（`research/`）**：任务目录存在 `research/persona.json`、`research/questions.json`、`research/coverage.json` 时：
   - `shopping_questions` 直接采用 `questions.json` 的 `selected` 条目（含 `question_id` / `weight` / `stage` / `from_query`），不必重复构建；无该产物时再按下方 0.1 自行构建 5-10 条；
   - `weight=must`（P0 必答）问题必须被改后商品信息直接回答：答案落到 `core_answer` / `specs` / `faq`，并在 `changes` 对应模块带 `gap_id`（如 Q-01）；
   - `coverage.json` 的 `items` 直接作为改前判定（`state` / `hit_zones` / `missing_slots`），`state=gap/partial` 条目写进 `info_gaps`；
   - 画像（persona.json）决定 FAQ 与内容角度的优先顺序，不改变事实与证据规则；
   - 平台在成稿后会按 `changes[].gap_id` 与 FAQ 逐条核对 P0 覆盖，缺失即质检未过。
1. 构建消费者真实购物问题集（`shopping_questions`）：来源优先级为商品数据本身、市场关键词、Marketplace 数据、采样 answers/sampling.json 的问题族、公开问答（如 Reddit/论坛/帮助中心）。示例（行车记录仪）：
   - Which dash cams offer 360-degree coverage?
   - Which dash cams support four cameras?
   - Which dash cams are suitable for family vehicles?
   每个 SKU 收集 5-10 条与本品类相关的问题，标 `source`。
2. 逐条判断「当前商品信息是否足以回答」：能答标 `covered_by_page=true`；不能答的写进 `info_gaps`，说明缺口在哪个表达面（标题/五点/详情/规格/图片/SKU/ASIN）+ 具体缺什么（如「支持四路摄像头，但标题与描述未写 Four-Channel，AI 无法识别该优势」）。
3. 竞品对照（`competitor_benchmarks`）：结合平台填写的竞品，观察竞品如何呈现功能、属性与卖点，找出本品信息表达上的不足，逐一列 `our_gap` 与改法；无竞品数据时省略并注明。

### 1. 5C 评分（Agentic Shelf Score）
改造前后各评一次，输出 `agentic_shelf_score`。五个维度均 0-100：
- **C1 Completeness（完整性）**：商品 Listing 标题/描述/属性/图片/变体等必需字段完整程度。量化：已完整填写的必需商品字段数 ÷ 必需字段总数 × 100。必需字段 = brand / model / title / price / availability / image / sku / core_answer / specs / faq。
- **C2 Context（场景）**：使用人群、使用场景、消费者需求与购物问题覆盖程度。量化：商品内容有效覆盖的购物问题数 ÷ 购物问题集总数 × 100。
- **C3 Citations（引用）**：AI 回答引用商品页面的频率（是否出现在 AI 参考的信息来源中）。量化：商品页面被 AI 引用的回答数 ÷ 有效回答总数 × 100。有采样/监测数据就按实际算；无数据标 `null` 并注明「未监测」，禁止编造。
- **C4 Correctness（准确性）**：AI 对产品功能、参数、规格、适用场景的描述准确程度。量化：AI 正确描述的信息项数 ÷ 被检查信息项总数 × 100。基于本页抓取值与证据账本自查，无监测时按「页面信息自洽且与规格书/账本一致的信息项占比」估算并注明口径。
- **C5 Customer Acquisition（获客）**：SKU 被 AI 推荐频率、推荐排名及获客表现。量化：综合推荐率与排名，其中 SKU 推荐率占 60%、推荐排名占 40%（推荐率：有推荐该 SKU 的回答数 ÷ 有效回答总数；排名：推荐位序归一化，第 1 名 100、每降 1 名扣固定分直至 0）。无监测数据标 `null` 并注明。
- **综合分**：采用五项平均分 `Score = (C1+C2+C3+C4+C5) / 5`；存在 `null` 维度时只对有值维度平均并在 `note` 写明「C3/C5 未监测，未纳入总分，按实测值重算」。

### 2. 评分结果怎么指导改造（低分 → 优化动作）
- C1 完整性低 → 补充标题、描述、属性、图片、FAQ 等必填字段；标题写「品牌 + 型号 + 品类 + 关键属性」。
- C2 场景低 → 增加使用场景、适用人群、需求导向内容（good / not_good、问题式 FAQ）。
- C3 引用低 → 优化商品页信息质量与可引用结构（核心答案段、参数文字表、FAQ 原问句、Product JSON-LD），增强被 AI 引用的来源。
- C4 准确性低 → 修正商品信息，统一官网、平台与第三方产品资料口径，删除矛盾/过时表述。
- C5 获客低 → 分析竞品推荐表现，强化差异化卖点与购物问题覆盖（比竞品多覆盖的问题可先行补齐）。
- 每个优化动作必须落到本 SKU 的 `changes`（module/after/problem）里，改造后的 5C 分数重新计算写入 `after`，并在 `notes` 说明提升依据；分数只基于真实抓取值与证据账本，禁止为了高分编造字段或问题。

## 输出（唯一交付物）
`plan/sku_changes/<asset_id>.json`，合法 JSON，Schema：

```json
{
  "asset_id": "sku-01",
  "source_page": 1,
  "target_url": "https://example.com/products/xxx",
  "product": {
    "brand": "Botslab", "model": "R1",
    "title": "Botslab R1 2K Security Camera – White",
    "price": {"amount": "99.99", "currency": "USD", "evidence_id": "c-002"},
    "availability": "In stock",
    "rating": {"value": 4.5, "count": 320, "evidence_id": "c-004"},
    "image_url": "https://…/main.jpg", "sku": "BL-R1", "gtin": "可选", "asin": "可选，Amazon ASIN",
    "image_alt": "Botslab R1 security camera, 2K, white"
  },
  "core_answer": "2-3 句：是什么产品、适合谁、关键参数、边界",
  "ref_links": [{"url": "https://…", "mode": "excerpt|text", "text": "客户自定义文字/内容"}],
  "trust_badges": ["Free US shipping", "30-day returns", "1-year warranty"],
  "benefits": [{"feature": "2K resolution", "meaning": "人脸/车牌更清晰", "evidence_id": "c-001"}],
  "bullet_points": ["五点描述（可选，Amazon 场景）：每条一句，属性 + 用户价值，最多 5 条"],
  "specs": [{"name": "Resolution", "value": "2K", "evidence_id": "c-001"}],
  "fit": {"good": ["户外使用"], "not_good": ["室内仅需基础监控"]},
  "faq": [{"question": "买家在 AI 里的原问句", "answer": "直接回答", "evidence_id": "可选"}],
  "shipping_returns_warranty": "运费/时效/退货/保修一段话",
  "brand_identity": "Designed and sold by Botslab",
  "reviews_summary": "服务端可见的评分与优缺点；没有就留空字符串",
  "cta": "Buy now",
  "pending_confirmations": [{"key": "price", "claim_id": "c-002", "asset_id": "sku-01", "question": "页面未显示价格，请确认售价", "suggested_default": "", "why": "写进商品卡与 FAQ 需要"}],
  "shopping_questions": [{"question": "Which dash cams support four cameras?", "source": "marketplace_keywords|public_qa|sampling|product_data", "covered_by_page": true, "gap": "标题与描述未写明 Four-Channel，AI 无法识别该优势"}],
  "info_gaps": [{"area": "标题|五点|详情|规格|图片|SKU/ASIN", "gap": "缺什么", "action": "怎么补"}],
  "competitor_benchmarks": [{"competitor": "竞品名", "presentation": "竞品如何呈现功能/属性/卖点", "our_gap": "我们表达上的不足", "fix": "改法"}],
  "agentic_shelf_score": {"before": {"C1_completeness": 60, "C2_context": 40, "C3_citations": null, "C4_correctness": 80, "C5_acquisition": null, "total": 60, "note": "C3/C5 未监测，未纳入总分"}, "after": {"C1_completeness": 90, "C2_context": 85, "C3_citations": null, "C4_correctness": 95, "C5_acquisition": null, "total": 90, "note": "说明提升依据"}},
  "used_factors": ["F-P-001", "F-P-003", "F-P-006"],
  "factor_notes": ["本页无变体，F-P-004 不适用"],
  "notes": ["核验项只写在这里"],
  "changes": [{"module": "标题", "before": "页面原文", "after": "改后文案", "problem": "解决的问题", "evidence_id": "c-001"}]
}
```

## 因子落实（转化层 F-P-*，只决定重点，不改事实）
- 按资产 Brief `factors` 优先；Brief 没给时按模块勾选适用的 F-P-*：F-P-001 商品卡字段 → `product.*` 完整真实；F-P-002 Product JSON-LD → `schema` 的 `name`/`description` 同步；F-P-003 首屏参数 → `core_answer` + `specs` 前几条；F-P-004 变体 SKU → 页面有变体才写；F-P-005 购买路径无死链 → `cta`/`target_url` 真实可达；F-P-006 政策运费 → `shipping_returns_warranty`/`trust_badges`；F-P-007 feed 一致性 → 与 geo-pdp 交付的价格/库存/GTIN/标题一致。
- 输出顶层写 `used_factors`（实际落实的 id）与 `factor_notes`（未落实原因，如「本页无变体」「抓不到评分」）；不适用直接写明，不得为凑因子编造参数。
- 因子只决定重点写什么、按什么顺序写，不改写事实与证据规则：`evidence_id`、禁止编造、1:1 复刻等规则优先。

## 证据编号（evidence_id）
- `evidence_id` 必须存在于 `evidence/ledger.json` 且该 claim `status=verified`、`approved_for_publication=true`（优先用 `evidence/evidence_map.json` 中本资产可用的 claim 列表）。
- 改后内容引用的硬事实（价格/参数/政策/认证/评分/型号）与 `evidence_id` 一一对应；没有账本条目的一律省略该字段，**禁止编造编号**。
- 无账本（客户未提供资料、geo-evidence 已注明跳过）时：只写抓取页面可见事实，全部 `evidence_id` 省略，并在 `notes` 说明「未建账本，仅用抓取值」。

## 客户待确认（pending_confirmations，可选）
- 抓取页缺失或账本里 `needs_client_confirmation` / `blocked` 的核心事实，统一写进顶层 `pending_confirmations`（每项 `{key, claim_id, asset_id, question, suggested_default, why}`），与 geo-evidence 步骤 5 的输出 schema 一致，供平台按 key 回填。
- 页面能查到的事实不得进待确认清单；待确认项不得以「待核验 / pending」字样出现在改后正文里。

## 5C 落实到 changes
- 每个 SKU 必须输出 `shopping_questions` / `info_gaps` / `competitor_benchmarks` / `agentic_shelf_score`（before 与 after 各一次）。
- 5C 低分项的优化动作必须逐条落到 `changes`（module/after/problem），`after` 评分在改造后重新计算；无监测数据（C3/C5）标 `null` 并注明，禁止编造分数。

## 模块改造要求（每个模块对应一条 changes）
- 标题：品牌 + 型号 + 品类 + 关键属性
- 核心答案段：是什么、适合谁、关键参数、限制，2-3 句脱离页面也成立
- 概述段（answer-first，AI 可引用）：H1 下方先回答「这是什么、关键参数、价格/库存」，单句 ≤25 词；同时写入 feed `description` 与 Product JSON-LD `description`
- 卖点：删营销套话，改「属性 → 对用户的意义」；Amazon 场景可另给 `bullet_points`（最多 5 条，属性 + 用户价值）
- 参数表：真实参数，不确定不写
- 适用与不适用：good / not_good
- FAQ：4-8 条，用买家原问句，答案先给结论
- 购买信息：运费/时效/退货/保修
- Reviews：有真实数据才写
- 表述中的数字必须可追到抓取页面/证据账本（账本存在时填 `evidence_id`）；无绝对化词（best / #1 / ultimate）
- `changes` 至少 6 条；`before` 引用抓取原文（缺失写「（页面无此模块）」）

## 参考链接（精确事实 · 客户补充）
- `ref_links` 原样透传客户填写的参考链接，不核对内容、不抓取正文，最多 10 条。
- 每条两种模式，按 `mode` 渲染：`excerpt`=展示 `text` 前 100 字符，超出折叠可展开，附来源链接；`text`=以 `text` 作为蓝色文字链接，点击跳转 `url`。
- 渲染位置两处：改后详情页正文末尾（购买信息之后）+ 方案预览「事实依据」表（REF-xx 行，来源=客户补充）。

## 改后详情页形态：原页 1:1 复刻
- 以抓取到的原商品页 HTML 为基底整页复刻：布局、图片、样式、价格、评论区、页脚全部保留，只替换文字。
- 替换范围：`<title>`、meta description、og / twitter 标题与描述、页面第一个 `<h1>`、Product JSON-LD 的 `name` / `description`。
- 原页 FAQ 问答可保留原文；只有能确认更准确时才替换答案，不新增结构。
- 抓不到原页 HTML 时回退模板页，并在 manifest 标记 `pdp_replica=false`。

## 发布文案硬性规则
- 正文禁止出现：`待核验`、`pending verification`、`not shown on the source page`、`on the product page`、`before publishing`、来源标注。
- 查不到的信息直接省略，不写「待核验」占位；核验说明只放 `notes`。
- 价格有真实来源才写；抓不到价格就不给 `price` 字段（平台显示 Check current price）。
- 商品卡字段（图片/SKU/GTIN/库存/评分）只填真实抓取值；图片回退顺序：JSON-LD image → og:image → 页面图片。
- 语气是给买家看的商品文案，不是审计报告。
- 正文语言跟随 `article_language`（缺省英文；选中文时按简体/繁体输出），禁止混排其它语言。

## 完成后
- 输出一行阶段标记：`::STAGE:sku_rewrite::`
- 不在 assets 下生成 HTML，由平台渲染四件套


# 附：完整参考文档（已合并内联，无需再读外部文件）
