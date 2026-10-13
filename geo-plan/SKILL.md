---
name: geo-plan
description: 海外 GEO 生文流水线第二阶段（规划）。基于 geo-research 的画像与竞品，构建文章计划（结构 DNA/标题候选/表达变体）并生成逐篇大纲（标准版/品牌版），供 geo-write 写作。当需要为海外 AI 平台文章批量规划结构、标题、字数档位与大纲时使用。
---

# GEO 规划（geo-plan）

来源：Dify 工作流「海外GEO生文-wx-360gpt-v18-13」第二阶段（N5 构建迭代计划 → 合规分流 → 维度评分 5x5 → N6-1 大纲策略规划 → N6-2 大纲生成 → N6-split 大纲拆分 → N6-per单篇大纲(brand)）。

## 输入（来自 geo-research 的交接 + 用户输入）
- GEO 画像、竞品清单、知识库摘要、关键词分类（keyword_modes / comparison_count）、AI 问答结构方向
- 用户输入：article_count、article_type、article_style、article_length、publish_media、task_name 等

## 执行流程

### 步骤 1 构建迭代计划（N5 / N5-A）
- 先判定渠道与输出语言要求；按 article_count 为每篇文章分配关键词，并生成「结构 DNA」（结构 | 分组 | 开篇 | 视角 | 标题层级）+ 2-3 个表达变体候选 + 标题候选池。
- 结构类型由 article_type 映射（对比排名类 / 性能评测类 / 经验分享类 / 知识科普类 / 新闻报道类 / 自我介绍类），每种结构有对应表达变体池、评分制变体池、排名方式池、品牌词模式池。
- 标题时间词按当前真实日期动态生成（年/季度/半年），不写死；数量词只用小范围，避免标题说 TOP10 但实际只有 4 家竞品；[____] 占位留给大纲阶段补创意。
- 结构参考输入：用 geo-research 的「AI 问答结构方向」补充开篇切入、分节方式、对比维度与 FAQ 形式候选，与上述结构类型映射的候选池合并择优；AI 方向只影响单篇结构细节，不改变结构类型映射与表达变体池本身，且同批文章必须保持结构差异化。
- 规则细节见 [references/01-plan-building.md](references/01-plan-building.md)。

### 步骤 2 合规分流
- content_mode = brand_focus → 品牌组（文章不使用竞品，competitor_names 置空）
- compliance_mode ∈ {medical, financial} → 合规组
- 其余 → 标准组

### 步骤 3 品牌文：维度评分 + 单篇大纲
- 品牌文章先做 5×5 维度评分（目标平台拆解、Top5 维度解读、细分分类建议）→ [references/02-score-5x5.md](references/02-score-5x5.md)。
- 再按 N6-per单篇大纲(brand)：把 N5 的结构 DNA「翻译」成具体大纲（Step 1 解读 structure_dna → Step 2 选变体 → Step 3 决定排名/对比位置 → Step 3.5 知识库覆盖度校验 → Step 4 用知识库填 content_brief）→ [references/04-outline-brand.md](references/04-outline-brand.md)。

### 步骤 4 标准文：N6-1 大纲策略规划（全部）+ 生成与拆分
- N6-1 批量规划全部文章的大纲，含 5×5 细分表覆盖、每段 approx_words、章节结构、FAQ 规划 → [references/03-outline-strategy.md](references/03-outline-strategy.md)。
- N6-2 生成大纲（含 LLM 格式错误预修复与截断容错）→ N6-split 拆分（字段白名单过滤，确保每篇必要字段齐全）→ 规则见 [references/05-outline-code.md](references/05-outline-code.md)。

## 档位规则（全局最高优先级，覆盖下方所有字数表述）
- 长文/长文档/长文章 → 1000-1500 English words
- 社交渠道（TikTok/YouTube/Instagram/Twitter/X/Facebook 等）→ ≤350 English words，硬上限，严禁任何链接
- 问答社区（reddit/论坛/社区/问答/贴吧）→ 300-450 English words（约 0.5 倍折算）
- 未填或标准 → 700-900 English words
- 大纲各段「约 X words」之和必须落在所选档位区间。
- 每篇大纲必须与文章类型匹配：官网/博客渠道不规划竞品内容；TL;DR 整批最多 1 篇（仅第 1 篇可用）；FAQ 问题用词包原问句。

## 大纲质量红线（强制）
- 词包中的每个疑问句（含 ?）必须分配 FAQ 条目或正文 H2/H3，原问句原样保留，禁止改写或遗漏。
- 每篇标题必须包含该篇主关键词或其自然变体，且与词包原文差异化（换措辞/换问法/换切入点）；年份只能用当前年份或「最新/近期」等通用词；🚫 标题默认不出现品牌/客户名，除非任务输入明确要求标题带品牌名。
- 标题语言跟随任务字段 article_language（缺省英文）：英文按 8-14 words，其他语言按同等信息量自然表达（不套用英文词数硬限）。
- 标题与正文一致，禁止主题漂移；排名/对比类竞品统一一行点评表（官网渠道作废，不出现竞品）。
- 严禁规划不存在的功能/规格（以画像核证结果为准，「待核验」卖点不得进入正文规划）。

## 输出与交接（传给 geo-write）
1. 每篇文章计划：structure_dna、presentation_candidates、content_mode、compliance_mode、competitor_names 等
2. 每篇大纲 JSON：title、content_brief、章节（覆盖意图词 / 5x5 标签 / 段落概要 / 二级要点 / approx_words）、FAQ 主题
3. 渠道规则 key（blog/qna/pr/social/linkedin/x/facebook/ecommerce/help/ads）
