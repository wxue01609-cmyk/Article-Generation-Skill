# 失败层判定规则

每个问题族（topic）只判定一个**主失败层**：最上游、最先需要解决的那一层。上游没解决时，下游动作通常无效（页面抓不到，改文案没有意义）。

## 一、判定顺序与依据

`compute_topic_metrics.py` 按下列顺序给出 `suggested_layer`，模型在 diagnosis.json 中确认或推翻；推翻必须写 `layer_override_reason`。下表中的“提及率”指 **非验证类问题的提及率**（`unbranded_mention_rate`）：问句里点名品牌的验证类问题提及率天然偏高，不计入可见度判断；没有非验证类问题时才退回整体提及率。

| 顺序 | 失败层 | 脚本触发条件（默认阈值 low=0.2 / high=0.5） | 模型需要补充确认的证据 |
|---|---|---|---|
| 0 | `insufficient_data` | 该 topic 答案数 < 6 | 是否需要补采样；不得据此下结论 |
| 1 | `crawl_blocked` | 该 topic 对应的业务对象页面在 site_audit 中 `blocked=true`（HTTP 错误、noindex、robots 拦截搜索类爬虫、爬虫 UA 被 WAF 拦截） | 拦截是否针对全部相关页面；是否只是审计环境网络受限（`unreachable` 不算拦截） |
| 2 | `not_in_product_pool` | 电商/平台卖家场景，商品卡出现率 ≥30%，品牌卡片率为 0 | 品牌 SKU 是否在平台商品目录中（Merchant Center / feed 状态需客户确认）；卡片商家是谁 |
| 3 | `mentioned_inaccurate` | 带事实错误标注的答案 ≥10%，或品牌提及中负面情感 ≥20% | 逐条列出 `accuracy_issues`：答案原话、正确事实、正确事实的来源 |
| 4 | `strong` | 提及率 ≥ high | 若有分析数据，检查 AI 来源访问与转化；可见度高但转化低时改判 `recommended_not_converting` |
| 5 | `cited_not_mentioned` | 自有页面被引用的答案 ≥20%，但提及率 < low | 被引用的是哪些页面、哪段内容；品牌名/品类是否在该段落中清楚出现 |
| 6 | `known_not_recommended` | 发现类（Discovery）提及率 < low，且验证类问题提及率 ≥ high | 竞品靠哪些来源胜出（source_gaps）；第三方是否存在品牌 |
| 7 | `not_selected` | 提及率 < low 且自有页面被引用率 < 5% | 是否有对应主题的自有页面；页面是否覆盖问题族的核心问法 |
| 8 | `known_not_recommended` / `strong` | 提及率在 low 与 high 之间：头部竞品提及率 > 品牌 1.5 倍判 `known_not_recommended`，否则 `strong` | 头部竞品的来源结构 |

`recommended_not_converting` 脚本不会自动给出：必须有 `contract.inputs.analytics` 中的 AI 来源访问/转化数据作为依据，由模型判定。

## 二、问题类型的读法
- 问题文件的 `prompt_type` 为 `Discovery` 的题计入“发现率”；类型名含 `Verif` / `Brand` / `验证` 的题计入“验证率”。
- 品牌名出现在问句中的题（验证类、点名对比类）提及率天然偏高，不能和发现类混算可见度。
- 交易类、购后类问题单独成组分析（它们对电商转化很重要，但选词规范不计入自然可见度）。

## 三、场景差异
- **电商 / 平台卖家**：先看商品卡，再看文字提及。卡片里没有品牌时，即使文字提及率尚可，也优先判 `not_in_product_pool`。
- **B2B / SaaS**：重点看第三方评测和目录（G2、Clutch、行业目录）在引用来源中的占比；竞品靠第三方胜出时判 `known_not_recommended`。
- **本地服务**：地址、营业时间、电话说错一律归 `mentioned_inaccurate`。
- **品牌认知**：没有对比决策层；重点看描述准确度与一致性。

## 四、置信度
- `high`：问题文件已锁定、每题 ≥3 次采样、覆盖 ≥2 个平台，且多个指标指向同一结论。
- `medium`：满足采样要求但只有单一平台，或指标之间部分矛盾。
- `low`：采样不足、问题文件未锁定，或依赖推断字段（`derived`）较多。

## 五、写法要求
- `evidence` 写可复核的数字和事实（“商品卡出现在 72% 的答案中，品牌卡片率 0%”），不写形容词。
- 不把相关当因果：诊断只描述现状与最可能的瓶颈，不承诺改动后的效果。
