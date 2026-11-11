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
- 因子库：`factor_library.json`（优先平台根目录实时库；skill 内 `assets/factor_library.json` 兜底），取 `stage=pdp` 的转化层因子（F-P-*）与本资产 Brief `factors`

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
    "image_url": "https://…/main.jpg", "sku": "BL-R1", "gtin": "可选",
    "image_alt": "Botslab R1 security camera, 2K, white"
  },
  "core_answer": "2-3 句：是什么产品、适合谁、关键参数、边界",
  "ref_links": [{"url": "https://…", "mode": "excerpt|text", "text": "客户自定义文字/内容"}],
  "trust_badges": ["Free US shipping", "30-day returns", "1-year warranty"],
  "benefits": [{"feature": "2K resolution", "meaning": "人脸/车牌更清晰", "evidence_id": "c-001"}],
  "specs": [{"name": "Resolution", "value": "2K", "evidence_id": "c-001"}],
  "fit": {"good": ["户外使用"], "not_good": ["室内仅需基础监控"]},
  "faq": [{"question": "买家在 AI 里的原问句", "answer": "直接回答", "evidence_id": "可选"}],
  "shipping_returns_warranty": "运费/时效/退货/保修一段话",
  "brand_identity": "Designed and sold by Botslab",
  "reviews_summary": "服务端可见的评分与优缺点；没有就留空字符串",
  "cta": "Buy now",
  "pending_confirmations": [{"key": "price", "claim_id": "c-002", "asset_id": "sku-01", "question": "页面未显示价格，请确认售价", "suggested_default": "", "why": "写进商品卡与 FAQ 需要"}],
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

## 模块改造要求（每个模块对应一条 changes）
- 标题：品牌 + 型号 + 品类 + 关键属性
- 核心答案段：是什么、适合谁、关键参数、限制，2-3 句脱离页面也成立
- 概述段（answer-first，AI 可引用）：H1 下方先回答「这是什么、关键参数、价格/库存」，单句 ≤25 词；同时写入 feed `description` 与 Product JSON-LD `description`
- 卖点：删营销套话，改「属性 → 对用户的意义」
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
- 正文语言跟随 `article_language`，禁止混入中文。

## 完成后
- 输出一行阶段标记：`::STAGE:sku_rewrite::`
- 不在 assets 下生成 HTML，由平台渲染四件套


# 附：完整参考文档（已合并内联，无需再读外部文件）
