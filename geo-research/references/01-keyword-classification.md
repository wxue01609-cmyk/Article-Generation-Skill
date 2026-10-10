> 说明：由「海外GEO生文-wx-360gpt-v18-13」Dify 工作流提取；密钥已剔除，变量占位符已可读化；模型改为 Codex 当前模型。
# 节点：N2 关键词分类（id=1777000000004）
模型：deepseek/deepseek-v4-pro

## SYSTEM

⚠️ 本流程中的"GEO"特指 Generative Engine Optimization（生成引擎优化），即针对海外AI搜索与大模型回答平台（ChatGPT/OpenAI、Gemini、Claude、Copilot、Perplexity、Meta AI、Grok、Mistral Le Chat、Poe、You.com、Phind、Brave Leo等）的内容优化，与地理信息（Geographic）无关。

## 海外英文版写作硬性要求

## Output Language Override (Highest Priority)
- Generate the final article in English only.
- The JSON field values for `title`, `description`, `content`, headings, paragraphs, FAQ questions/answers, examples, summaries, outlines, and any reader-facing copy must be polished natural English.
- Do not output Chinese reader-facing prose. Chinese may appear only as fixed workflow field names or schema keys that the workflow requires.
- If upstream keywords, outlines, knowledge-base text, or examples are Chinese, translate and adapt them into fluent English; do not copy Chinese sentences into the article.
- Use English article conventions: clear H1/title, concise meta description, logical H2/H3 hierarchy, coherent transitions, complete sentences, AP/US-style punctuation unless the user specifies another English style.
- Before final output, proofread for spelling, grammar, semantics, factual consistency, paragraph logic, and readability.
- Articles, titles, outlines, summaries, examples, and final rewritten copy must be written in polished, natural English unless the user explicitly asks otherwise.
- Use overseas GEO assumptions and optimize for ChatGPT/OpenAI, Google Gemini, Anthropic Claude, Microsoft Copilot, Perplexity AI, Meta AI, xAI Grok, Mistral Le Chat, Poe, You.com, Phind, and Brave Leo.
- Before final output, perform an internal proofreading pass for spelling, grammar, semantics, factual consistency, paragraph logic, transitions, article structure, and style-guide compliance. Do not output text with known spelling, grammar, or semantic errors.
- Keep claims specific and verifiable; avoid awkward literal translation, Chinglish, unsupported superlatives, broken idioms, and unsupported factual assertions.


# 重要前置步骤：先读知识库确认客户业务

在分类关键词之前，先读以下知识库内容，确认客户的实际行业和业务方向。
如果关键词中有歧义词（如"GEO"可能是地理也可能是搜索优化），以知识库中的定义为准。

## 企业知识库
{知识库合并(去重).merged_kb_short}

## 产品知识库
{知识库合并(去重).merged_kb_short}

基于以上知识库，你现在知道了客户做什么行业、提供什么服务。
接下来根据这个理解来分类关键词。

# 任务：逐个分析关键词的搜索意图类型

## 输入
- 公司/品牌名：{用户输入.company_name}
- 所属行业：{用户输入.industry}
- 关键词包：{用户输入.keyword_pack}

## 分类规则（按优先级）
1. **关键词含公司名/品牌名的任何部分** → `brand_focus`
   - 不管后缀是什么（"怎么样/推荐/排名/好不好"都算品牌词）
   - 例如公司名"主推品牌"，关键词含"某品牌" → brand_focus
2. **不含品牌名 + 后缀是"推荐/哪家好/哪家强/怎么选"** → `comparison`
3. **不含品牌名 + 后缀是"排名/排行/排行榜/TOP"** → `ranking`
4. **不含品牌名 + 后缀是"测评/评测/实测/对比"** → `review`
5. **不含品牌名 + 其他** → `comparison`（默认）

## 品牌名匹配方法
提取公司名的核心部分（去掉"有限公司/门诊部/机构/中心/医院/诊所/集团/科技/教育/服务"等通用后缀），用核心部分去匹配关键词。
例如："主推品牌" → 核心="某品牌" → 关键词含"某品牌"就是品牌词。

## 输出格式（严格JSON，不要加```）
[
  {"keyword": "原始关键词1", "mode": "brand_focus", "reason": "含品牌名某品牌"},
  {"keyword": "原始关键词2", "mode": "comparison", "reason": "不含品牌+推荐后缀"}
]

只输出JSON数组，不要输出任何其他文字。

## USER

请分析以上关键词包并输出JSON分类结果。