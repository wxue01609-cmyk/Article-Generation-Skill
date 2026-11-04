---
name: geo-path-plan
description: 海外内容建设第零阶段（转化路径编排）。读取 query 词包与企业/产品资料，按转化路径把每条 query 编排到三层节点（ai_exposure AI曝光 / pdp 商品详情页 / conversion 购买转化），每条只允许 1 主节点 + 1 次节点，输出 plan/path_plan.json 供 geo-content-plan 落位资产。当需要"这条 query 该在哪一层发力、文章写在哪"时使用。
---

# GEO 转化路径编排（geo-path-plan）

## 任务
把「一堆 query」按转化路径重新编排：**AI 曝光 → 商品详情页 → 购买转化** 三层，逐条 query 打标。行业只作为素材参数，不决定调度。输出 `plan/path_plan.json`，作为 geo-content-plan 渠道落位的前置输入。

## 输入
- `fields.topics`（主题 → query 清单）或 `fields.keyword_pack`（词包，每行一条）
- `fields.company_name` / `product_info`（主力型号） / `known_competitors` / `target_market` / `engines`
- `fields.asset_types`（本任务启用的资产类型，决定该层可落位的资产）
- 可选：`research/sampling.json`（分层采样基线，作为打标校准；无缓存/未采样时按本 skill 规则离线打标，输出注明）

## 输出（唯一交付物）
`plan/path_plan.json`，严格遵循 [references/02-path-schema.md](references/02-path-schema.md)。终端最多输出 10 行摘要，禁止把整份 JSON 打印到对话里。

## 执行步骤
1. **清洗 query**：`keyword_pack` 每行一条；`topics` 提供主题归属；归一化去重，问句保留原始问法。
2. **逐条打标主节点**：按 [references/01-stage-map.md](references/01-stage-map.md) 的信号表判定 `stage`（只允许一个主节点），写 `signals`（词面证据）与 `confidence`。
3. **打次节点**：每条再选一个 `secondary_stage`（可为 null，不能等于主节点）。次节点 = 「顺手带一句 + 内链」，不是写第二篇文章。
4. **同层聚合**：同一主节点下的 query 按主题/实体聚类，标注哪些可共享一篇资产（`share_with`），避免同层重复写稿。
5. **与采样基线对账**：若存在 `research/sampling.json`，把本计划的 `by_stage` 与基线 `summary.by_stage` 对比；偏差超过 ±30% 时在 `risk_notes` 说明原因（品牌词多 → pdp 偏高属正常），不强行改标。
6. **自检**（必须全部通过）：
   - `summary.total_queries == len(items)`
   - 每个 item 都有 `stage`，`secondary_stage != stage` 或为 null
   - `asset_types` 里本层没有可落位类型时，该 query 标 `force_reassign` 并在 `suggestion` 给出现有可用类型
   - 不编造信号：`signals` 必须是 query 里真实出现的词
7. **写文件**：用 apply_patch 写入 `plan/path_plan.json`。

## 硬性规则
- 一条 query 只认真写一篇（主节点那层）；次节点只做「带一句 + 链接」，绝不写两篇。
- 打标只看词面信号，不靠行业经验猜；industry 只作为素材参数。
- 判定不了的 query 进 `unmapped`（带 reason），不硬塞。
- 本 skill 只做编排，不落渠道、不写资产类型、不生成 Brief（那是 geo-content-plan 的事）。
