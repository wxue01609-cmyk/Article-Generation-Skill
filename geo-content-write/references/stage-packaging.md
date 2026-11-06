# 成稿包 · 按 stage 分组输出与增量重跑

## 目录结构（平台兼容，文件不搬家）
```
plan/
  content_matrix.json        # 矩阵（含 stage / secondary_stage）
  sku_changes/<id>.json      # SKU 改造 JSON（平台渲染四件套）
assets/
  asset_index.json           # 全量索引（合并写，每项含 stage）
  stage_index.json           # 按 stage 的索引（整份重写）
  <asset_type>/<id>.html     # 普通资产成品（路径不变，平台按 file 字段取）
  sku/<id>.html …            # SKU 成品（平台渲染）
packs/
  ai_exposure/manifest.json  # 该层交付清单
  pdp/manifest.json
  conversion/manifest.json
polish_report.json           # geo-polish 全链路质检结果
```

## asset_index.json 每项
```json
{"asset_id": "blog-01", "asset_type": "blog", "stage": "ai_exposure",
 "title": "…", "file": "assets/blog/blog-01.html", "word_count": 1180, "checks": []}
```

## stage_index.json
```json
{"ai_exposure": {"count": 3, "assets": ["blog-01", "review-01"]},
 "pdp": {"count": 1, "assets": ["sku-01"]},
 "conversion": {"count": 1, "assets": ["faq-01"]}}
```

## packs/<stage>/manifest.json
```json
{"stage": "ai_exposure", "generated_at": "…",
 "assets": [{"asset_id": "blog-01", "asset_type": "blog", "file": "assets/blog/blog-01.html", "title": "…"}]}
```

## 增量重跑规则
- 输入 `selected_stages=["ai_exposure"]`：只生成该层资产，`asset_index.json` 合并写（其它层条目保留），`stage_index.json` 整份重写，`packs/` 只刷新该层 manifest。
- 重跑某层前先读 `polish_report.json` 该层 blocking 项：已修复的不重复报。
- SKU 改造资产先出 `plan/sku_changes/<id>.json`，平台渲染后才把成品登记进 `asset_index.json`；增量时平台负责合并该部分。
- feed/JSON-LD 等商品数据交付由 geo-pdp 写 `plan/sku_deliverables/<id>/` 目录（不改 `<id>.json`），两者分工见 geo-pdp 的 SKILL.md。
