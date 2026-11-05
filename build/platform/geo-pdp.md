## 平台落位
- 交付三件套放进 `sku_changes` / `assets` 对应字段：改后 PDP 正文、OpenAI 商品 feed、Google Merchant Center feed、Product JSON-LD；三处价格/库存/GTIN/标题必须一致，不一致以证据账本为准并提醒。
- 只交付可导入文件内容（feed 用标准 CSV/JSON 结构，JSON-LD 用 Product schema），不直接改客户后台、不调平台接口。
- 上传前提示实时价格/库存以客户后台为准；数据日期与平台/货币写进 `notes`。