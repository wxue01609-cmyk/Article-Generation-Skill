# 节点归属快速表（geo-content-plan 就地打标用）

存在 `plan/path_plan.json` 时以它为准，本表只用于缺省场景。三层沿用采样基线口径：`ai_exposure` / `pdp` / `conversion`。

## 主节点
| 信号 | 主节点 |
| --- | --- |
| best / top / review / vs / alternatives / compare / which / worth it / reddit / forum | ai_exposure |
| how to / what is / why / guide / tips / benefits / mistakes | ai_exposure |
| 品牌名+型号 且含 buy / price / cost / specs / dimensions / where to buy | pdp |
| 品牌名+型号，纯导航（official / manual / download） | pdp |
| return / warranty / shipping / refund / is it good for / for [use case] / setup / install / troubleshoot / not working / compatible | conversion |
| 裸品牌名（无型号无意图词） | pdp |

## 次节点（可为 null，不能等于主节点）
- 主=ai_exposure 且含品牌/型号 → pdp（带一句 + 内链）
- 主=ai_exposure 且含 buy/price/where → conversion
- 主=pdp 且含 review/best/worth → ai_exposure
- 主=pdp 且含 return/warranty/shipping → conversion
- 主=conversion 且含品牌/型号 → pdp
- 其余 → null

## 用途
- `stage` 进矩阵 item（必填），`secondary_stage` 可选（null 时 JSON 里省略需求见 schema）。
- `by_stage` 进 summary，与 items 统计一致。
- 一条 query 只认真写一篇（主节点那层），次节点只做「带一句 + 链接」。
