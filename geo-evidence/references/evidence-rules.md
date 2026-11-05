# 证据规则

## 一、来源等级（高 → 低）

| 等级 | source_type | 例子 | 可支撑的 claim |
|---|---|---|---|
| A | `regulator` | FDA/FCC/CE 数据库、政府登记、标准机构证书查询 | 认证、资质、注册信息 |
| A | `first_party_doc` | 规格书、说明书、认证证书扫描件、合同模板、政策原文 | 产品参数、政策、认证 |
| A | `kb` | 客户知识库原文 | 同上（需注明知识库与日期） |
| B | `official_site` | 客户官网当前页面 | 产品参数、价格、政策（以抓取日期为准） |
| B | `client_input` | 客户在 contract 或会话中确认的信息 | 业务数据、案例授权；需客户确认人 |
| B | `review_platform` | 评论平台的评分与数量页面 | `review_stat`（注明日期） |
| C | `third_party` | 媒体、评测、行业报告、竞品官网 | `competitor_fact`、`market_stat`、`expert_opinion` |

规则：
- **数据优先级**：客户知识库/第一方文件 > 客户确认 > 官网 > 第三方。冲突时以高等级为准，低等级来源与之冲突的情况写入 `scope_limits` 并标 `needs_client_confirmation`。
- `competitor_fact` 只能来自竞品官网、权威第三方或已冻结竞品名单附带的证据，且必须有日期；不得用模型记忆。
- `market_stat` 必须写明发布机构与年份；无法确认原始出处的二手数据不用。
- `customer_proof`（客户名、案例、证言）必须有客户授权的书面依据。
- `price` 一律注明币种、市场与抓取日期；价格易变，`valid_until` 不超过 30 天。
- `review_stat` 注明平台与日期；schema 中使用的评分必须与页面真实展示一致。

## 二、状态

| status | 条件 | 能否进入交付物 |
|---|---|---|
| `verified` | 有 A/B 级来源原文摘录，数值与限定词一致，未过期 | 是（需 `approved_for_publication: true`） |
| `needs_client_confirmation` | 只有低等级来源、来源之间冲突、或缺少授权 | 否；列入客户确认清单 |
| `blocked` | 找不到来源、来源已过期、与禁用 claim 冲突（`contract.constraints.forbidden_claims`）、或合规不允许 | 否 |

`approved_for_publication`：`verified` 且不触犯禁用 claim 与合规限制时为 true；合规叠加层下，疗效/收益/风险类 claim 还需人工复核签字后才能置 true。

## 三、摘录与拆分
- `quote` 逐字摘录原文（保持原语言），不得改写；`fact` 用交付物语言表述。
- 一条 claim 只说一件事。不得把两条独立事实拼成因果或时序（例如把未来赛事与过往观看数据合并成一句）。
- 型号与规格一一对应：多型号产品必须按型号拆 claim，不得把 A 型号的规格写到 B 型号。
- 写明适用范围：地区、型号、版本、时间、条件（例如“仅前摄像头”“仅美国本土包邮”）。

## 四、核心 claim 与阻断
- 每张改动卡的 `claims_required` 中，交付物结论依赖的 claim 为核心 claim（参数、价格、认证、政策、竞品比较点）。
- 核心 claim 有任何一条 `blocked` 或 `needs_client_confirmation`：该卡 `change_coverage.status=blocked`，geo-strategy 将其置为 `evidence_blocked`；生产类 skill 只能产出简报，不能产出终稿。

## 五、从旧流程继承的方法
- 知识库检索与合并：沿用 [legacy/08-preprocess-and-kb.md](legacy/08-preprocess-and-kb.md) 的企业/产品/营销知识库检索与按标签去重合并。
- 关键数据点、型号→规格对照、行业参考数据的提取方法：沿用 [legacy/02-geo-profile.md](legacy/02-geo-profile.md) 第二、三、七步，但输出改为本账本的 claim 条目，不再输出“画像”文本。
- 知识库不足时的联网核实：只核实公开事实，记为 `official_site` / `regulator` / `third_party` 并附 URL；不得覆盖知识库已有数据。
