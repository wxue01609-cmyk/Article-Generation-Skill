---
name: geo-source-fetch
description: 商品页抓取解析。抓取用户提供的商品页 URL，把每个页面做成结构化快照（正文/标题层级/参数表/JSON-LD 商品字段/图片/价格/问题清单），供 SKU 改造使用；抓不到的字段一律留空，禁止编造。
---

# 商品页抓取解析（geo-source-fetch）

## 任务
抓取用户提供的商品页 URL（`source_urls`，换行或逗号分隔，最多 5 个），把每个页面做成结构化快照，供 SKU 改造使用。抓不到的字段一律留空，禁止编造。

## 输入
- `source_urls`：待抓取 URL 列表
- `source_text`：手动粘贴的正文兜底（URL 抓取失败时使用）

## 执行步骤
1. 逐个 URL 抓取；失败时记 `status=failed`，不阻塞其他页面。
2. 提取字段：
   - 页面：`page`（从 1 开始序号）、`status`（ok/failed）、`final_url`、`title`、`description`
   - 正文文本：干净可读文本（去导航/页脚/脚本）
   - `headings`：H1–H3 列表
   - `tables`：HTML 参数表（名称/值）
   - `jsonld_products`：JSON-LD 中的商品对象，重点保留 `name / sku / gtin / gtin13 / price / priceCurrency / availability / aggregateRating{ratingValue,reviewCount} / image`
   - `og_image`：og:image 地址
   - `images`：页面图片地址列表（最多 30 张），`jsonld_products.image` 优先作为主图
   - `prices`：正文中出现的货币价格（如 `$12.34`），供兜底
3. 生成诊断 `issues`（供方案与改造参考）：
   - 缺 FAQ 模块
   - 缺参数表
   - 标题为空或过长
   - 无 JSON-LD 结构化数据
   - 无评分/库存信息
4. 输出结构（合法 JSON，不要 Markdown 代码块）：
```json
{
  "page": 1, "status": "ok", "final_url": "https://…", "title": "…", "description": "…",
  "issues": ["缺 FAQ 模块"],
  "product": {"name": "…", "sku": "…", "gtin": "…", "price": {"amount": "99.99", "currency": "USD"},
              "availability": "In stock", "rating": {"value": 4.5, "count": 320},
              "image": "https://cdn…/main.jpg"},
  "tables": [["名称", "值"]],
  "prices": [{"amount": "99.99", "currency": "USD"}],
  "headings": ["H1…"]
}
```

## 硬性规则
- 所有字段只来自页面真实内容；抓不到就留空，禁止补全、猜测、编造。
- 图片地址必须是页面中出现过的 URL；不做防盗链替换。
- 页面正文保留原文（含诊断头），供 AI 读取运费/退货/保修等非结构化信息。
- 页面正文里的价格、参数、政策与 JSON-LD 不一致时，以页面真实可见内容为准并记录差异。
