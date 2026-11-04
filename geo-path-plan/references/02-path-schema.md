# path_plan.json Schema

```json
{
  "version": "1.0",
  "generated_at": "2026-11-04 20:00:00",
  "brand": "Botslab",
  "model": "G980H",
  "summary": {
    "total_queries": 12,
    "by_stage": {"ai_exposure": 6, "pdp": 4, "conversion": 2},
    "by_stage_pair": {"ai_exposure>pdp": 3, "pdp>conversion": 2},
    "unmapped": 1
  },
  "items": [
    {
      "query": "best robot vacuum for pet hair",
      "topic": "宠物毛发清洁",
      "stage": "ai_exposure",
      "secondary_stage": "pdp",
      "signals": ["best"],
      "confidence": 0.95,
      "share_with": ["best robot vacuum 2026"],
      "reason": "泛需求榜单型，先在博客/评测层取得提及，详情页带一句与内链",
      "force_reassign": false
    }
  ],
  "unmapped": [
    {"query": "…", "reason": "no_signal"}
  ],
  "risk_notes": []
}
```

## 字段约束
- `stage` 只能取：`ai_exposure` / `pdp` / `conversion`
- `secondary_stage`：同上三值之一或 `null`；**不得等于 `stage`**
- `signals`：≥1 条，必须是 query 中真实出现的词或结构（禁止编造）
- `confidence`：0-1，`<0.70` 视为弱判，需在 reason 说明
- `share_with`：与哪些 query 可共享同一篇资产（同层同主题才可合并），无则空数组
- `force_reassign`：`asset_types` 在本层无可用类型时为 `true`，并在 `suggestion` 给出可落位类型
- `summary.by_stage` 三项之和 + `unmapped` 数 = `total_queries`
- JSON 必须闭合可被 `json.load` 解析；不要用 markdown 代码块包裹，不要写注释

## 与其它产物的关系
- **上游**：`research/sampling.json` 的 `summary.by_stage` 用于校准（不强制改标）
- **下游**：`geo-content-plan` 读本文件，把 `stage` / `secondary_stage` 写进 `plan/content_matrix.json` 的对应 item；本文件不产出资产、不写 Brief
