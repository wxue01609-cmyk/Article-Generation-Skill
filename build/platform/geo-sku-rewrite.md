## 平台落位
- 输出进 `sku_changes`：`{asset_id, source_page, target_url, product, core_answer, trust_badges, benefits, specs, fit, faq, shipping_returns_warranty, brand_identity, reviews_summary, cta, changes, notes}`。
- 1:1 复刻：结构/模块顺序与原商品页一致，只改文字内容；`changes[].before` 必须是页面原文（缺失写「（页面无此模块）」）。
- 价格/评分/库存/图片只填真实抓取值，抓不到留空并在 `notes` 说明；改后正文不得出现「待核验 / pending verification / on the product page / before publishing」等审核语。