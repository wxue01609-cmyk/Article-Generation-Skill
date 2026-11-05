## 平台落位
- 调用工具 `geo_sample` 一次：传 `topics`（或整理好的 query 列表）、`brand`（company_name）、`competitors`（known_competitors）、`engines`、`target_market` 对应国家代码；任务带 `answers_json` / `samples_json` / `citations_json` 时一并传入。
- 读取返回的 `query_stage` / `query_secondary_stage`，把主层级写入矩阵 item 的 `stage`，次层级写入 `secondary_stage`（可为 null）；矩阵 `summary` 输出 `by_stage`，`notes` 附一句采样基线摘要（来源：真实采样 / 离线分层；各层样本数；品牌提及率）。
- 工具不可用时报错/超时：按规则正文离线打标，`notes` 注明「未采样」。