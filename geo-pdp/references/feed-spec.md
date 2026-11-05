# 商品数据 feed 规范

商品卡的数据主要来自商家提交的结构化商品数据。本流水线产出 feed 文件或字段改写建议，由客户上传（第一版不直接对接客户后台或平台 API）。

## 一、OpenAI（ChatGPT 购物）商品 feed

来源：OpenAI Commerce Product Feed Spec（https://developers.openai.com/commerce/specs/feed ，2026-11-02 查阅）。要点：
- 每个可购买商品或变体一行；标准上传目前只面向美国市场。
- 结账（checkout）需要单独开通的集成；广告字段另有要求。
- 原始评论与问答列表**不在**该 feed 的范围内。
- 价格或库存变化时（促销开始/结束、售罄）应及时更新；feed 中的日期字段不会自动调度价格或库存变化。
- 资格标记不保证展示。

**必填（9 个）**

| 字段 | 要求 |
|---|---|
| `item_id` | 稳定唯一，不复用 |
| `title` | 建议 ≤150 字符，包含变体信息 |
| `description` | 纯文本，建议 ≤5000 字符 |
| `url` | 商品页，尽量选中对应变体 |
| `brand` | 真实品牌，不能用占位值 |
| `seller_name` | 卖家名称 |
| `image_url` | JPEG 或 PNG 直链 |
| `price` | 格式 `79.99 USD` |
| `availability` | `in_stock` / `out_of_stock` / `pre_order` / `backorder` / `unknown`；缺失或非法值整行被拒 |

**推荐/可选**
- 标识与变体：`group_id`、`listing_has_variations`、`variant_dict`、`offer_id`、`gtin`（8/12/13/14 位且校验位正确）、`mpn`（不得为了替代缺失的 GTIN 而编造 MPN）。
- 属性：`condition`、`product_category`、`material`、`color`、`size`、`gender`、`age_group`、`dimensions`（或 `length`/`width`/`height` + `dimensions_unit`）、`weight` + `item_weight_unit`。
- 图片：`additional_image_urls`。
- 价格：`sale_price`（为正、低于 `price`、同币种）。
- 卖家：`seller_url`。
- 物流：`shipping_price` 或元组形式的 `shipping`（同一笔费用不要两者都填）。
- 退货：`accepts_returns`、`return_deadline_in_days`、`return_policy`。
- 评论：`review_count`、`star_rating`（0-5，两位小数）。
- 资格：`is_eligible_search`（默认 true；设为 false 同时关闭结账）、`is_eligible_checkout`（默认关闭，需集成开通，并要求 `seller_privacy_policy` 与 `seller_tos`）、`is_ads_eligible`。别名 `enable_search` / `enable_checkout` 同时出现时以 `enable_` 为准，只发一种。

## 二、Google Merchant Center 商品数据

Google 购物与 AI 模式的商品信息来自 Merchant Center。以下为常用字段，**字段要求以 Google 官方《Product data specification》为准，交付前核对最新版本**（本文件未逐项核验）。

| 字段 | 说明 |
|---|---|
| `id` `title` `description` `link` `image_link` `availability` `price` | 基础必填 |
| `brand` `gtin` `mpn` | 有 GTIN 的商品应提供 GTIN；没有时用品牌 + MPN，并按规范标记 |
| `condition` | 二手/翻新商品必须标注 |
| `item_group_id` + `color` / `size` / `material` / `pattern` | 变体商品 |
| `sale_price` `sale_price_effective_date` | 促销 |
| `shipping` `return_policy_label` 等 | 物流与退货（也可在账户层设置） |
| `product_highlight` `product_detail` | 卖点与参数（适合承载 PDP 的关键卖点与参数表） |
| `google_product_category` `product_type` | 类目 |

## 三、统一做法
1. 先从 PDP 导出 / feed 导出整理一份**内部商品记录**（每个变体一行），字段取上面两套规范的并集。
2. 字段值只用证据账本中可发布的 claim；无法核实的属性留空，不编造。
3. 改写重点：标题加入区分属性与场景（不堆砌）；描述首句即核心答案；补齐 GTIN、变体、材质/尺寸/重量、物流与退货、评论字段。
4. 按目标平台导出：`feed_openai.csv`、`feed_google.tsv`（按需），并附 `feed_changes.md`（字段 | 原值 | 新值 | 原因 | claim_id）。
5. 运行 `scripts/check_feed.py` 校验，再与 PDP、schema 交叉核对价格、库存、GTIN 是否一致（`scripts/check_product_schema.py --feed`）。
