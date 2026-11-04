# 内容建设全链路质检 · 判定话术与检查项

按 stage 分单元执行；每个资产一个结果，每关给 `pass` / `warning` / `blocking`。

## 关卡 1 事实（Fact）
- 通过：正文每个具体数字（价格/参数/尺寸/评分/认证编号）、每条政策（退换/保修/物流）都能在 brief、知识库、`source/meta.json` 或证据账本中找到原文。
- warning：表述与技术参数从知识库推理而来但原文缺失（如"更安静"来自"30dB"），正文无矛盾。
- blocking：出现无法溯源的具体数字；价格与证据账本冲突；把抓取页缺失信息写成"无"（应写"页面未找到"或省略）。

## 关卡 2 证据（Evidence）
- SKU 改造：每个 `changes[i].after` 必须能追到 `geo-evidence` 账本条目（evidence_id）；`notes` 里的待确认项必须有对应输入框。
- 普通资产：每条 `proof_points` 需有来源标注（知识库 / 待核验）；`待核验` 必须保留标注，不得悄悄写成事实。
- blocking：改后出现账本中没有的属性；`待核验` 被当事实写。

## 关卡 3 可提取（Extractable）
- 首段 ≤120 词内给出结论（answer-first）；H2 可独立成句引用；有清单/表格可被 AI 摘取。
- SKU 页：Overview 段含"适用人群 + 核心卖点 + 购买建议"。
- blocking：首段绕圈子无结论，且全文无结构化要点。

## 关卡 4 渠道（Channel）
- 官网资产（blog/landing/category/sku/faq）：0 竞品品牌名、0 对比表、0 "A vs B"。
- 三方评测/对比：有披露声明；结论"不同需求→不同方案"。
- 社区问答：0 链接、0 促销、口语化、结尾真实问题。
- blocking：官网资产出现竞品名或对比表。

## 关卡 5 分发（Distribution）
- `asset_index.json` 每项的 `file` 在磁盘上存在；`stage_index.json` 的计数与 index 一致；`packs/<stage>/manifest.json` 与 index 对应。
- `word_count` 在 brief ±20%；FAQ 原问句保留。
- 所有站外 `<a>` 带 `target="_blank" rel="noopener"`；站内内链默认 target；无死链（可抽样验证）。
- blocking：索引与文件对不上；站外链接缺 `rel="noopener"`。

## 汇总
- `blocking` 清零该层才 `pass: true`；`warning` 写入 `asset_index.json` 的 `checks` 后放行。
- 输出 `polish_report.json`（见 SKILL.md），供增量重跑与 `geo-diagnose` 回流读取。
