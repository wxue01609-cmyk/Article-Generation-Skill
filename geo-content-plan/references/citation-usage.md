# 引用内容参考（reference_citations）使用规则

来源：`research/citations.json`（平台分层采样时抓取的「AI 实际引用的第三方页面」摘要：title / headings / excerpt）。
用途：让方案知道**AI 正在引用什么样的内容**——结构骨架、证据点、组织方式，从而把文章写得更容易被引用。

## 什么时候用
- `research/citations.json` 存在且有 `status=ok` 的条目时，把与 item `stage` 同层的引用条目写进该 item 的 `reference_citations`。
- 无引用文件 / 全部抓取失败：该项不写 `reference_citations`，不阻塞方案。
- 已在 `sampling.json` 的 `citations` 里带摘要时，与文件内容一致，直接使用。

## 怎么用（三条铁律）
1. **只借鉴结构与证据点**：标题层级怎么组织（如"先对比维度再给结论"）、用什么证据类型（规格表/价格/认证/政策）可以从引用页学习；对应写成 Brief 的 `outline` 与 `key_points` 的参考注记。
2. **禁止照抄**：引用页的句子、段落、列表原文一律不得进入正文或 Brief；只允许转述结构与思路。
3. **官网资产不受污染**：引用页属于竞品/第三方时，官网资产（blog/landing/category/sku/faq）的 Brief 仍不得出现竞品品牌名——参考结构可以，点名不行；对比/review 类只能落三方媒体。

## 写入格式（Brief 内）
```json
"reference_citations": [
  {"title": "…", "url": "https://…", "domain": "…", "headings": ["h1 …", "h2 …"], "excerpt": "前 200 字"}
]
```
- 与该项 `stage` 不同层的引用条目不写进来（层级错配会让文章发错层）。
- `excerpt` 只保存 200 字摘要作为上下文提示，正文阶段仍然禁止引用原文。
