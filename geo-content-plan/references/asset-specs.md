# 各资产 Brief 骨架（方案阶段只写结构与要点）

## blog 官网博客
`outline`：H1 → 直接结论段（≤120 词）→ 4-7 个 H2（问题/判断标准/参数/场景/边界）→ FAQ（原问句 3-5 条）→ 结论。
`key_points`：每 H2 一句核心结论；`proof_points`：可核验参数/认证/来源；`cta`：单一软 CTA。
禁止：竞品名、TL;DR（整批最多 1 篇）、作者简介。

## category 官网类目页
`outline`：类目导语（这是什么/适合谁）→ 选购维度 → 子类目分块（3-6 个）→ 自家产品对比表（只列自家型号）→ 场景 → FAQ → 内链。
`key_points`：每个子类目一句适用边界；`proof_points`：参数口径/认证。

## landing 官网落地页
`outline`：Hero（H1/副标题/证据条/主 CTA）→ 痛点 → 解决方案 → 3 个收益模块 → 工作方式 → 规格/证据 → 使用场景 → 异议处理 → 真实背书（无则不写）→ FAQ → 结尾 CTA。
`key_points`：每屏一句转化主张；`cta`：只保留一个主 CTA；`word_count` 300-700。

## sku 官网产品/SKU 页
`outline`：标题公式 → 5 条卖点（利益+证据）→ 描述（3 段）→ 参数表 → 包装/兼容 → 适用/不适用 → FAQ → schema Product。
`key_points`：型号差异、核心规格、兼容性；`proof_points`：参数来源，未核验标 `待核验`。
`title` 公式：品牌 + 型号 + 核心规格 + 场景（≤70 字符）。

**存在待改造页面时（item 带 `source_page`）**：
- `outline` 改为改造清单：标题改写方向 → 核心答案段要点 → 卖点改写 → 参数表来源（页面表格 / JSON-LD / 图片）→ 适用与不适用 → FAQ 原问句族 → 购买信息与品牌方身份 → Product schema。
- `key_points` 写「改什么、为什么」，不写改后全文；`proof_points` 只列页面里能核实到的参数。
- 把 `source_issues` 里的每条问题对应到一个改造模块，写进 `outline` 或 `risk_notes`。
- `word_count` 按改后页面估算；`internal_links` 不得指向该页面自身。

## faq 帮助中心
`outline`：5-8 个问题（原问句）→ 每个直答 40-60 词 → 步骤/边界 → 相关链接。
`key_points`：每问一句答案；`proof_points`：手册/参数来源；schema FAQPage。

## thirdparty_pr 三方 PR
`outline`：标题（品牌+新闻点）→ 5W 导语 → 3 个事实段 → 官方引语 → Boilerplate → 媒体适配说明。
`key_points`：新闻点、差异化、市场意义；`proof_points`：数据/奖项/覆盖；`cta` 不写促销。

## thirdparty_review 三方评测/对比
`outline`：披露声明 → 测试/评估方法 → 维度对比表 → 分场景结论（适合谁/不适合谁）→ 局限性 → FAQ。
`key_points`：每个维度一句结论；`proof_points`：测试方法/来源；`risk_notes`：必须写披露与利益关系。

## qna 社区问答
`outline`：问题式标题 → 真实场景与约束 → 已尝试方案 → 2-5 个具体判断问题 → 邀请经验。
`key_points`：场景细节、约束、决策问题；`cta` 不写；全文 0 链接。

## social 社交帖
`outline`：钩子 → 1-3 个要点 → 结尾问题/CTA → 话题标签。
`word_count` ≤150；平台规则优先。

## ecommerce 电商 Listing
`outline`：标题（≤200 字符）→ 5 条 bullet（利益+参数）→ 描述 → 后台关键词 → A+ 模块 → 图片脚本。
`key_points`：主关键词、变体差异、合规声明。

## 通用
- `title` 必须具体，不用 "Ultimate Guide" 等绝对化词。
- `angle` 一句话说明与现有内容的差异，避免同质化。
- `internal_links` 给锚文本 + 目标路径；目标不存在时写建议新建。
- `dependencies` 写前置资产（如 SKU 页先于落地页）。
