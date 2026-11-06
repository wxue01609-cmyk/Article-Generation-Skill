## 平台落位
- 青蛙端没有 `scripts/*` 脚本与磁盘：按规则正文人工逐关执行（不要把五关当成可选），输出结构与规则正文一致。
- 对成稿包按 stage 分组跑五关（事实/证据/可提取/渠道/分发），输出进 `polish_report`：`{"by_stage": {stage: {"passed": bool, "checks": [...]}}, "summary": {...}}`。
- 有 blocking 的层不得交付：先修复，修复后只重跑该层，不丢其它层；warning 记入 `checks` 放行。
- `stage_index` 与磁盘产物一一对应（平台无磁盘，以输出数组实际内容为准）；索引对不上时标 blocked。