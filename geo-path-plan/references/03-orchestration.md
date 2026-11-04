# 三 stage 并行 / 增量生产规则

三层互不阻塞：任一层可单独开工、单独重跑，不要求另外两层先完成。

## 并行
- 同一任务内三层可同时生产：`ai_exposure` 出博客/评测，`pdp` 出详情页改造，`conversion` 出 FAQ/政策模块。
- 并行前提只有两条：① 矩阵里该层资产的 Brief 已确认；② 该层所需事实已就绪（普通资产可带「待核验」，SKU 改造必须过 geo-evidence）。
- 冲突处理：两个资产引用同一条事实时，以知识库原文为准；口径不一致时后写的一方回读先写的一方，不各自表述。

## 增量（改一层只重跑一层）
| 变更 | 只重跑 | 不必重跑 |
| --- | --- | --- |
| 补了一批 ai_exposure 层 query | ai_exposure 层资产 | pdp / conversion 层既有产物 |
| 商品页价格/参数变了 | pdp + conversion（政策/FAQ 引用到价格时） | ai_exposure 层（除非正文引用了该价格） |
| 换了退货/保修政策 | conversion 层 | 其它两层 |
| 品牌卖点表述调整 | 三层都受影响（共享事实） | — |

## 增量实现口径（与 geo-content-write 对齐）
- 输入 `selected_stages`（数组，缺省三层全跑）→ 只生成这些层的资产。
- `assets/asset_index.json` **合并写**：同 `asset_id` 覆盖，其它层条目原样保留，末尾按 `stage` 重排。
- `assets/stage_index.json` 每次整份重写，只统计当前已存在的产物文件。
- 重跑某层前，先读 `polish_report.json` 中该层的 blocking 项，已修复的不再重复报。

## 打包
- 交付包按 stage 分组目录：`packs/<stage>/`（manifest 清单 + 资产文件引用），不复制大文件，用清单指到 `assets/`。
- 平台侧按 `asset_index.json` 的 `file` 字段取文件，路径仍是 `assets/<asset_type>/<id>.html`（保持平台兼容，不因分组搬家）。
