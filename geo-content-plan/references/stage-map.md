# 节点归属快速表（geo-content-plan 就地打标用）

> 本文件是 `geo-path-plan/references/01-stage-map.md` 的**镜像副本**（同源规则，禁止单独修改）；
> `build/parity_check.py` 第 3.3 条会逐表比对两份文件，不一致时发布前 FAIL。
> 存在 `plan/path_plan.json` 时以它为准，本表只用于缺省场景。三层沿用采样基线口径：`ai_exposure` / `pdp` / `conversion`。

## 三层定义

| stage | 中文 | 该层目标 | 常见资产（受 asset_types 限制） | 衡量指标基线 |
| --- | --- | --- | --- | --- |
| ai_exposure | AI 曝光 | 让 AI 在泛需求/对比/口碑类回答里提及并引用品牌 | 官网博客、三方评测/PR、社区问答、社交 | sampling.json 中 `ai_exposure` 的品牌提及率 |
| pdp | 商品详情页 | 让 AI 在「品牌+型号」查询时给出准确商品卡与详情 | SKU 页、品牌落地页、类目页 | sampling.json 中 `pdp` 的商品卡/描述准确度 |
| conversion | 购买转化 | 消除购买顾虑，AI 在售后/购买决策中把流量导向站内 | SKU 页（政策模块）、FAQ、落地页 | sampling.json 中 `conversion` 的转化信号占比 |

## 主节点判定（按优先级，命中即定，不叠加）

| 优先级 | 信号词（词面命中即算） | 主节点 |
| --- | --- | --- |
| 1 | `best` / `top` / `review` / `vs` / `versus` / `alternatives` / `compare` / `which` / `worth it` / `reddit` / `forum` / `experience` | ai_exposure |
| 2 | `how to` / `what is` / `why` / `guide` / `tips` / `benefits` / `mistakes` / `learn` / `explained` | ai_exposure |
| 3 | 品牌名 + 型号（同现）且含 `buy` / `price` / `cost` / `specs` / `specification` / `dimensions` / `manual` / `where to buy` / `order` | pdp |
| 4 | 品牌名 + 型号（同现），无购买/价格词，纯导航（`official` / `login` / `download`） | pdp |
| 5 | `return` / `warranty` / `shipping` / `refund` / `cancel` / `delivery` / `is it good for` / `for [use case]` / `set up` / `install` / `troubleshoot` / `not working` / `compatible` / `safe` | conversion |
| 6 | 裸品牌名（无型号、无意图词） | pdp（详情页是品牌承接点） |

- 优先级 1 命中即 `ai_exposure`；若同时有品牌+型号购买词，主节点仍取 ai_exposure，次节点 pdp。
- 优先级 5 命中即 `conversion`；若同时含 `best/review`（如 `best robot vacuum for pets return policy` 之类罕见组合），主节点仍取 conversion，次节点 ai_exposure。
- `how to use` / `install` / `setup` 属于 conversion（售后操作），与 `how to choose/buy`（ai_exposure 教育）区分开。

## 次节点判定（可为 null）

| 条件 | 次节点 |
| --- | --- |
| 主节点 = ai_exposure，且 query 含品牌名/型号 | pdp（文章里带一句"产品详情见官网" + 内链） |
| 主节点 = ai_exposure，且 query 含 `buy` / `price` / `cost` / `where` | conversion（带一句"价格与政策以官网为准" + 内链） |
| 主节点 = pdp，且 query 含 `review` / `best` / `vs` / `worth` | ai_exposure（详情页引用一篇评测 + 链接） |
| 主节点 = pdp，且 query 含 `return` / `warranty` / `shipping` | conversion（详情页补政策模块 + 链接） |
| 主节点 = conversion，且 query 含品牌名/型号 | pdp（政策/FAQ 里指向商品页） |
| 其余 | null（只在一层发力） |

## 示例

| query | 主节点 | 次节点 | 理由 |
| --- | --- | --- | --- |
| best dog water fountain 2026 | ai_exposure | pdp | `best` → 曝光；含品类品牌候选 → 详情页带一句 |
| G980H robot vacuum price | pdp | null | 品牌+型号+price → 详情页；无其它信号 |
| G980H return policy | conversion | pdp | return → 转化；品牌+型号 → 指向商品页 |
| how to clean robot vacuum | conversion | null | how to + 操作类动词 → 转化售后 |
| pawflow pet fountain review reddit | ai_exposure | conversion | review/reddit → 曝光；口碑问题 → 带购买提示 |
| is G980H good for pet hair | conversion | ai_exposure | is it good for + 场景 → 转化；顺带引评测 |

## 用途

- `stage` 进矩阵 item（必填），`secondary_stage` 可选（null 时 JSON 里省略需求见 schema）。
- `by_stage` 进 summary，与 items 统计一致。
- 一条 query 只认真写一篇（主节点那层），次节点只做「带一句 + 链接」。
