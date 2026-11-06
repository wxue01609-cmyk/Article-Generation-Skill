---
name: geo-evidence
description: 海外 GEO 事实证据账本（双通道）。按内容建设矩阵资产（asset_id）或 SKU 改造改动卡（change_id）核实所需事实：从客户知识库、规格书、认证、政策、官网、评论平台与权威第三方逐条摘录原文，建立带来源、日期、适用范围与发布许可的证据账本，计算每个资产/改动卡的证据覆盖并阻断证据不足的改动。当方案已选定、生产内容前需要确认“哪些事实可以写、凭什么”时使用。
---

# GEO 事实证据账本（geo-evidence）

两条通道：①内容建设（13 skill 链路）geo-content-plan 矩阵资产 → **geo-evidence** → geo-content-write / geo-sku-rewrite / geo-pdp → geo-polish；②SKU 改造（改动卡流水线）geo-contract → geo-diagnose → geo-strategy → **geo-evidence** → 生产类 → geo-polish。

本 skill 由 geo-research 的知识库合并（第 1 步）与画像提取（第 4 步）升级而来：不再输出“画像”文本，而是输出**一条条可审计的 claim**。生产类 skill 只能使用账本中 `verified` 且 `approved_for_publication: true` 的 claim。

## 前置条件（两条通道二选一）
- 内容建设通道：`plan/content_matrix.json` 中已确认的资产（按 `asset_id` 核验），成稿前对本资产要用的硬事实（数字/参数/价格/政策/认证/评分）逐项建 claim；不依赖 `strategy/changes.json`。
- SKU 改造通道：`strategy/changes.json` 中已有 `selected: true` 的改动卡（`tech_ticket` 除外），每张卡写明 `claims_required`。
- 资料：`inputs/knowledge/`（或平台知识库文本）下的客户资料；有 `contract.constraints` 时按其禁用 claim 与合规叠加层执行，没有则跳过该检查。

## 必读
- [references/evidence-rules.md](references/evidence-rules.md)：来源等级、状态、摘录与拆分、阻断规则、ledger.json 字段定义（文末附录）。

## 执行流程

### 步骤 1 汇总待核实清单
- 内容建设通道：按 `content_matrix.json` 中已确认资产（含 `selected_asset_ids` 指定的资产）整理要写进正文/改造页的硬事实，逐项作为 claim；同一事实被多个资产需要时只建一条 claim。
- SKU 改造通道：收集所有选中卡的 `claims_required`。
- 按 claim_type 归类，型号相关的按型号拆分。

### 步骤 2 逐条找来源
按 evidence-rules.md 的来源等级从高到低查找：
1. 客户知识库与第一方文件（`inputs/knowledge/`）：逐字摘录原文，记录文件、页码/段落、文件日期。
2. 客户官网当前页面：记录 URL 与抓取日期。
3. 监管与标准数据库（认证、注册信息）。
4. 评论平台（评分、数量，注明日期）。
5. 权威第三方（竞品事实、市场数据、专家观点），必须带 URL 与日期。

找不到来源的 claim 标 `blocked`，不改写成“看起来合理”的表述。

### 步骤 3 判定状态与发布许可
- `verified` / `needs_client_confirmation` / `blocked`，并写 `scope_limits`（适用型号、地区、条件）。
- 触犯 `forbidden_claims` 或合规叠加层限制的 claim 不得 `approved_for_publication`。
- 合规叠加层下的效果/证言类 claim 需要人工复核（`human_reviewed_by`）。

### 步骤 4 计算覆盖并回写
在 `evidence/ledger.json` 的覆盖段中按核验单元列出 `required` / `covered` / `missing`：
- 内容建设通道：字段为 `asset_coverage`，按 `asset_id` 组织；
- SKU 改造通道：字段为 `change_coverage`，按 `change_id` 组织。
```bash
# 内容建设通道（不依赖 changes.json，回写 evidence/evidence_map.json）
python3 scripts/check_ledger.py --project <项目目录> --channel assets --write
# SKU 改造通道（回写 changes.json，缺口卡置为 evidence_blocked）
python3 scripts/check_ledger.py --project <项目目录> --channel changes --write
```

### 步骤 5 客户确认清单
把所有 `needs_client_confirmation` 与 `blocked` 的核心 claim 整理成一份清单交给使用者：缺什么、为什么需要、影响哪个资产/改动卡。客户补齐后更新账本，再重跑步骤 4（只核对仍在使用中的资产/卡）。

### 步骤 6 交还下游
- 内容建设通道：产出 `evidence/evidence_map.json`（`asset_id → [claim_id]`）交还成稿阶段；证据不足的资产在 Brief 标记，正文/改造页不得使用账本之外的具体事实。
- SKU 改造通道：通知 geo-strategy 重跑 `score_changes.py --select`；`status=planned` 且覆盖为 `ok` 的卡进入生产。

## 硬性约束
- 不编造来源、不改写原文摘录、不用模型记忆充当证据。
- 一条 claim 一件事；不拼接独立事实；型号与规格一一对应。
- 价格类 claim 有效期不超过 30 天；过期即失效。
- 账本是唯一事实源：生产类 skill 不得使用账本之外的硬事实（数字、年份、认证、价格、客户名、竞品事实）。

## 输出与交接
1. `evidence/ledger.json`（通过 check_ledger.py）
2. 内容建设通道：`evidence/evidence_map.json`（asset_id → 可用 claim 列表）；SKU 改造通道：回写后的 `strategy/changes.json`（evidence 得分与状态）
3. 客户确认清单（缺口 claim 及影响的资产/改动卡）
