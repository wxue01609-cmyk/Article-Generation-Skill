## 平台落位
- 方案阶段先由工具 `geo_sample` 分层，`geo_sample` 有结果时直接采用其 `stage` / `secondary_stage`，本技能作为兜底编排：再核对一次「1 主节点 + 1 次节点」与内链位，不重复分层。
- 把编排结果 `plan/path_plan.json` 的等价内容输出为矩阵前传：每条 query 的 `stage` / `secondary_stage` 写入后续内容矩阵 item；summary 输出 `by_stage`。
- `geo_sample` 不可用或输入带 `path_plan_json`（上游编排结果）时，以本技能为主体完成分层编排。
- 判定不了的 query 放进 `notes`（带 reason=unmapped），不硬塞。