# 商品结构化数据（JSON-LD）

## 一、模板

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Acme D4 Dual 4K Dash Cam",
  "image": ["https://acme.com/images/d4-front.jpg"],
  "description": "Dual-channel 4K dash cam for rideshare drivers…",
  "sku": "D4-DUAL-64",
  "gtin13": "0123456789012",
  "brand": {"@type": "Brand", "name": "Acme"},
  "offers": {
    "@type": "Offer",
    "url": "https://acme.com/products/d4-dual?variant=123",
    "price": "129.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "itemCondition": "https://schema.org/NewCondition",
    "shippingDetails": {"@type": "OfferShippingDetails", "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "US"}},
    "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": "US", "merchantReturnDays": 30,
                                "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow"}
  },
  "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.6", "reviewCount": "312"}
}
```

多变体商品可用 `ProductGroup` + `hasVariant`（每个变体一个 `Product`，含各自的 `offers`），`variesBy` 写明差异维度。

## 二、规则
- **与页面一致**：价格、库存、评分、评论数必须与页面可见内容一致；schema 里有、页面上没有的信息（尤其评分）不得添加。
- **与 feed 一致**：price / availability / gtin 与 feed 相同。
- **事实来源**：每个值对应证据账本 claim；评分与评论数来自 `review_stat` claim（注明日期）。
- **GTIN**：只填真实且校验位正确的值；不确定时不填。
- **不做**：伪造 `review`、给不存在的评论写 `aggregateRating`、把全站评分写进单品。
- 其他类型按页面需要：FAQPage（FAQ 模块，注意搜索引擎对 FAQ 富结果的展示限制，标记仍有助于机器理解）、BreadcrumbList、Organization（全站）。

## 三、校验
`scripts/check_product_schema.py --jsonld <文件> [--feed <feed 文件>]`：检查必需属性、availability 取值、GTIN 校验位、评分字段完整性，以及与 feed 的价格/库存/GTIN 一致性。上线后建议再用 Google Rich Results Test 与 Schema.org Validator 复核。
