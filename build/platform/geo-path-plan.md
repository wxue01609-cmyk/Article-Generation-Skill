## 平台落位
- 把编排结果 `plan/path_plan.json` 的等价内容输出为矩阵前传：每条 query 的 `stage` / `secondary_stage` 写入后续内容矩阵 item；summary 输出 `by_stage`。
- 判定不了的 query 放进 `notes`（带 reason=unmapped），不硬塞。