---
name: geo-layered-sampling
description: 分层采样基线。把词包 query 按转化路径（AI 曝光 / 商品详情页 / 购买转化）分层，得到「平台 × 层」基线（样本数、品牌提及率、来源引用率、商品卡率），并给每条 query 标注 stage 与 secondary_stage 供内容矩阵使用。当需要"这套词包在 AI 里现在怎么被回答、每层有多少样本"时使用。
---

# 分层采样基线（geo-layered-sampling）

## 任务
把词包 query 按转化路径（AI 曝光 / 商品详情页 / 购买转化）分层，得到「平台 × 层」基线，并给每条 query 标注 `stage`，让内容矩阵的资产分布与 AI 曝光 → 详情页 → 转化漏斗对齐。

## 转化层级定义
- `ai_exposure` AI 曝光：榜单/推荐/评测/对比/选购指南/科普（best、top、recommend、review、vs、guide、how to choose/buy、what is）
- `pdp` 商品详情页：价格/参数/规格/购买/差异比较（price、specs、buy、difference、品牌+型号导航）
- `conversion` 购买转化：售后/物流/保修/政策/兼容/操作安装（return、warranty、shipping、policy、compatible、is it good for、how to install/setup/clean/use）

## 输入
- `topics`（主题 → query 清单）或 `keyword_pack`（每行一条）
- `brand`（company_name）、`competitors`（known_competitors）、`engines`、`target_market` 对应国家代码
- 可选：`answers_json`（平台已采集的真实 AI 答案数组）、`samples_json`（现成采样结果）、`citations_json`（平台抓取的「AI 实际引用的第三方页面」摘要）

## 分层规则（与 geo-path-plan 的 stage-map 一致）
1. 逐条 query 按词面信号打分：`ai_exposure` / `pdp` / `conversion` 三套信号表；分数并列时优先级 曝光 > 转化 > 详情页。
2. `best/top/recommend + buy` 判为榜单意图（曝光），抵消 pdp 的 buy 权重。
3. 品牌/型号命中只加分证明「产品相关」，不决定层级。
4. `how to + 售后/操作词`（return/cancel/exchange/claim/refund/warranty/install/set up/setup/troubleshoot/fix/clean/use/not working）强制归转化层；`how to + choose/buy/select/pick` 归曝光层（选购教育）。
5. `what is / what are / what's` 科普问法归曝光层（教育内容），与详情页参数问法（specs/price/buy）区分。
6. 每条 query 只允许 1 个主层级（`stage`）；可再选 1 个次层级（`secondary_stage`，可为 null，不能等于主层级）。
7. 次层级只做「主层资产里带一句 + 内链」的落点，不产第二篇文章。

## 采样来源优先级
1. `answers_json`：真实平台答案数组（query/platform/answer/cited_sources/product_cards），有新粘贴的真实答案时直接按平台×层聚合基线，不需要再用缓存或已算好的结果。
2. `samples_json`：没有 answers_json 时，直接采用已算好的采样结果，只解析与格式化。
3. 以上都没有：按分层规则离线打标，输出注明「离线分层（未采样，仅规则打标）」。

## 输出
- `query_stage`：`{query: stage}`；`query_secondary_stage`：`{query: secondary_stage|null}`
- `stages`：每层样本数、品牌提及率、来源引用率、商品卡率；`platforms`：平台×层基线
- 把每条 query 的主层级写入内容矩阵 item 的 `stage`，次层级写入 `secondary_stage`

## 硬性规则
- 同一条 query 的 `stage` 全局一致，不许在不同资产里标不同层。
- 采样回答原文只用于核验与统计，**不得原样写入下游文章**。
- 引用内容（`citations_json` / `citations`）：只允许借鉴结构与证据点类型，任何句子、列表、段落不得照抄；与知识库冲突时以知识库为准。
- 引用条目按 `stage` 使用：只把与本条 query 同层的引用写进该资产的参考，不跨层混用。
- `stage` 只影响资产的漏斗定位与 Brief 角度，不改变渠道/资产类型决策。
