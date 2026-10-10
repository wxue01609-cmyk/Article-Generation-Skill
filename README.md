# Article-Generation-Skill（海外 GEO 生文）

由 Dify 工作流「海外GEO生文-wx-360gpt-v18-13」迁移而来的 Codex skills 流水线，用于生成面向海外 AI 平台（ChatGPT/OpenAI、Gemini、Claude、Copilot、Perplexity、Meta AI、Grok、Mistral Le Chat、Poe、You.com、Phind、Brave Leo 等）被检索引用的 GEO（Generative Engine Optimization）英文内容。

## 组成（4 个 skill，按顺序接力）

| Skill | 阶段 | 输出 |
| --- | --- | --- |
| geo-research | 调研：预处理、知识库合并、关键词分类、AI 问答结构提取、GEO 画像（8 步）、竞品研究 | 画像 + 竞品清单 + AI 问答结构方向 + 知识库摘要 |
| geo-plan | 规划：文章计划（结构 DNA/标题候选）、合规分流、5×5 维度、逐篇大纲 | 计划 + 大纲 JSON |
| geo-write | 写作：标准版 / 无营销知识库版 / 品牌版，分渠道规则 | 文章 JSON（英文 HTML） |
| geo-polish | 质检：合并容错、违禁词清洗、链接校验替换、帖子兜底、机械质检 | 最终可发布文章 |

## 输入变量

keyword_pack（词包）、company_name、industry、company_intro、core_qualifications、awards、advantages、product_info、task_name、task_description、publish_media、article_type、article_count、article_style、article_length、known_competitors、engines、ent_dataset_id、prod_dataset_id、zhishi_custom_id（后三个为原 Dify 知识库 ID，本环境中可用文件/文本资料代替）。

## 与原工作流的差异

- 模型不再使用 360GPT（deepseek），由 Codex 当前模型执行；不依赖任何外部 API。
- 联网搜索（竞品检索、链接校验）改用 Codex 内置 web_search 工具，规则与输出格式不变。
- 新增「AI 问答结构提取」步骤：收到词包后先用关键词联网向 AI 平台提问，提取竞品文章内容结构方向供规划与写作参考；结构方向只作参考，原生文规则优先，不得机械照搬。
- 原 YAML 中内嵌的两个 API 密钥已全部剔除；**请勿把原始 yml/任何含密钥的文件提交到公开仓库**，并建议在 360 后台重置旧密钥。
- 知识库检索节点（企业/产品/营销）在无对应接口时，直接读取用户提供的文件或文本。

## 安装

```bash
# 方式一：本地使用，把 4 个文件夹放入 skills 目录
cp -r geo-research geo-plan geo-write geo-polish ~/.codex/skills/

# 方式二：装好后在 Codex 中直接说"海外GEO生文"，四个 skill 会按需接力
```

## 说明

每个 skill 的 `SKILL.md` 是入口（何时使用、流程、交接格式），`references/` 里是各节点的完整提示词原文或规则摘要。受提示词篇幅影响，代码节点的确定性逻辑以规则摘要形式保留，未原样移植全部 Python。
