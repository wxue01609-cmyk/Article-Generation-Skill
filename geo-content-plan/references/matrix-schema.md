# content_matrix.json Schema

```json
{
  "version": "1.0",
  "generated_at": "2026-11-02 18:00:00",
  "summary": {
    "total_queries": 12,
    "mapped": 10,
    "gaps": 2,
    "by_intent": {"informational": 4, "commercial": 3, "transactional": 2, "support": 1},
    "by_asset_type": {"blog": 4, "sku": 2, "landing": 1, "faq": 1, "thirdparty_review": 2}
  },
  "items": [
    {
      "asset_id": "blog-01",
      "primary_query": "how to choose an outdoor led display",
      "secondary_queries": ["outdoor led display buying guide"],
      "query_text": "how to choose an outdoor led display",
      "intent": "informational",
      "intent_label": "信息型",
      "confidence": 0.92,
      "intent_signals": ["starts with 'how to'", "no purchase modifier"],
      "needs_review": false,
      "cluster": "outdoor-led-selection",
      "funnel": "TOFU",
      "priority": "P1",
      "channel": "官网博客",
      "asset_type": "blog",
      "target_url": "/blog/how-to-choose-outdoor-led-display",
      "source_page": 1,
      "source_url": "https://example.com/products/led-p4",
      "rewrite_mode": "existing_page",
      "source_issues": ["参数不在 HTML 文字表中", "页面没有 FAQ 区块"],
      "title": "How to Choose an Outdoor LED Display: A Practical Buying Framework",
      "angle": "用亮度/像素间距/防护等级/维护方式四个维度建立判断框架",
      "outline": [
        {"h2": "Start with viewing distance and pixel pitch", "points": ["..."]},
        {"h2": "Match brightness to ambient light", "points": ["..."]}
      ],
      "key_points": ["...", "..."],
      "proof_points": ["IP65 rating from product KB", "待核验：亮度实测数据"],
      "cta": "Download the specification checklist",
      "internal_links": [{"anchor": "outdoor LED series", "target": "/products/outdoor"}],
      "word_count": 1100,
      "publish_order": 1,
      "dependencies": [],
      "risk_notes": []
    }
  ],
  "gaps": [
    {"query": "best led wall reddit", "reason": "no_asset_type", "suggestion": "启用社区问答或三方评测"}
  ],
  "clusters": [
    {"name": "outdoor-led-selection", "pillar": "blog-01", "supporting": ["blog-02", "faq-01"]}
  ]
}
```

## 字段约束
- `intent` 只能取：informational / commercial / transactional / navigational / support / community / news / local
- `funnel` 只能取：TOFU / MOFU / BOFU / Retention
- `priority` 只能取：P0 / P1 / P2
- `asset_type` 只能取启用的类型：blog / landing / sku / category / thirdparty_pr / thirdparty_review / qna / social / ecommerce / faq
- `asset_id` 正则：`^(blog|landing|sku|category|pr|review|qna|social|ecom|faq)-\d{2}$`
- `outline` 至少 3 项（sku/faq 可 2 项）；每项必须有 `h2` 与 `points`（≥1）
- `word_count`：blog 700-1500；landing 300-700；sku 150-400；category 600-1000；faq 300-600；qna 150-350；pr 400-700；social ≤150；ecommerce 200-500
- `confidence` 0-1；`<0.70` 时 `needs_review` 必须为 true
- `summary` 必须与 items/gaps 实际统计一致

## 待改造页面字段（可选，仅 sku）
- `source_page`：整数，对应 `source/index.json` 的 `page`；只能取 `status` 为 `ok` / `manual` 的页面，抓取失败的页面禁止分配
- `source_url`：该页面的 `final_url`（重定向后的真实地址）；手动粘贴的 `manual` 页面没有 URL 时留空
- `rewrite_mode`：固定 `existing_page`；仅在挂载了 `source_page` 时出现
- `source_issues`：`meta.json` 中 `issues` 的摘要数组；用于在 Brief 里列出「修正页面对 AI 不可读的问题」
- 硬约束：
  - 挂了 `source_page` 的 item，`asset_type` 必须是 `sku`
  - `target_url` 必须等于 `source_url`（保留原路径，不另造新 URL）；`manual` 页面沿用原 `target_url`
  - 多条 query 可复用同一 `source_page`；不同型号不得共用
  - 没有匹配页面时按新建 SKU 页规划，禁止虚构 `source_page`
  - 页面里的价格/评分/库存抓不到时不写进 Brief 的 `proof_points`，正文阶段写「Confirm current price at checkout」
