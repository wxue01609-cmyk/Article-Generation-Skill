# 预处理与知识库规则（代码节点摘要）

来源：N1 代码预处理、1-1/1-2/1-3 知识库检索、联网搜索-企业产品资料、知识库合并(去重)、数据清洗代码、N2b 分类解析。

## N1 代码预处理
- 输入归一化：article_type 兼容「对比排名 / 对比排名类」等写法。
- RAG 查询构造：ent_rag_query = "{企业名} 企业简介 品牌荣誉 行业认证 服务优势"；prod_rag_query = "{核心锚点} 核心参数 产品亮点 服务优势 技术特点"。
- 合规模式：海外客户统一走 standard。
- 地域提取：内置海外城市/国家名单（中英文），按关键词包中最早出现 + 最长匹配提取 region。
- 内容模式判定 content_mode：
  - 品牌词检测（完整字面 / 去公司后缀核心名 / 品牌意图词占比 ≥30%）→ brand_focus；自我介绍类 → brand_focus
  - 对比排名类 / 性能评测类 → comparison；经验分享类 → experience；知识科普类 / 新闻报道类 → knowledge
  - 未识别 → auto（交给 N4 智能选型）
- needs_competitors = content_mode ∈ {comparison, experience, auto}。
- 已知竞品白名单：优先专门字段 known_competitors，读不到再从自由文本里提取。

## 知识库检索与合并
- 1-1 产品知识库：query = prod_rag_query，top_k = 5，score ≥ 0.7。
- 1-2 企业知识库：query = ent_rag_query，top_k = 5，score ≥ 0.7。
- 1-3 营销知识库（可选，zhishi_custom_id 存在时调用）。
- 联网搜索-企业产品资料：对企业资料做一次联网补充搜索后解析。
- 知识库合并(去重)：企业 + 产品 + 营销 + 公司简介/资质/奖项/优势，按标签去重拼接成结构化摘要（产品说明 / API 产品说明 / 客户人群 / 搜索意图 / 场景摘要 / 企业基础事实）。

## N2b 分类解析
- 解析 N2 输出的 JSON 数组，构成 keyword → mode 映射（brand_focus / comparison / ranking / review，非法值兜底为 comparison）。
- 输出 classification_count / brand_count / comparison_count，comparison_count 决定下游是否走竞品联网流程。
- 解析失败时返回空映射（全 0），不阻断流程。

## 数据清洗代码
- 清洗上游变量（知识库/搜索返回），剔除控制字符、非法引号与换行符，保证拼接进提示词/请求体时安全一致。
