---
name: geo-research
description: 海外 GEO 生文流水线第一阶段（调研）。输入词包、企业/产品资料与知识库，输出关键词意图分类、GEO 画像与已验证竞品清单，供 geo-plan 规划文章。当用户要求面向海外 AI 平台（GEO）批量生成文章、先做关键词分类/用户画像/竞品调研时使用。
---

# GEO 调研（geo-research）

来源：Dify 工作流「海外GEO生文-wx-360gpt-v18-13」第一阶段（N1 代码预处理 → 知识库检索 → N2 关键词分类 → N4 GEO 画像分析 → N3na 竞品研究）。本 skill 只做分析和数据准备，不写文章。

## 输入变量（全流水线共用）

| 变量 | 含义 | 必填 |
| --- | --- | --- |
| keyword_pack | 词包（段落） | ✅ |
| company_name | 企业名称 | ✅ |
| industry | 行业 | ✅ |
| ent_dataset_id / prod_dataset_id | 企业/产品知识库 ID | ✅ |
| task_name | 任务名 | ✅ |
| article_count | 文章数量 | ✅ |
| company_intro / core_qualifications / awards / advantages | 企业简介/核心资质/获奖/优势 | 选填 |
| product_info | 产品信息 | 选填 |
| task_description | 任务描述 | 选填 |
| publish_media | 发布媒体（决定渠道规则） | 选填 |
| article_type / article_style / article_length | 文章类型/风格/长度档位 | 选填 |
| known_competitors | 已知竞品（客户填写时一律以客户为准） | 选填 |
| engines | 目标海外 AI 平台 | 选填 |
| zhishi_custom_id | 营销知识库 ID（可选知识源） | 选填 |

知识库检索对应原工作流的 360 RAG 接口；本环境中若资料以文件/文本提供，直接读取文件内容代替检索。

## 执行流程

### 步骤 1 预处理与知识库合并
- 输入归一化（article_type 兼容"对比排名/对比排名类"等写法）、提取地域、判定 content_mode（brand_focus / comparison / experience / knowledge / auto）。
- 检索企业知识库、产品知识库、营销知识库，并做一次企业资料联网搜索；全部按标签合并去重成一份结构化摘要。
- content_mode 判定：公司名出现在词包或品牌意图信号占比 ≥30% → brand_focus；对比排名类/性能评测类 → comparison；经验分享类 → experience；知识科普类/新闻报道类 → knowledge；未识别 → auto。
- 规则细节见 [references/08-preprocess-and-kb.md](references/08-preprocess-and-kb.md)。

### 步骤 2 关键词分类
- 逐个分析词包关键词的搜索意图类型：brand_focus（品牌词）/ comparison（对比词）/ ranking / review。
- 统计 classification_count / brand_count / comparison_count；comparison_count=0 时后续跳过竞品流程。
- 提示词原文见 [references/01-keyword-classification.md](references/01-keyword-classification.md)。

### 步骤 3 AI 问答结构提取
- 触发条件：收到 keyword_pack 即执行，无其他前置；词包为空或无有效关键词时，输出空结构方向并注明原因。
- 用词包关键词（带上行业/地区上下文）构造自然问题，优先直接调用 ChatGPT 对话接口提问并拿回答（scripts/ask_chatgpt.py，配置见 [references/10-chatgpt-api-config.md](references/10-chatgpt-api-config.md)）；接口未配置或调用失败时，退回内置 web_search 联网检索 AI 平台公开回答，并在输出注明；海外市场用英文或当地语言提问。
- 提取「竞品文章内容结构方向」：AI 回答的开头切入、分节方式、对比维度、清单/FAQ 形式、结尾方式，以及被引用文章的结构方向（标题层级/段落组织/切入点）。
- 结构方向只作参考，不是固定模板：与原生文规则冲突时以原生文规则为准，并在输出中说明未采纳的点。
- 规则细节见 [references/09-ai-answer-structure.md](references/09-ai-answer-structure.md)。

### 步骤 4 GEO 画像分析（8 步，防幻觉核心）
严格按顺序执行 8 步：核心产品提炼 → 关键数据点提取 → 行业参考数据锁定 → 用户画像构建 → 搜索场景与询问问题 → 材质性能参数提取 → 关键词意图分析与文章类型权重建议。
- 数据优先级铁律：营销知识库 > 客户输入 > 已有知识，严禁编造；关键数据点必须来自知识库，下游文章原样引用。
- 提示词原文见 [references/02-geo-profile.md](references/02-geo-profile.md)。

### 步骤 5 竞品研究
1. 离线候选：凭训练记忆中真实存在的同行生成 5-8 家候选（宁可少列、绝不编造；客户已填已知竞品时以客户为准；必须同行业、同梯队、同业务模式）→ [references/03-competitor-offline.md](references/03-competitor-offline.md)。
2. 联网搜索：用内置 web_search 逐条核实候选与证据 URL（原工作流调 360 API，规则不变）→ [references/04-competitor-search.md](references/04-competitor-search.md)。
3. 双路合并与去重：离线候选 + 联网结果按名称归一化合并，信息完整度择优，排序优先级 = 客户白名单 > 双路命中 > 仅联网 > 仅离线 → [references/06-competitor-dedupe.md](references/06-competitor-dedupe.md)。
4. 单候选逐个联网校验，确认机构真实存在 → [references/05-competitor-verify.md](references/05-competitor-verify.md)。
5. 竞品详情：按维度问卷逐一回忆每个竞品真实信息，供下游生文引用 → [references/07-competitor-details.md](references/07-competitor-details.md)。

## 硬性约束
- 输出语言：英文版硬性要求（Output Language Override），交付给下游的正文相关材料必须为自然英文；分析类中间产物按各提示词原文要求执行。
- 防幻觉：所有数据点必须可溯源（知识库/搜索/客户输入），标注置信度；搜索结果优先于训练记忆。
- 竞品铁律：不编造机构、不跳出同梯队、不把客户本身列入竞品、证据 URL 必须真实。
- AI 问答结构方向只作参考：AI 回答与被引用文章的内容、URL 必须真实来自本次接口调用或联网检索，严禁编造；结构方向严禁覆盖数据优先级铁律，与原生文规则冲突时以原生文规则为准。

## 输出与交接（传给 geo-plan）
1. 关键词分类结果（keyword_modes + comparison_count，JSON）
2. AI 问答结构方向（词包问题 → AI 回答要点 → 被引用竞品文章的结构方向 + 冲突标注，JSON）
3. GEO 画像（8 步结果：核心产品、关键数据点、行业参考数据、用户画像、搜索场景与问题、材质性能参数、文章类型权重）
4. 已验证竞品名单（含置信度/证据 URL/核心业务/详情问卷）
5. 合并后的知识库摘要（企业 + 产品 + 营销）
6. 预处理产物：content_mode、region、task 描述等
