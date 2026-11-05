## 平台落位（字段名铁律）
- 矩阵 item 字段名必须严格用 `asset_id` / `primary_query`（不是 id/query），否则平台勾选成稿会失败；写完逐项核对。
- 分层与编排：优先采用 `geo_sample` 返回的 `query_stage`；工具不可用或返回离线分层时，若带 `plan/path_plan.json` 直接采用其 `stage` / `secondary_stage`；两者都没有时按 stage-map 就地打标。每个 item 必须带 `stage`，`secondary_stage` 有值就写（只做内链位，不另产文章）。
- 本次带 `citations_json` 时：把与 item 同层的引用条目写进 Brief 的 `reference_citations`（只借鉴标题层级与证据点类型，禁止照抄原文句子）；官网资产不得因此出现竞品品牌名。
- 输入提供 `source_urls` 且可能落 SKU 资产时，先按规则核对待改造页面匹配，不允许虚构。
- 三方类资产（thirdparty_pr / thirdparty_review / qna / social / ecommerce）：`target_url` 必须写 `external:TBD`，禁止编造第三方 URL。