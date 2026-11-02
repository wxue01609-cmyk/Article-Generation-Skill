# SKU 页面改造（基于已有商品页）

适用：矩阵 item 满足 `asset_type=sku` 且带 `source_page`（用户提供了待改造商品页 URL）的资产。
此时**不直接写资产 HTML**，改为输出结构化的「改造 JSON」，由平台渲染成两类成品：
- 可发布的改后商品详情页 `assets/sku/<id>.html`
- 改前/改后对比页 `assets/sku/<id>-before-after.html`（切换按钮 + 绿色改动标注 + 逐项依据表）

## 输入
- `source/index.json`：页面索引（`page` 序号、`status`、`title`、`description`、`issues`、`product`）
- `source/page-NN/page.txt`：抓取正文（含「页面诊断」头）
- `source/page-NN/meta.json`：`tables`（HTML 参数表）、`jsonld_products`、`issues`、`prices`、`headings`
- 矩阵 item 的 `source_url` / `title` / `angle` / `primary_query` / `source_issues`

## 执行要求（目标：被 AI 商品卡 / 购物结果引用）
1. 读取 `source_page` 对应页面；改前内容一律以抓取快照为准，禁止脑补原页面。
2. 按以下模块改造，每个模块都对应一条 `changes`：
   - 标题：品牌 + 型号 + 品类 + 关键属性（材质/容量/供电/颜色），让属性型问题能匹配到；
   - 核心答案段：是什么、适合谁、关键参数、限制，2-3 句，脱离页面也能成立；
   - 卖点：删掉营销套话（premium / best-in-class / ultimate 等），改「属性 → 对用户的意义」；
   - 参数表：把页面里（图片/JSON-LD/正文）的参数写成 name/value；不确定的参数**不要写进 specs**（禁止“待核验”行）；
   - 适用与不适用：good / not_good 各列清楚；
   - FAQ：用买家在 AI 里问的原问句（问题族），至少 4 条；
   - 购买信息：运费/时效、退货、保修写清楚；
   - 品牌方身份：`Designed and sold by <brand>`；
   - Reviews：评分/数量/高频优缺点必须服务端可见，没有真实数据则不写。
3. 事实只能来自抓取页面与知识库；价格/评分/库存抓不到就留空，正文写 `Confirm current price at checkout`；**禁止发明**。
4. `changes` 至少 6 条：`before` 引用抓取到的原文（可节选，缺失写“（页面无此模块）”），`after` 写改后实际文案，`problem` 说明解决的问题。

## 输出（唯一交付物）
`plan/sku_changes/<asset_id>.json`（合法 JSON，不要 Markdown 代码块）。Schema：

```json
{
  "asset_id": "sku-01",
  "source_page": 1,
  "target_url": "https://example.com/products/botslab-r1",
  "product": {
    "brand": "Botslab",
    "model": "R1",
    "title": "Botslab R1 2K Security Camera with 90-Day Battery – White",
    "price": {"amount": "99.99", "currency": "USD"},
    "availability": "In stock",
    "rating": {"value": 4.5, "count": 320, "source": "评分来源"},
    "gtin": "可选，命中才写",
    "image_alt": "Botslab R1 security camera, 2K, 90-day battery, white"
  },
  "core_answer": "2-3 句：是什么产品、适合谁、关键参数、边界。脱离页面单独成立。",
  "trust_badges": ["Free US shipping", "30-day returns", "1-year warranty"],
  "benefits": [
    {"feature": "2K resolution", "meaning": "清晰度更高，人脸/车牌更易辨认"}
  ],
  "specs": [{"name": "Resolution", "value": "2K"}],
  "fit": {"good": ["适合的场景/人群"], "not_good": ["不适合的场景/人群"]},
  "faq": [
    {"question": "买家在 AI 里问的原问句", "answer": "直接回答"}
  ],
  "shipping_returns_warranty": "运费/时效/退货/保修一段话。",
  "brand_identity": "Designed and sold by Botslab",
  "reviews_summary": "服务端可见的评分与高频优缺点；没有就留空字符串",
  "cta": "Buy now",
  "changes": [
    {"module": "标题", "before": "抓到的原标题原文", "after": "改后标题", "problem": "解决的问题"}
  ]
}
```

## 完成后
- 输出一行阶段标记：`::STAGE:sku_rewrite::`。
- 不写 `assets/sku/<id>.html`（平台会渲染）；`assets/asset_index.json` 里该资产由平台补录。
