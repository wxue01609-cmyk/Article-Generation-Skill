## 平台落位
- 输入 `monitoring_json`（监测平台导出的 AI 答案数组/对象），不自己采样、不调 AI 接口。
- 输出进 `diagnosis`：`{"by_stage": {...指标}, "failing_queries": [...], "competitors": [...], "recommendations": [...], "notes": [...]}`；指标只来自输入数据，编不出来就标 `insufficient_data`。
- 判定每条 query 卡在哪个失败层（ai_exposure / pdp / conversion），给下一轮方案的回流建议（不改稿、不产资产）。