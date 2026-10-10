# 机械质检清单（N8 结果合并摘要）

来源：N8 结果合并（mechanical_check 机械检查 + LLM 自评合并为 quality_score）。

## 标题检查
- 禁止占位符泄漏：[____]、[待补充]、{keyword}、{time}、{persona}
- 禁止营销词
- 禁止以冒号/逗号结尾（疑似截断）；禁止结尾半截词（如「逻辑全」「全：」）
- 旧版长度 20-28 字符规则已禁用，不执行

## 正文检查
- 禁止 `**` 残留
- 禁止占位符泄漏、价格信息（如 `\d+元起`）
- 禁止内部骨架标注：「全文目标字数」「约 X 字」「approx_words」
- 禁止软广免责声明（「客观科普」与「本文」同现）
- 禁止内部标签：「本篇切入角度」「本篇开篇类型」「铺垫段：」
- 禁止 CTA 转化话术：立即购买 / 立即预约 / 加微信 / 扫码关注
- 禁止英文绝对化营销词：best ever / #1 / no.1 / revolutionary / world's best / ultimate / unbeatable / perfect choice / top-rated / top ranked
- 问句数量 ≥2（疑似词包问句未覆盖）
- 奖项/资质表述核证：「颁发」「评选出」「荣获」「年度…奖」「最佳…奖」等必须与画像核证结果比对

## 合并逻辑
- 机械检查问题（issues）与 LLM 自评（llm_review）合并计算 quality_score
- 输出最终文章 JSON（title / content / description / tags / self_review / quality_score）
