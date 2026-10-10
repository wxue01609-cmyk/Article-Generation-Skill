# 大纲生成与拆分的工程规则（代码节点摘要）

来源：N6-2 大纲生成、N6-split 大纲拆分、合规分流。

## N6-2 大纲生成
- 解析 N6-1 LLM 输出：先取主数组；主数组缺篇时，用「候选大纲 + 词包分配」拼出最小可用 item。
- LLM 格式错误预修复：
  - JS 风格字符串拼接（`"覆盖意图词 ["+"A"+","+"B"+"]"`）还原为数组
  - 已知常错的「键名+数组」字段粘连修复
  - 顶层数组缺 `]` 自动补齐
- 截断容错：整段修复失败则逐篇提取（跳到下一个 `{`）；循环清理尾部未完成的 key/value，直至结构完整。

## N6-split 大纲拆分
- 字段白名单过滤：仅保留大纲必要字段，章节内部同样白名单过滤。
- JSON 解析容错顺序：剥 markdown code block → 直接解析 → 定位最外层 `{}` → 正则提取关键字段片段（兼容新旧两种 key）。
- 确保必要字段存在（title / content_brief / 章节 / approx_words 等）。

## 合规分流
- content_mode = brand_focus → 品牌组，competitor_names 置空（品牌文不使用竞品）。
- compliance_mode ∈ {medical, financial} → 合规组。
- 其余 → 标准组。
- 输出 `standard_plans / compliance_plans / brand_plans` 三组。
