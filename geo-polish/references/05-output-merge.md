# 输出合并与截断容错（articles-merge 摘要）

来源：articles-merge 合并输出。

- 聚合上游各迭代（标准版文章 + 品牌文章等）为 all_articles
- 截断容错 `_rescue_from_broken`：当文章 JSON 未闭合（截断）时，用正则提取 title / content / description 字段兜底，self_review 标记为「[截断] JSON 未闭合，已尽力提取已生成部分」
- 非对象输入（纯文本等）直接包成 {title: "", content: <文本>, tags: [], description: "", self_review: ""}
- 输出：`{"all_articles": [...], "compliance_mode": "standard"}`
