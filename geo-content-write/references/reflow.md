# 诊断回流闭环（geo-diagnose）

内容建设不是一次性的：成稿发布后，用监测数据回流诊断，把「AI 现在怎么回答」和「我们产出的内容」对账，增量修补矩阵。

## 触发时机（任一即可）
- 成稿交付完成、发布一段时间后（接监测平台数据）
- 客户反馈「某个 query 还是没被 AI 提及 / 提及但内容不对」
- 换价格/参数/政策后只想验证某一层

## 依赖
- 需要已安装 `geo-diagnose`（来自 SKU-Content-Upgrade-Skill 或本地 `~/.codex/skills/geo-diagnose`），本 skill 不重复实现诊断逻辑。
- 输入数据：`research/sampling.json`（分层基线）+ 监测平台导出的答案结果（本流程用平台或脚本产出，diagnose 不自行采样）。

## 流程
1. **采样/拉数据**：对 `plan/path_plan.json` 的 query 清单跑一次分层采样，得到新的 `research/sampling.json`（或 answers.jsonl）。采样统一走 `geo-layered-sampling`：青蛙通道用 `geo_sample` 工具；本地通道由平台预生成 `research/sampling.json`。**不要依赖单篇生文旧线的 `geo-research/scripts/sample_by_stage.py`**（不属于内容建设 13 skill，青蛙包内不存在）。
2. **诊断**：调 geo-diagnose，读取新基线，按问题族统计提及、排位、引用来源、商品卡；逐层判定「卡在哪个失败层」。
3. **出回流补丁**：产出 `plan/reflow_patch.json`：
   ```json
   {
     "version": "1.0",
     "diagnosed_at": "2026-11-20 10:00:00",
     "by_stage": {
       "ai_exposure": {"issues": ["unbranded_mentions"], "actions": [{"type": "add_item", "query": "…", "stage": "ai_exposure", "asset_type": "blog", "reason": "…"}]},
       "pdp": {"issues": ["wrong_specs"], "actions": [{"type": "raise_priority", "asset_id": "sku-01", "to": "P0"}]},
       "conversion": {"issues": [], "actions": []}
     }
   }
   ```
4. **合并进矩阵**：geo-content-plan 重跑时读取 `reflow_patch.json`：`add_item` 新增 item、`raise_priority/lower_priority` 调 P、`fix_brief` 改 Brief 字段；打补丁后自检规则照旧，补丁应用后把该补丁标记 `applied: true`（不重复应用）。
5. **只重跑受影响层**：按补丁落在哪层，用 `selected_stages` 增量重跑，不重写其它层。

## 闭环判定
- 每层以 `research/sampling.json` 的对应基线指标对比：`ai_exposure` 看品牌提及率、`pdp` 看商品卡/描述准确度、`conversion` 看转化信号占比。
- 达标（达到客户确认的目标值）该层关闭；连续两轮诊断无变化则该层标 `stuck`，停止空转并升级人工介入。
