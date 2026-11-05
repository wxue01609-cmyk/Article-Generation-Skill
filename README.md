# Article-Generation-Skill（海外 GEO 生文 / 内容建设）

用于生成面向海外 AI 平台（ChatGPT/OpenAI、Gemini、Perplexity 等）被检索引用的 GEO 英文内容。
本仓库是**唯一规则源**：本地平台与青蛙平台都从这里同步，不允许任何一端手写副本。

## 三端同源机制（重要）

| 端 | 规则来源 | 说明 |
| --- | --- | --- |
| GitHub（本仓库） | 唯一源 | 所有 `geo-*/SKILL.md` + `references/` 改这里 |
| 本地 `~/.codex/skills` | 本仓库同步副本 | 本地平台直接读取，必须与仓库逐字节一致 |
| 青蛙上传包 | **自动构建产物** | `python3 build/build_frog_package.py` 从本仓库生成，提示词内联全部规则全文 |

工作流（改规则只走这一条）：

```bash
# 1. 改本仓库的 SKILL.md / references
# 2. 同步到本地平台
cp -R geo-* ~/.codex/skills/
# 3. 重新生成青蛙包（自动内联规则，禁止手改包内文件）
python3 build/build_frog_package.py
# 4. 发布前必须校验三端一致（不一致直接 FAIL）
python3 build/parity_check.py
```

`parity_check.py` 会校验：仓库与本地逐字节一致、青蛙提示词逐字包含每个规则文件、
分层分类器（本地 `sample_by_stage.py` vs 青蛙 `geo-sample.py`）在固定词包上输出完全一致、
agent.json 注册 13 技能且引用齐全。

## 组成

### 内容建设链路（13 个 skill，按执行顺序）

| # | Skill | 阶段 | 核心作用 |
| --- | --- | --- | --- |
| 0 | geo-doc-parse | 运行前 | 解析上传文档，回填词包/企业/产品资料，不改写事实 |
| 1 | geo-layered-sampling | 分层基线 | 按转化路径分层采样，产出 query→stage 与平台×层基线 |
| 2 | geo-path-plan | 转化路径编排 | 每条 query 1 主节点 + 1 次节点，行业只作素材 |
| 3 | geo-content-plan | 方案 | 意图分类、渠道落位、资产矩阵与逐项 Brief（只做方案） |
| 4 | geo-evidence | 证据账本 | 逐条摘录建立 claim 账本，证据不足的改动阻断 |
| 5 | geo-source-fetch | 页面抓取 | 商品页结构化快照（JSON-LD/参数表/价格/图片） |
| 6 | geo-content-write | 成稿 | 按 Brief 写完整可发布 HTML；SKU 走改造 JSON |
| 7 | geo-sku-rewrite | SKU 改造 | 1:1 复刻原页面只改文字，输出改造 JSON |
| 8 | geo-pdp | 商品数据交付 | PDP + OpenAI/Google feed + Product JSON-LD 一致性 |
| 9 | geo-asset-render | 渲染 | 整页 / 模块片段 / 改前改后对比页，全内联样式 |
| 10 | geo-translate | 中英对照 | 保留结构翻译，供内部审阅 |
| 11 | geo-polish | 全链路质检 | 按 stage 跑事实/证据/可提取/渠道/分发五关 |
| 12 | geo-diagnose | 诊断回流 | 按问题族统计提及/排位/份额/商品卡，判定失败层 |

### 单篇生文链路（4 个 skill，旧线保留）

| Skill | 阶段 |
| --- | --- |
| geo-research | 调研 + 分层采样 |
| geo-plan | 文章计划与大纲 |
| geo-write | 按大纲写作 |
| geo-polish（批量模式） | 清洗、链接校验、机械质检 |

任务类型是「单篇生文」时走这 4 个；是「内容建设方案」时走上面 13 个。两条线互不影响。

## 输入变量

keyword_pack（词包）、company_name、industry、company_intro、core_qualifications、awards、advantages、product_info、task_name、task_description、publish_media、article_type、article_count、article_style、article_length、known_competitors、engines、ent_dataset_id、prod_dataset_id、zhishi_custom_id（后三个为原 Dify 知识库 ID，本环境中可用文件/文本资料代替）。

内容建设模式额外输入：source_urls（待改造页面 URL，最多 5 个）、source_text（URL 抓取失败时手动粘贴的页面正文）、query 词包、知识库资料。

## 与原工作流的差异

- 模型不再使用 360GPT（deepseek），由 Codex 当前模型执行；主线不依赖任何外部 API（可选配置直连 ChatGPT 接口，仅用于「AI 问答结构提取」，见下文）。
- 联网搜索（竞品检索、链接校验）改用 Codex 内置 web_search 工具，规则与输出格式不变。
- 新增「AI 问答结构提取」步骤：收到词包后优先直接向 ChatGPT 对话接口提问拿回答（需在环境变量配置密钥），提取竞品文章内容结构方向供规划与写作参考；接口未配置时自动退回联网检索兜底；结构方向只作参考，原生文规则优先，不得机械照搬。
- 原 YAML 中内嵌的两个 API 密钥已全部剔除；**请勿把原始 yml/任何含密钥的文件提交到公开仓库**，并建议在 360 后台重置旧密钥。
- 知识库检索节点（企业/产品/营销）在无对应接口时，直接读取用户提供的文件或文本。

## 安装

```bash
# 方式一：本地使用，把全部 skill 文件夹放入 skills 目录
cp -R geo-* ~/.codex/skills/

# 方式二：装好后在 Codex 中直接说"海外GEO生文"或"海外内容建设"，对应 skill 会按需接力
```

## 可选：直连 ChatGPT 接口配置
- 环境变量与验证方式见 [geo-research/references/10-chatgpt-api-config.md](geo-research/references/10-chatgpt-api-config.md)。
- 密钥只放在运行环境中（CHATGPT_API_KEY），严禁写入仓库；未配置时「AI 问答结构提取」自动退回联网检索兜底。

## 说明

每个 skill 的 `SKILL.md` 是入口（何时使用、流程、交接格式），`references/` 是完整规则。青蛙包由 `build/build_frog_package.py` 自动把 `SKILL.md` 与 `references/` 全文内联成 `prompts/*.md`，因此三端规则一致；`build/parity_check.py` 是发布前的硬性校验。
