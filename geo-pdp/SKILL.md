---
name: geo-pdp
description: 海外 GEO 商品数据交付 skill（独立站电商专用，双通道）。内容建设通道：按 content_matrix.json 中 asset_type=sku 且需要 feed/JSON-LD 的资产，改造商品详情页、产出商品数据 feed 与 Product 结构化数据；SKU 改造通道：按 geo-strategy 的改动卡（pdp_rewrite / product_feed / product_schema）。只使用证据账本中可发布的事实，产出改前改后对照、改后正文 HTML、可上传的 feed 文件（OpenAI / Google Merchant Center）和 Product JSON-LD，并做一致性校验。当电商客户的 SKU 需要进入 AI 商品卡、被正确描述或提升 AI 来源转化时使用。
---

# GEO 商品详情页与商品数据（geo-pdp）

两条通道：①内容建设（13 skill 链路）geo-content-plan 矩阵中的 sku 资产 → geo-evidence → **geo-pdp** → geo-polish（全链路）；②SKU 改造（改动卡流水线）geo-contract → geo-diagnose → geo-strategy → geo-evidence → **geo-pdp** → geo-polish（改动卡模式）。

内容建设通道：处理矩阵中 `asset_type=sku` 且挂 `source_page`、需要 feed/JSON-LD 交付的资产（由 agent 编排按 `selected_asset_ids` 决定是否进入本轮）。SKU 改造通道：只处理 `executor=geo-pdp` 的改动卡，仅用于 `dtc_ecommerce` 场景。

## 前置条件（两条通道二选一）
- 内容建设通道：`content_matrix.json` 中该 sku 资产已确认（`selected_asset_ids` 含它或全选），有 `source_page`/`source_url`，且 `evidence/evidence_map.json` 中该资产的可用 claim 覆盖其交付所需硬事实；证据不足的资产只产出“待补资料清单”。
- SKU 改造通道：改动卡 `status=planned`、`selected=true`，且证据账本中该卡 `change_coverage.status=ok`。
- 现状资料：线上页面（`source/index.json` 对应页面或 `contract.inputs.ecommerce.pdp_export`）、feed 导出（如有）。

## 必读
- [references/pdp-content.md](references/pdp-content.md)：PDP 模块、写法与交付物。
- [references/feed-spec.md](references/feed-spec.md)：OpenAI 商品 feed 与 Google Merchant Center 字段。
- [references/product-schema.md](references/product-schema.md)：Product / Offer JSON-LD 模板与规则。
- [references/pdp-content.md](references/pdp-content.md)「交付物」一节：`manifest.json` 字段（`core_answer` / `claims_used` / `target_url` / `internal_links` 等）。

## 执行流程

### 步骤 1 读现状
读取该 SKU 的现有标题、描述、卖点、参数、价格、变体、购买信息、评论展示、schema 与 feed 字段；对照 diagnosis 中该 topic 的失败层与发现（例如“价格只由 JS 渲染”“卡片商家是 Amazon”“答案把续航说错”）。

### 步骤 2 按卡片/资产类型生产
- **pdp_rewrite**（SKU 改造通道）或 **SKU 页改造**（内容建设通道）：按 pdp-content.md 的 10 个模块逐个给出改后内容，产出 `before_after.md` 与 `pdp.html`。关联的核心问法必须在页面上有直接答案；`core_answer` 写进 manifest。
- **product_feed**：整理商品记录（每个变体一行），按目标平台导出 `feed_openai.csv` / `feed_google.tsv`，附 `feed_changes.md`（字段 | 原值 | 新值 | 原因 | claim_id）。
- **product_schema**：按模板生成 `product.jsonld`；评分只在页面真实展示时添加。

每个硬事实（参数、价格、GTIN、政策、评分、认证）必须对应账本中 `verified` 且可发布的 claim，记入 manifest 的 `claims_used`。

### 步骤 3 校验
```bash
python3 scripts/check_feed.py --feed deliverables/<change_id>/feed_openai.csv --spec openai
python3 scripts/check_product_schema.py --jsonld deliverables/<change_id>/product.jsonld --feed deliverables/<change_id>/feed_openai.csv --page deliverables/<change_id>/pdp.html
```
PDP、feed、schema 三处的价格、库存、GTIN、标题必须一致；不一致时以证据账本为准并在交付说明中列出需同步修改的位置（包括 Amazon 等平台 listing）。

### 步骤 4 交付
- 内容建设通道：产出交付文件后写 `manifest.json`（`core_answer` / `claims_used` / `target_url` / `final_url` / `internal_links`），与 `plan/sku_changes/<asset_id>.json` 一并交给 geo-polish（全链路第 2 关校验 `claims_used`）。
  - 分工：`plan/sku_changes/<asset_id>.json` 由 `geo-content-write` 产出（改后正文的结构化 JSON，平台据此渲染四件套）；本 skill 只写交付目录，不改那个 JSON。
  - 交付目录用 `plan/sku_deliverables/<asset_id>/`，不要写同名目录 `plan/sku_changes/<asset_id>/`，避免与上面的 JSON 文件冲突。
- SKU 改造通道：写 `deliverables/<change_id>/manifest.json`，改动卡 `status` 置为 `in_production`，交给 geo-polish（改动卡模式）。

## 仓库边界
- 内容建设通道（矩阵资产 → feed/JSON-LD）在本仓库内闭环，脚本只用 `scripts/` 下的三个校验器与标准库。
- SKU 改造通道依赖仓库外的 `geo-contract` / `geo-strategy` / `geo-measure` 三个 skill（改动卡、坐席与复盘）；本仓库只保证改动卡的交付物格式与质检口径，不包含那三个 skill 的实现。

## 硬性约束
- 不编造参数、认证、评论、评分、库存与价格；无法核实的属性留空。
- 不写绝对化营销词（best / #1 / ultimate 等）和压力话术（限时、仅剩）。
- 第一版只交付可导入文件与改后内容，不直接修改客户店铺后台或调用平台 API。
- 价格与库存会变化：交付说明中写明数据日期，提醒客户在上传前以实时数据为准。

## 输出
- 内容建设通道：`plan/sku_deliverables/<asset_id>/`：`before_after.md`、`pdp.html`、`feed_*.csv|tsv`、`feed_changes.md`、`product.jsonld`、`manifest.json`（按资产需要取用）。改后正文 JSON 仍由 geo-content-write 写在 `plan/sku_changes/<asset_id>.json`，两者不要互相覆盖。
- SKU 改造通道：`deliverables/<change_id>/`：同上文件集（按卡片类型取用）。
