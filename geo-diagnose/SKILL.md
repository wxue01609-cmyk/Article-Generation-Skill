---
name: geo-diagnose
description: 海外 GEO 内容优化流水线第二步（答案与来源诊断）。读取选词 skill 的问题文件和 geo-monitoring / 监测平台导出的答案结果（本 skill 不采样），按问题族统计提及、排位、份额、引用来源与商品卡，审计站点 AI 可读性与场景专属项，核验竞品，判定每个问题族卡在哪个失败层。当 contract.json 已就绪、需要诊断“AI 现在怎么回答、我们输在哪里”时使用。
---

# GEO 答案与来源诊断（geo-diagnose）

两条通道：①内容建设（13 skill 链路）监测数据 → **geo-diagnose** → 回流补丁（reflow_patch.json）→ geo-content-plan；②SKU 改造（改动卡流水线）geo-contract → **geo-diagnose** → geo-strategy → geo-evidence → 生产类 → geo-polish。

本 skill 回答一个问题：**每个高价值问题族，品牌现在卡在哪一层？** 不出方案、不写内容。

## 前置条件
- 监测结果文件：`inputs/monitoring/` 或平台导出的 `answers_json`。**本 skill 不自行采样、不调用 AI 接口**；没有结果文件就停止，请使用者先跑监测。
- 问题文件（可选）：`inputs/question_bank.json` 或 `plan/content_matrix.json` 中的 query 清单。
- 有 `contract.json` 时按其约束执行；内容建设通道没有该文件时跳过（不以它为阻塞条件）。

## 必读
- [references/monitoring-input.md](references/monitoring-input.md)：结果文件格式与字段映射。
- [references/failure-layers.md](references/failure-layers.md)：失败层判定规则与置信度。
- [references/site-audit.md](references/site-audit.md)：站点与场景审计清单。
- [references/artifact-contracts.md](references/artifact-contracts.md)：responses / topic_metrics / diagnosis 字段定义与场景审计项说明。

## 执行流程

### 步骤 1 归一化答案数据
```bash
python3 scripts/normalize_monitoring.py --project <项目目录>
```
- 结果文件包含多期导出时，用 `--only <文件名片段>` 只处理诊断期文件。
- 新平台首次接入时按 monitoring-input.md 第四节写 mapping.json 并抽查。
- `unmatched_questions` 不为空时，先查明原因（问题 ID 不一致 / 问句改写），不要带着未匹配记录往下算。

### 步骤 2 竞品名单
- `contract.competitors.status=frozen`：直接使用，不增删。
- 否则按竞品核验流程（承接自 geo-research，文件已内置）（离线候选 → 联网核实 → 合并去重 → 单个校验）：[03](references/competitor/03-competitor-offline.md)、[04](references/competitor/04-competitor-search.md)、[05](references/competitor/05-competitor-verify.md)、[06](references/competitor/06-competitor-dedupe.md)。同时参考答案中实际出现的品牌（responses 的 `brands_mentioned`）。结果写回 `contract.competitors`（`status=verified`，附证据 URL），然后**重跑步骤 1**，让排位推断包含新竞品。

### 步骤 3 站点审计
```bash
python3 scripts/audit_site.py --project <项目目录> --bot-check
```
再按 site-audit.md 完成「人工」项和该场景的审计项（电商需对照 PDP 导出与 feed 导出核对价格、GTIN、变体）。

### 步骤 4 按问题族统计
```bash
python3 scripts/compute_topic_metrics.py --project <项目目录>
```
得到每个 topic 的提及率（按问题类型拆分）、平均排位、声量份额、头部竞品、引用来源结构、商品卡指标、情感、分平台数据和建议失败层。

### 步骤 5 判定失败层（模型）
逐个 topic 按 failure-layers.md 确认或推翻建议层，写入 `diagnosis/diagnosis.json`：
- `business_value`（0-10）：依据问题族优先级、旅程阶段、对应业务对象的金额输入（场景包价值公式），写明依据。
- `evidence`：可复核的数字；`source_gaps`：竞品被引用、品牌缺席的高频域名；`accuracy_issues`：答案原话 vs 正确事实 vs 来源。
- `scenario_findings`：场景审计发现（如“SKU-123 价格只由 JS 渲染，Offer schema 缺失”）。
- 推翻建议层时写 `layer_override_reason`；有分析数据时检查高可见度 topic 是否 `recommended_not_converting`。

```bash
python3 scripts/check_diagnosis.py --project <项目目录>
```

### 步骤 6 诊断报告
写 `diagnosis/diagnosis.md`（给人看）：数据范围与可信度 → 失败层分布（按商业价值加权）→ 高价值问题族逐个说明 → 站点问题 → 竞品与来源格局 → 待确认问题。

## 硬性约束
- 只读不采：答案数据全部来自结果文件；不补采、不臆测 AI 会怎么回答。
- 数据不足就标 `insufficient_data` 或 `evidence_level=hypothesis`，不下确定结论。
- 不把相关当因果，不承诺改动效果。
- 审计环境网络受限（`unreachable`）不等于页面有问题，需人工复核。

## 输出与交接（给 geo-strategy）
1. `diagnosis/responses.jsonl`、`topic_metrics.json`、`site_audit.json`
2. `diagnosis/diagnosis.json`（通过 check_diagnosis.py）
3. `diagnosis/diagnosis.md`
4. 更新后的 `contract.competitors`（如有核验）
