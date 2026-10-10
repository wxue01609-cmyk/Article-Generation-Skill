---
name: geo-write
description: 海外 GEO 生文流水线第三阶段（写作）。根据 geo-plan 的大纲批量生成面向海外 AI 平台的英文文章（标准版/无营销知识库版/品牌版），输出完整 JSON，供 geo-polish 质检。当需要按已有大纲把 GEO 文章写成英文 HTML 正文时使用。
---

# GEO 写作（geo-write）

来源：Dify 工作流「海外GEO生文-wx-360gpt-v18-13」第三阶段（迭代1-标准版：N7-1标准版 / 7-1生文-无营销知识库ID；迭代3-品牌文章：N7-品牌版）。

## 任务
读取上游大纲，严格按大纲给出的文章标题、章节层级、段落顺序和要求生成英文 HTML 文章，输出最终 JSON 数组。大纲的 content_brief 是「写作方向」不是正文，必须用自己的语言展开，禁止照搬。

## 三条写作路径
- 有营销知识库 → [references/02-standard-writer.md](references/02-standard-writer.md)（N7-1 标准版）
- 无营销知识库 → [references/03-standard-writer-no-kb.md](references/03-standard-writer-no-kb.md)（7-1 生文-无营销知识库ID）
- 品牌文（brand_focus）→ [references/04-brand-writer.md](references/04-brand-writer.md)（N7-品牌版：标题可含品牌名，不写竞品）

## 全局输出控制（最高优先级，覆盖下方所有字数要求）
- 思考预算：内部推理 ≤3000 token，禁止反复推演、不写草稿再重写，直接按大纲一次性输出最终 JSON。
- 输出必须是完整闭合的 JSON 对象，最外层 `}` 必须出现；接近输出上限立即收尾闭合——宁可少写也不能截断。
- 字数档位：长文 = 1000-1500 English words；社交渠道 = ≤350（硬上限，严禁任何链接）；问答社区 = 300-450；默认/标准 = 700-900。
- 社交/社区帖子模式（发布媒体含 reddit/论坛/社区/问答/贴吧/X/社交等时，与文章化要求冲突一律以本条为准）：
  - 禁止 h1-h6 / TL;DR / 表格 / 加粗小标题；content 用 3-5 个自然段（p 包裹）口语化写成
  - 允许只讲透 1-2 个点、允许思维跳跃；全文保留 2-3 处不确定表达（I might be reading that wrong. 等）
  - 结尾必须是具体的真实经历提问（Did you end up buying twice? 等），禁止 CTA、禁止 What do you think?
  - 全文 0 链接、0 表格、0 小标题

## 渠道规则（写作前必须先命中渠道）
按 publish_media 命中渠道（blog/qna/pr/social/linkedin/x/facebook/ecommerce/help/ads），执行该渠道的定位、风格、结构、竞品限制、链接与 AI 收录要点；渠道规则与提示词其他要求冲突时以渠道规则为准。完整规则见 [references/01-channel-rules.md](references/01-channel-rules.md)。

## 输出语言与质量红线
- Output Language Override：全文英文，读者可见内容（title/description/content/标题/FAQ/示例）必须为自然英文；中文只允许出现在固定字段名。
- 真实性（P0，最高优先级）：事实只能来自知识库/画像/大纲，禁止编造；「待核验」内容必须标注。
- 竞品篇幅（P1）：对比文本品必须在竞品中第一个展示，竞品只允许一行点评表（官网渠道完全禁止竞品）。
- 品牌词强化（P1）：主推品牌与核心卖点在标题/首屏/结论/H2 持续出现。
- 禁用绝对化营销词（P1）：best/#1/revolutionary/ultimate 等，以及「最」「第一」类表述。
- 词包问句完整保留（P1）：原问句真实覆盖，正文问句不能丢。
- 事实溯源：输出 fact_sources 与 self_review（≤300 字逐项核对，涉及合规项必须摘录正文原话作证据）。

## 输出与交接（传给 geo-polish）
每篇文章 JSON：title / content（HTML）/ description / tags / self_review / fact_sources；注意文章 JSON 必须完整闭合。
