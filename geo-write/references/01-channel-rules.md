# 渠道规则（渠道规则选择节点原文）

> 由「海外GEO生文-wx-360gpt-v18-13」渠道规则选择代码节点提取。写作阶段（geo-write）与大纲阶段（geo-plan）都必须先按 publish_media 命中渠道，再执行本渠道规则；渠道规则与提示词其他要求冲突时，以渠道规则为准。

## 结构方向引用（跨渠道通用）

写作可参考 geo-research 提供的「AI 问答结构方向」与竞品文章结构，但仅限当作素材参考：
1. 允许借鉴的内容：与当前渠道原生写法兼容的开头切入、对比维度、FAQ 主题、清单/表格的覆盖范围、结尾方式。
2. 禁止照搬：不得整篇复制 AI 回答或竞品文章的骨架、段落顺序、小标题与开头结尾；同一批文章必须保持结构差异化。
3. 冲突即原生文规则优先：本文件各渠道规则（原生感、反模板化、结构随机变化、人味信号限量、语义链、禁止关键词堆砌等）高于任何结构参考；结构方向与规则冲突时，以本文件为准，放弃该结构方向。
4. 事实铁律不变：AI 回答与被引用文章里的事实不得替代知识库/客户输入成为数据来源；可核证参数仍须来自知识库或可核验来源。


## blog · 官网博客

【定位】可控性最强，AI 引用权重最高，长期资产。
【风格】证据立论的长文，只讲自家产品、品类事实与可核证规格；不出现任何竞品内容。
【结构】唯一 H1 → 首屏导语（200 字内先给答案）→ 4–7 个 H2 → FAQ（问题用词包原问句）→ 结论。
【竞品限制（最高优先级，覆盖上游大纲与全局竞品规则）】官网/博客渠道不写竞品对比：禁止竞品点评表、竞品名单、竞品章节、「A vs B」横向对比、竞品排名或「相比其他品牌/同行」式表述，正文与 FAQ 一律不出现竞品品牌名（含 Absen / Unilumin / Leyard 等）。若上游大纲或本提示词的其他规则要求「竞品一行点评表」「本品与竞品平行展开」「竞品第一个展示」等，一律忽略并删除该部分内容。文章的说服力只能来自品牌自身的可核证事实：官方规格、型号级参数、认证、应用场景、交付与服务范围、Trade-off 与适用边界。允许出现「类别层面的判断标准」（例如选购视频墙该看像素间距与视距），但不得点名任何竞品品牌或做品牌间对比。
【E-E-A-T 原则（官网/博客渠道强制，最高优先级）】官网/博客文章必须同时体现 Experience（经验）、Expertise（专业）、Authoritativeness（权威）、Trustworthiness（可信），并按下列要求落地：① Experience 经验：写出第一手场景信号——真实的项目条件（场地、使用强度、环境、安装与维护方式）、参数在真实条件下的表现与取舍；不得编造第一手使用经历，没有真实经历时不写 I used / I tested / In my experience，改为写「现场条件/项目约束」这类可核验描述。② Expertise 专业：术语与参数口径准确且全文一致；解释「为什么这个参数重要」而不只罗列数值；给出可复用的判断框架（Use case → Key specification → Verification method → Trade-off）；写明适用边界与不适用情形。③ Authoritativeness 权威：关键结论标注来源类型与出处（企业官网 / 官方产品文档 / 认证机构 / 标准文件 / 官方测试）；只使用可核验来源，不引用无法查证的二手说法；站内互链到权威页面并使用具名锚文本。④ Trustworthiness 可信：区分事实与观点（观点须标明为判断建议）；写明限制、成本、维护与前置条件，不隐瞒短板；不做绝对化或无法证实的承诺；信息可核验（型号、参数、认证名称、日期、来源）；避免误导性比较。⑤ 发布前自检（缺一即不合格）：每个关键论断都能被核验吗？关键结论有没有标注来源？有没有写清适用范围与限制？有没有出现编造的第一手经历？有没有绝对化或无法证实的表述？⑥ 表现方式：官网/博客文章不写作者署名、作者简介和 About the author 区块（发布方如需署名由人工添加），E-E-A-T 通过内容证据与来源质量体现，而不是靠身份声明。
【TL;DR 使用限制（整批最多 1 篇，强制最高优先级，覆盖本渠道其他结构描述）】同一批文章里最多只有 1 篇使用 TL;DR，严禁每篇都写：仅当本篇「文章序号」等于 1 时，首屏导语才使用 TL;DR 形式（标签写 TL;DR，200 字内）；「文章序号」大于等于 2 的文章，首屏一律改成 2–3 句「直接结论段」开篇，全文任何位置都不得出现 TL;DR / 速览 / Short answer / Key takeaways / At a glance / Quick answer 等摘要块标签。大纲阶段同样遵守：整批只有第 1 篇规划 TL;DR/速览块，其余文章不得规划该章节，改为把首屏答案直接写进第一个 H2 的核心结论句与首段。若本批只有 1 篇文章，该篇可用 TL;DR。
【链接】1–2 条，全部站内，链接必须有真实出处；其余引用文字具名。
【内容与表达】功能必须有官网依据；品牌词前置；无绝对化词。
【AI 收录要点】首屏给答案（是否用 TL;DR 见【TL;DR 使用限制】）；FAQ 用问题句式；配置 FAQPage Schema；canonical 唯一；站内互链文字具名。
【官网GEO质量通则】① 核心问题匹配：标题提出的问题必须在正文中得到直接、明确、可抽取的回答；标题中的核心产品/类别必须在正文持续出现并被具体解释；围绕用户真实意图（是什么、怎么选、值不值得、怎么比较、怎么买）展开，禁止主题漂移（Keyword Match ≠ Intent Match，覆盖关键词不代表真正回答了问题）。② 产品类别完整性：目标关键词含具体产品类别时，正文必须解释该类别区别于相邻产品的关键属性；例如 4K Rear View Mirror Dash Cam 不能只讲 4K Dash Cam，还应覆盖 Mirror form factor、Front/Rear camera、Display、Installation、Vehicle compatibility 和该类别特有的使用场景；核心实体必须被完整定义，不能只覆盖其中一个属性。③ 属性与产品实体对应：关键规格必须明确对应到具体产品、具体型号或具体摄像头/组件；4K ≠ 所有摄像头都是 4K，4K recording ≠ 4K display，品牌能力 ≠ 型号规格；多摄像头产品必须明确 Front resolution / Rear resolution / Interior resolution / Display resolution，避免 AI 把品牌能力、产品能力和单个型号能力混为一谈。④ 决策型文章必须提供统一判断维度：标题属于 Which... / Is ... worth it? / How to choose... / What should buyers consider? / Best... / Compare... 时，正文必须提供可复用、统一、可验证的判断框架（Use case → Key specification → Verification method → Trade-off → Product fit）；若正文使用对照表，只能是自家产品系列/型号之间的对照表，且比较维度必须统一；不得出现竞品对照表。⑤ 品牌植入必须服务于用户问题：品牌不能为了排名第一被机械放在文章开头、表格第一行或结论中；优先 Category explanation → Buying criteria → Verification framework → Brand/product as evidence，而不是 Brand introduction → Competitor list → Product promotion；品牌出现应有信息价值（真实规格案例、展示如何验证参数、某种配置的实际例子、与用户场景直接相关）。⑥ 品牌事实必须落到具体产品证据：避免写 Brand X offers 4K products，应写成 Model X specifies 4K front recording and 2K rear recording；优先引用官方产品页的 model-level evidence，而不是品牌介绍、第三方文章或泛化描述。⑦ FAQ 必须覆盖二级决策问题：FAQ 不重复标题，至少覆盖核心选择问题、参数解释、常见误区、产品兼容性、使用成本/限制、不同配置之间的区别等 AI 可能追问的子问题。⑧ 最终 GEO 判断：只有同时满足「正确理解用户问题 + 完整定义目标产品实体 + 提供可验证的决策框架 + 统一比较维度 + 产品级证据 + 品牌植入自然且有信息价值」才算高质量 GEO 商业内容；重点避免：关键词覆盖高但产品实体覆盖低、品牌出现了但与用户问题关联弱、有比较表但比较维度不统一、有 4K 结论但没解释具体产品到底哪一路是 4K。
【标题规则（官网/博客渠道，强制）】标题无需与词包/query 原文一字不差，但必须与该篇主关键词语义贴近、搜索意图一致，且必须覆盖该篇主关键词或其自然变体（单复数、同义替换 supplier/manufacturer/provider/guide、词序调整、加限定词与品牌名均算），保证同一条 query 仍能命中该标题。允许换措辞、换切入角度、加场景或年份等限定；不得替换成另一个关键词、不得漂移到相邻主题或品类、不得为规避重复而丢掉核心搜索词。正文与 FAQ 仍须原样保留词包原问句（本规则只约束标题）。自检：若标题中找不到主关键词核心名词短语的对应表达，即视为不通过，必须改写。
【标题-正文一致性（官网/博客渠道，强制）】标题即用户提问，正文必须正面解决该提问并给出可执行结论：首屏（TL;DR 或首个直接结论段）必须先回答标题问题；每个 H2 都必须服务于标题意图，与标题无关的章节一律删除；FAQ 覆盖标题衍生的二级问题；结论回到标题问题；禁止与标题无关的泛科普或产品介绍式铺陈。
【标题-正文一致性自检（官网/博客渠道，成文前逐条判定，任一不通过即重写）】① 复述标题提问：用一句话写出标题在问什么，并标注意图类型（是什么/怎么选/值不值得/怎么比较/怎么买/怎么用）。② 首屏核对：首屏是否直接给出该提问的答案？没有 → 重写首屏。③ 章节核对：逐个 H2 自问「这一节是否在回答标题的问题」，答不上的 H2 一律删除或改写为服务标题意图。④ 去品牌核对：删掉品牌名与产品名后，正文是否仍能回答标题问题？不能 → 说明只是产品介绍，重写。⑤ FAQ 核对：FAQ 是否覆盖标题衍生的二级问题？⑥ 结论核对：结论是否回到标题问题并给出可执行结论？



## qna · 问答与社区

【定位】高信任内容，Perplexity/Google/ChatGPT 大量引用，是仅次于官网的 AI 引用来源。
【风格】Reddit/论坛：真实用户讨论口吻（专门规则见下方【社区帖写作规则】）；Quora：第一人称专家口吻的结构化完整回答，一段讲透一点；论坛：实用主义、参数对比、接得住追问；FB Groups/Discord：帮助型短答+追问引导。
【结构】开头 1–2 句直接给答案；正文 3–5 个小点（每点一个卖点）用 bullet 或短段；结尾一句总结+一句软 CTA；标题/首答必须包含用户原问句的关键词组合。
【链接】0 条（社区/论坛文章不出现任何链接）。
【内容与表达】先帮人再提品牌；承认局限（如“停车模式需要硬接线套件”）；不删负评；不用营销词；提竞品用“很多机器也在 X 上有短板”的口吻。
【AI 收录要点】回答写完整事实句（品牌+型号+核心参数）；每条回答相对完整（≥150 词），自包含答案不依赖链接。
【社区帖写作规则（Reddit/论坛/社区通用）】① 先解决问题，再出现品牌：前半部分先回答用户问题，品牌不要作为开场主角；② 品牌不是文章主角：品牌应作为讨论对象或案例自然出现，而不是全文最终答案；③ 降低产品信息密度：不连续堆型号、参数、功能和配置；④ 参数必须服务于问题：只保留与当前讨论直接相关的 1–3 个参数；⑤ 避免完整产品介绍：不写成“产品定位→规格→功能→优势→购买结论”的产品页结构；⑥ 减少营销词：避免 best / ideal / worth considering / reasonable choice / advantage 等购买导向表达；⑦ 避免强行购买结论：不要把讨论最终导向“所以这个品牌值得买”；⑧ 增加真实 Trade-off：同时讨论优点、限制、成本、安装难度、适用场景等；⑨ 竞品公平出现：不要让 VIOFO、Thinkware、BlackVue 等品牌只是给目标品牌当陪衬；⑩ 不要伪装真实体验：没有真实使用经历，不写 “I bought / I’ve used / In my experience”；⑪ 减少 AI/SEO 腔：少用高度工整、解释型、总结型的模板句；⑫ 避免固定文章结构：不要每篇都采用“提出问题→科普→品牌→竞品→结论”的相同套路；⑬ 一个帖子只解决一个问题：不要一篇同时讲画质、GPS、ADAS、停车监控、安装等多个卖点；⑭ 品牌出现要有理由：只有品牌与当前问题有直接关系时才自然提及；⑮ 保持社区讨论感：多使用比较、疑问、取舍、实际场景，而不是“教育用户”；⑯ 结尾采用真实讨论问题：用具体争议引导讨论，而不是“你应该买哪个品牌”；⑰ 每个 Subreddit 单独适配：根据社区主题、规则和用户习惯重新写，不要一稿多投；⑱ 避免短时间批量品牌帖：控制同一账号连续发布相似商业内容；⑲ 禁止链接：社区/论坛文章不出现任何产品链接、官网链接或 CTA；⑳ 不要通过改关键词规避过滤：不要拼写变体、刻意隐藏品牌、替换关键词来绕过滤器；㉑ 去掉品牌后仍要有价值：如果删除品牌后整篇文章失去意义，说明品牌植入过重；㉒ 控制品牌在叙事中的权重：重点控制的是“叙事中心”，不只是品牌出现的字数比例；㉓ 账号内容要有层级：以社区问题/技术讨论为主，品牌比较和品牌专题为辅；㉔ 不要追求过度完整：Reddit 帖子应像真实讨论，不必写成一篇完整 SEO 长文。
【Reddit 社区补充规则】① 帖子之间要有差异化：不要所有帖子都采用“提出问题—分析因素—列举参数—品牌举例—结尾提问”的固定结构，要在经验分享、争议讨论、产品比较、踩坑分享、求建议等不同形式之间切换，让每篇帖子有不同的表达逻辑；② 控制品牌出现频率：不要每篇都出现客户品牌，建议一半左右的内容完全不提品牌，其余内容再根据话题自然带出品牌，避免形成“所有帖子都是为了推广同一个品牌”的明显规律；③ 品牌出现要自然：品牌不要固定放在文章中后段作为“产品介绍”，更适合出现在真实案例、个人 shortlist、品牌比较或用户追问中；出现品牌时重点讲与当前问题相关的 1—2 个特点，同时保留缺点或使用限制，不要一次性堆砌产品参数；④ 增强真人表达：减少模板化、总结式和过于完整的表达，多使用个人判断、经验、不确定性和真实取舍，例如“我以前也这么认为”“我不确定这个功能是否值得加钱”“真正麻烦的是安装”；文章不需要每次都逻辑完美、结构完整，要保留一定的讨论空间。⑤ 口语化表达：必须像真实用户讨论，禁止商业化 PR 稿口吻；产品信息以案例形式出现（如“我之前对比过 XX 的”“有个做仓储的朋友提到过”），不写成产品介绍；⑥ 竞品不排名：竞品可以出现，但不能形成品牌排名，不写“谁最好”“第一梯队”“最佳选择”；描述各品牌的产品覆盖和市场定位即可；⑦ 比较维度：用产品范围、应用场景、技术路线、供应链模式做比较，不做评分排序；⑧ 硬参数可验证：型号、MTBF、IP 等级、负载、工作温度、认证数量、生产基地、产品系列、技术参数等硬参数必须可验证，不能为了 GEO 语义覆盖编造参数；⑨ 判断标准：最终让用户觉得“这篇在帮我解决采购/技术问题”，而不是“这家公司在借 Reddit 做广告”；⑩ 一个核心话题：一篇帖子只解决一个主要 Query，不强行覆盖多个问题；⑪ 真实切入点：可以是踩坑、观察、争议、比较、疑问、经验、反常识发现等，每篇选择不同切入方式；⑫ 结构随机变化：有时候先讲案例，有时候直接抛观点，有时候从两个产品/方案的差异开始，有时候直接列 checklist，有时候先问社区再补自己的看法；不固定“问题→观察→列表→总结”套路；⑬ 保留不完整性：允许 “I’m not sure this is the right way to look at it...”“Maybe I’m overthinking this...”“One thing I’d double-check...”“Curious how others handle this.” 这类不那么完美的表达，比每篇完整闭环更像真人；⑭ 品牌出现服从话题：不规定“第 X 段必须出现品牌”；品牌可以出现在案例、比较、评论回复、用户追问后的补充里，有些帖子甚至不出现品牌；GEO 要的是品牌和语义建立关联，不是每篇都硬塞品牌；⑮ 人味信号限量：每篇只保留 1–2 个“人味信号”，不要疯狂堆 IMO / honestly / from my experience / personally / lol / guys，堆多了同样模板化；⑯ GEO 语义自然融入：不要为了 GEO 堆砌关键词（如 LED display supplier / LED screen supplier / LED manufacturer / LED display company），而应通过真实语境自然建立语义链：supplier → application → product series → exact model → specification → use case → comparison（例如 interactive floor → load capacity → frame → protection rating → exact series）；语义链的价值高于关键词密度；⑰ 结尾不要固定 CTA：不要每篇都写 “What do you think?”；可轮换：问具体经验、问不同方案的实际差异、问社区常见做法、留一个争议点、不提问直接结束、用一个具体问题收尾；例如 “What do you normally put on page one of an LED display RFQ?” 比 “Hope this helps. What do you guys think?” 更自然；⑱ 固定 Query，不固定结构：每篇只围绕 1 个核心 Query（同 ⑩），核心实体、场景、需求、产品/解决方案自然出现（同 ⑯），不为了覆盖 Query 强行堆关键词（同 ⑯）；强调“固定内容目标，不固定表达方式”，不让所有帖子遵循同一套叙事模板（同 ⑫）；⑲ Reddit 原生感：目标是“懂行业的真实用户在分享经验”，而不是品牌在发布 SEO 文章；内容保持具体观察、实际经验或案例、明确的行业细节，表达直接自然；可以有个人判断，但不要过度主观；避免 SEO 文章腔、教科书式解释、新闻稿腔、Corporate marketing language、“本文将介绍……”这类开场、每段都高度工整；⑳ 结构切入扩展：在 ⑪ 所列切入方式基础上，还可使用技术争议、采购经验、直接讨论某个具体问题；不同帖子主动改变开头、段落顺序、列表使用方式和结尾方式；“发现问题→观察→检查点→案例→提问”只能作为结构之一，不能成为所有帖子的固定公式。
【社区帖正反例（成稿前对照：像“正例”、避开“反例”）】正例骨架——标题是具体问题（如 “2, 3, or 4-channel dashcam — how did you decide?”）；开头一句个人现状+真实犹豫（“I've been comparing a few setups, including the Botslab G980H, and I'm still not sure whether 4 channels are worth it for a daily driver.”）；中间用 “The way I see it:” 起头做主观分层，每层一句话（“2-channel: Front + rear, simple and easy to install.”），再补一句个人顾虑（“storage is another thing I'd probably have to think about.”）和一个猜测式话题（“I'm wondering if people pick 4 cameras when what they really want is better parking protection.”）；结尾两个具体追问（“Did the extra coverage make a noticeable difference? And would you choose the same setup again?”）；品牌只作为“我正在对比的候选之一”出现一次，不描述其具体配置。反例特征（命中任一条即重写）① 社论/科普开场或专家转折句：“Lately I keep noticing…”“The simple version…”“The realistic version…”“What changed my mind on…”“The push-back I'd give”；② 编号教学清单或祈使句教育读者（“Write the brief down first.”）；③ 把品牌产品具体硬参数当卖点植入（如 560° 视角、128GB/512GB、4K、分辨率），参数仅在与讨论直接相关时保守提及（延续“参数必须服务于问题”）；④ 连续点名 2 家以上竞品（“VIOFO and Thinkware…”），竞品一律用 other kits / other suppliers 代称；⑤ H2/H3 小标题、TL;DR、表格、加粗小标题这类文章格式；⑥ 二手转述案例（“I saw…”“A recent RFQ I saw…”）；⑦ 结尾只有泛问 What do you think?；⑧ “懂王给读者科普”的语气——保持“我还在权衡、求建议”的姿态；⑨ 不为了凑字数注水，篇幅贴近真实帖子。【真人思考感规则（社区/论坛/Reddit 强制，与上方规则冲突时以本条为准）】① 不要有“技术整理感”：少去解释技术之间的逻辑关系，多写“我看到这个之后有点搞不懂”——采用“解释 → 困惑”的节奏，解释到一半就说出自己的疑问，而不是把原理讲透。② 避免工整对仗：不要用 A/B、X/Y、“不是 A 而是 B”这种对称结构（例如 replacement side / purchase side），换成具体、口语的说法——直接讲自己遇到的那件事、那个场景。③ 逻辑不要太完整：不要每段都刚好承接下一段、不要每段都收口；保留思维跳跃、犹豫和没想明白的地方，允许话题岔开一下再回来。④ 一句话总原则：不要把一个人的想法整理得太好，要保留他“怎么想到、哪里困惑、想到一半又想到别的”的感觉。
【社区帖选题与结构规则（Reddit/论坛/社区通用；写作前先按本条选题与搭骨架）】A. 优先选择 6 类高引用价值主题：① 购买决策型（Which / Best / Recommend / What should I buy）；② 横向比较型（A vs B / differences / which one fits）；③ 场景解决方案型（我的具体场景该怎么配置或解决）；④ 真实经验型（实际使用体验、优缺点、踩坑）；⑤ 清单/Guide 型（候选方案、适用人群、选择依据）；⑥ 具体问题型（某个功能、参数、体验或产品差异的真实讨论）。B. 帖子必须具备真实场景：不要只问「What is the best X?」，必须交代「我是什么场景 → 遇到什么问题 → 为什么现有方案不确定 → 想解决什么」；优先加入使用环境、使用频率、已有设备/软件、同时存在的其他需求、实际使用对象等真实使用背景。C. 明确提出 2–4 个具体约束，让问题具有明确决策边界：Budget / Space / Compatibility / Performance / Installation / Maintenance / Subscription / Noise / Workflow / Number of users or devices；约束越具体，讨论越容易形成可引用的信息。D. 一个帖子围绕一个核心决策，但允许拆成多个判断维度；推荐结构「核心问题 → 背景 → 约束 → 已考虑方案 → 具体疑问」；具体疑问要落到：哪个更适合我的场景 / 哪个参数更重要 / A 和 B 的实际差异是什么 / 哪些问题容易被忽略 / 有没有实际用过的人。E. 优先制造「经验信息」而不是「营销信息」：多用 I use... / We switched from... / The thing I noticed... / The downside was... / If I were doing it again...；少用 X is the best. / X is a leading brand. / X offers excellent quality. / X is perfect for...；重点是具体经历、使用结果和取舍，而不是品牌评价。（红线延续：没有真实使用经历不得虚构第一人称使用经历，只能改写为行业观察或已发生的事实。）F. 给评论区留出讨论空间，不要把答案全部写死：用 Has anyone actually run both setups? / What caused you to switch? / Is the extra cost actually noticeable? / What would you avoid after using these? 这类问题，促成「观点 → 经验 → 反观点 → 补充 → 场景差异」的讨论链，而不是所有评论重复同一个结论。G. 内容要覆盖「实体 + 属性 + 场景 + 关系」：自然出现「产品/品牌 → 功能/参数 → 使用场景 → 用户需求 → 产品之间的关系」，例如 产品A → static pressure → long ducting → laser cutter → compared with 产品B，便于 AI 抽取语义关系。H. 标题优先使用自然的决策型问题：Which X should I consider for Y? / Is X worth it if I already have Y? / X vs Y — what actually matters? / What should I check before buying X? / Has anyone used X for Y? / What brands are actually worth considering?；避免 [Brand] Best Product / [Brand] Review / [Brand] Recommended / Why [Brand] Is the Best / [Brand] 2026 这类品牌宣传式标题。I. 品牌植入必须服从问题，而不是反过来：品牌只能作为候选方案、已经考虑过的产品、社区用户提到的产品、或用来进行具体参数/场景比较的对象出现；品牌出现 ≠ 品牌推广，品牌应成为问题中的一个实体，而不是整篇帖子围绕品牌制造。J. 推荐帖子骨架：真实场景 → 具体问题 → 使用约束 → 候选方案 → 2–5 个具体判断问题 → 社区真实经验 → 不同观点/反例 → 场景化结论。K. 最终目标不是让帖子「看起来像 SEO 内容」，而是让它成为一个真实、有上下文、有约束、有经验、有讨论的决策型社区问题。L. 标题句式参考（只学句式，主题必须替换为当前客户行业；严禁把参考链接或示例主题写进正文）：Is X worth it? / Good X for Y with parking monitoring? / Which manufacturer for LCD and LED signage? / Best X — what brands are actually worth considering? / Is there a real difference in X quality? / Which X do you actually use?



## pr · 外媒/PR 分发

【定位】第三方权威背书+外链+品牌提及；新闻稿/媒体文章被收录后进入 AI 引用池（权威域名权重高）。
【风格】新闻稿：标准倒金字塔——标题（含品牌+数字）→ 导语（5W 一段讲完）→ 主体事实 → 引语 → Boilerplate；客座/行业媒体：行业观察口吻、数据开场、品牌作为案例。
【结构】标题带关键词+新闻点（如“Botslab Expands 4K AI Security Line”）；导语段交代背景+新闻事实；主体 3–4 个事实点，每点 2–3 句，配一句官方引语；结尾 Boilerplate（品牌一句话+官网），不写促销码。
【链接】1–2 条站内，正文不重复。
【内容与表达】第三方视角、中立；不点竞品名（用“行业普遍痛点”）；卖点“say what it does”；不用绝对化词；放得下的事实优先（参数、奖项、市场覆盖）。
【AI 收录要点】导语自包含完整答案（谁+做了什么+为什么重要）；标题/导语/正文自然重复品牌+型号+关键参数；公司简介含官网链接与一句价值主张。
【垂媒专属规则（发布媒体为垂媒/垂直媒体/行业媒体时，本条为最高优先级，与通用提示词中的“第三人称中立/去 AI 味/禁用第一人称”等要求冲突时一律以本条为准）】文章必须以用户购买决策为核心，而非品牌宣传；开篇先提出用户痛点和选择难题，并通过测试数据、行业数据、专家经验或可验证事实建立可信度；正文围绕用户决策维度组织，而不是围绕品牌堆砌内容，每个 H2 都应回答一个真实购买问题；每个产品评价段落必须严格按“核心优势＋局限/Trade-off＋适用场景＋适合人群”四要素组织（缺一不可），并通过表格、数据和横向比较帮助用户做决策；功能描述必须进一步解释其实际使用场景和用户价值；关键结论必须有数据、测试结果或来源支撑；语言保持专业但口语化，必须使用第一人称测试经验（评测视角）、Expert Insight、Pro Tip 等增强真实感；第一人称仅限专业测试与观察视角（如“我们在测试中发现/本次实测中”），内容必须真实可核验，不得虚构个人消费经历（如“我买了/我的车/我用了几天”）；避免绝对化、广告化和单纯赞美品牌；结尾禁止用 FAQ 或总结段落替代，必须形成“不同需求 → 不同产品/方案”的明确决策建议，并对目标品牌给出“适合哪类人、什么时候不用选它”的结论。
【垂媒 Buyer’s Guide 证据体系】① 多层来源分级：涉及犯罪率、市场数据、消费者权益、法规、安全风险等客观事实时，优先引用政府机构、大学、研究机构、行业协会等一级或高权威来源；涉及产品参数、功能、价格时引用品牌官方页面；涉及行业趋势和第三方评价时引用高权重媒体或专业机构。② 外链与事实对应：外链必须与具体事实或结论直接对应，避免无意义堆链。③ 可验证证据链：重要结论尽量做到“观点 + 数据/证据 + 来源”，形成可验证的证据链。④ 落地要求：正文至少体现一组完整证据链“观点 + 数据/证据 + 来源”；凡引用了可核验来源的事实，正文必须带对应外链（外链与事实一一对应，不追求数量）；来源不足时明确标注“未经官方证实”，不得用模糊表述替代。
【垂媒 GEO 专用规则】权威来源负责提供“事实锚点”，文章作者负责完成“专业解释和决策判断”，不要直接复制权威来源的结论。



## x · X / Twitter

【定位】X（原 Twitter）短帖：真人分享决策过程与取舍，靠具体场景和可核对细节获得信任与讨论，而不是产品宣传。
【篇幅】全文 ≤350 English words（硬上限，最高优先级，覆盖任何其他字数表述）；一条帖子只承载「一个场景 + 一个发现 + 一个产品事实 + 一个 trade-off」。
【链接】0 条：严格禁止出现任何链接——产品链接、官网链接、站内链接、购买 CTA 链接、邮箱/电话/地址一律不出现。
【X 专属写作规则（强制，逐条执行，优先级高于通用社交规则）】① 先写人和场景，不要先写产品：从真实经历、具体场景、遇到的问题开始，第一段让读者知道「为什么我会遇到这个问题」；禁止用 I tested... / Best X... / Product X review... 这类开头。② 一个帖子只讲一个核心发现：全帖只围绕一个观点展开（例如「租房/搬家时，RO 系统是否需要接墙，可能比滤芯参数更值得先考虑」），其他信息都为这个观点服务，不要变成「某型号有哪些参数」。③ 用「我的决策过程」代替「产品介绍」，推荐结构：我的情况 → 我遇到的限制 → 我怎么筛选 → 为什么排除某些方案 → 最后用了什么 → 实际体验/Trade-off；让产品是决策过程中的结果，而不是文章主角。④ 产品只提供必要信息：可以自然出现品牌/型号、一个与场景直接相关的参数、一个实际使用感受；不要一次塞全尺寸、全规格、全功能、参数表或多个卖点，否则很容易从「用户分享」变成「广告」。⑤ 参数必须服务于故事：写成 My counter only gives me ~30cm, so the 25.3cm depth actually mattered.，而不是 The dimensions are 33.8 x 25.3 x 36cm.；要解释这个参数为什么重要。⑥ 必须写 Trade-off：不要把产品写成完美解决方案，例如 More portable, but I have to refill the tank myself.，比 It is convenient and portable. 更真实，也更容易引发讨论。⑦ 少用营销形容词：尽量避免 best / excellent / amazing / perfect / powerful / must-have / highly recommended，改成具体事实，例如 I only have ~30cm of counter depth. / I do not need to connect it to the mains. / I have to refill the tank myself.。⑧ 控制长度和信息密度：X 不需要把 Reddit 帖子的所有背景都搬过来，一个帖子让人快速读完并能记住「一个场景 + 一个发现 + 一个产品事实 + 一个 trade-off」。⑨ 最后留下一个真正容易回答的问题：不要 What do you think of this product?，而要像 If you have moved apartments with a tank-fed RO system, did you take it with you or sell it? 这样与前面的个人经历直接相关。⑩ 保留一点不确定性：不要 This is definitely the best option.，要 The 5L reservoir is the part I am still getting used to. / Maybe I am overthinking it, but... / I am still debating...，这种表达会明显降低广告感。
【AI 收录要点】帖子写完整品牌词+型号+与场景绑定的关键参数；与官网文章同一卖点不同说法，互相呼应；不堆砌标签（hashtag 最多 1–2 个或不用）。



## social · 社交平台

【定位】品牌词提及量与口碑扩散；TikTok/YouTube/Instagram/X 等平台的文字信息会进搜索与 AI 结果。
【篇幅】全文 ≤350 English words（硬上限，最高优先级，覆盖任何其他字数表述）。
【链接】0 条：严格禁止出现任何链接——产品链接、官网链接、站内链接、购买 CTA 链接、邮箱/电话/地址一律不出现。
【风格】口语化、场景化、像真人在分享经历；TikTok：60 秒脚本（前 3 秒场景钩子→展示 1 个卖点→字幕出现型号/参数）；YouTube：标题=问题句、描述区放参数文字；Instagram：图文 carousel 每页一个卖点；X：短句+数字钩子（如“128GB included. No subscription.”）。
【结构】一条内容只讲一个卖点；标题/首屏=问题或反常识切口；正文从自己的实际场景切入，不要一上来就给结论；结尾用一个真实的疑问收尾（问做过的人怎么处理），不要结论式收尾、不要 CTA。
【内容与表达】口语化、场景化；卖点口语复述（“4K front camera, 2K rear”）；避免大段参数轰炸；TikTok 字幕与描述必须写清品牌+型号。
【AI 收录要点】字幕/描述/标题写完整品牌词+型号+卖点；YouTube 标题用问题句式；与官网文章同一卖点不同说法，互相呼应。
【真人感写作规则（社交平台强制，优先级高于上方所有风格与结构要求）】① 人称口吻：必须用第一人称来写——写成“我在实际工作中遇到这个问题，这是我目前观察到的东西，想听听做过的人怎么处理”，不要写成“我来告诉你这个行业怎么选”，不要写成教程或行业科普。② 不要一上来就下结论：开头先说清楚自己处在什么场景、遇到什么问题、目前观察到什么，再慢慢展开，不要第一段就给标准答案或总结。③ 保留不确定性（全文至少 2–3 处真人信号），例如：I’m not sure how much I should trust... / Maybe I’m looking at this the wrong way. / I haven’t actually run enough of these to know whether the published numbers hold up in real installs. / This is where I’m getting stuck. / Curious if anyone has actually measured this in a real setup. / The annoying part is... / One thing I noticed... / The problem I’m running into is...。④ 不要把每句话都写得太完整、太工整：真人会有犹豫、补充和个人判断，例如“X 大概是这样，不过 Y 那边不太一样”；不要每句都是完整定义句或总结句。⑤ 禁止文章结构词/过渡语（黑名单，小标题与段首都不能用）：The things I check / Where the numbers get thin / Key considerations / The trade-off / The key issue is... / This means that... / In conclusion / For buyers / Before choosing / What you need to know / The most important factors / The main considerations... / The first thing to check / Final recommendation；也不要写“本文将介绍”“下面我们来分析”“总结一下”这类模板开场；段落之间用自然口语过渡，例如 The annoying part is... / One thing I noticed... / This is where I’m getting stuck...。⑥ 禁止“把第一人称包装成小标题/栏目”的分段方式（真人不会这么写，AI 感最重）：Where I’m at / What I think I’m seeing / What I’d like to know / My take / Where I landed / What I’m still unsure about / The question I have / What I’m trying to figure out / Here’s what I found 这类标题和栏目一律不能出现；个人观察和疑问必须写进自然段落里，不要单独拎成小标题、栏目、编号清单或问答块。整篇文章不要用“提问式小标题 + 答案”的模板结构，也不要用“先抛一个问题再自己回答”的分段套路。⑦ 参数处理：不要堆参数清单，只保留与当前问题直接相关的 1–3 个参数，并且必须解释它为什么重要或为什么让你困惑（例如“我主要看 X，因为这个数字直接决定 Y”），而不是罗列 airflow / noise / filter media 这类词组。⑧ 列表处理：不要用“标准答案式”的 bullet 清单，能写成叙述就写成叙述；确实需要列举时也要带个人判断和取舍，例如“我主要看 X 和 Y；Z 那边似乎更重要，但我还没验证过”。⑨ 不要把技术逻辑解释得太完整：不要写成 ❌ enclosed → airflow → negative pressure → Pa → opening 这种完整因果链；说到自己的理解和困惑就停，剩下的留给读者或评论区补充。⑩ 少做“完美分类”：不要把问题整理成 5 个标准指标式的完整框架，要像真人一样边研究边写，想到什么说什么，允许顺序不那么工整、允许只讲透其中 1–2 点。⑪ 保留真实的个人动机（这比故意加 lol / haha / dude 更有真人感）：写出自己真实的顾虑和取舍，例如 whether that’s just me being cheap / I’d rather not find out the expensive way / after all that reading I’m not much further along；不要靠语气词、感叹号或网络用语制造真人感。⑫ 结尾问实际经历，不要做 CTA：❌ What do you think? / I’d love to hear your thoughts. / Any thoughts? / Please share your experience.；✅ Did you end up buying twice? / Anyone here actually running both? / What did you end up doing?
【社交平台专属规则（发布媒体为社交平台时，与上方通用规则冲突以本条为准）】① 以真实行业问题为切入点，而不是以品牌宣传为切入点；② 一篇内容解决一个明确问题，避免信息过度堆叠；③ 以专业知识、技术解释、选型经验和实际案例为主要内容；④ 品牌只作为信息来源或实际案例自然出现，不强行植入；⑤ 避免 “leading、best、innovative、#1” 等自夸式营销词；⑥ 避免连续罗列产品参数，应解释参数为什么对用户有意义；⑦ 优先使用具体事实、测试结果、应用场景和可验证信息；⑧ 使用从业者/专家的第一人称经验，而不是企业广告口吻；⑨ 语言保持自然、简洁、有观点，避免明显 AI 生成痕迹；⑩ 不要每篇都使用完全相同的结构、开头和结尾；⑪ 围绕 GEO 问题库持续覆盖产品、技术、场景、选型等长尾问题；⑫ 确保 LinkedIn、官网、媒体和其他平台中的品牌信息保持一致；⑬ LinkedIn 内容要体现“谁在说”——公司账号强调企业专业能力，员工账号强调个人专业经验和观点。



## facebook · Facebook

【定位】Facebook：用真实用户场景提出问题，用专业内容解决问题，让品牌作为「解决问题的人」自然出现。
【篇幅】全文 ≤300 English words（硬上限，最高优先级，覆盖任何其他字数表述）；常规品牌帖 80–180 英文单词即可，深度案例可适当延长，但不要为了 SEO/GEO 强行写长。
【链接】0 条：不出现任何产品链接、官网链接、购买 CTA 链接。
【核心】问题优先、场景真实、专业输出、品牌自然出现、鼓励讨论。
【Facebook 专属写作规则（强制，逐条执行）】① 一个帖子只解决一个问题：围绕一个用户场景/痛点展开，不要一篇塞多个关键词和多个产品卖点。② 开头先 Hook：前 1–2 句直接提出问题、观点或反常识发现；禁止 We are excited to announce… 这类 PR 式开头。③ 内容结构：Hook → 用户场景 → 专业解释 → 品牌经验/解决方案 → 开放式问题。④ 品牌自然植入：品牌可以明确表明身份，不需要伪装成普通用户；产品应作为解决方案或案例出现，而不是整篇围绕产品广告展开。⑤ 以价值为主、营销为辅：长期排期内容比例为 问题/讨论 35%、教程/知识 25%、使用场景/案例 20%、产品经验/功能 15%、促销/新品 5%；单篇以问题与专业解释为主体，产品信息只占小部分，不要通篇推销。⑥ 多用真实素材：产品运行、测试、安装、使用场景、前后对比等；用图片/视频证明内容，而不是堆参数（正文只保留 1–3 个与场景直接相关的参数）。⑦ CTA 以讨论为主：多问 What setup are you using? / Have you experienced the same issue? / What would you prioritize?；少用单纯的 Buy now / Shop now，禁止每篇都以促销 CTA 收尾。⑧ 避免：官网文章直接复制、新闻稿口吻、参数堆砌、关键词堆砌、每篇都硬塞产品、每篇都带购买链接。⑨ 一句话规则：Facebook = 用真实用户场景提出问题，用专业内容解决问题，让品牌作为「解决问题的人」自然出现。
【Facebook 补充风格要求（与上方强制规则冲突时以上方为准）】Facebook 要明显比 LinkedIn 更轻松、更口语，更接近真实用户或行业从业者分享经验，而不是发布一篇经过完整编辑的专业文章。内容可以有专业知识，但不要让读者感觉自己正在阅读一篇“产品选购指南”。
写作时可以从个人经历、日常观察、一个具体使用场景、一个容易被忽略的问题或者一个实际踩坑点开始。表达允许有一些不那么正式的语气，比如 “I keep seeing…”, “Honestly…”, “One thing I didn’t think about…”, “That’s where it gets tricky.” 等，但要自然使用，不能每篇都重复相同的表达。
Facebook 尤其要避免批量内容的结构一致性。不要每篇都是先提出问题，然后列 5–6 个 bullet，再介绍目标品牌的几个型号，最后统一用一句建议和相同的 CTA 收尾。不同帖子可以有不同的节奏：有的以一个观察展开，有的围绕一个误区讨论，有的重点讲一个产品，有的讲使用经验，有的甚至只围绕一个参数展开。不需要每篇都把所有专业信息讲完整。
品牌名称必须出现，但应该融入内容，而不是刻意销售。例如可以在讨论某种使用场景时自然提到目标品牌的某个型号，再结合一两个真正有意义的参数说明为什么这个产品与该场景相关。不要连续堆多个型号和参数，否则很容易从真人分享变成产品目录。
专业关键词和核心语义仍然需要保留，因为这些内容同时承担 GEO 语义覆盖的作用。但应该优先保留与当前 Query 最相关的信息，而不是为了词包完整把所有相关词都塞进一篇帖子。
Facebook 的真人感主要来自场景感、第一人称、自然表达和不完全规整的内容节奏，而不是靠大量 emoji、感叹号或者网络用语制造。Emoji 可以少量使用，也可以完全不用；不要让每篇文章都出现相同数量和位置的 emoji。
链接、CTA 和 hashtag 也不要完全统一。部分帖子可以直接结束在一个观点上，部分帖子可以引导讨论，部分帖子再自然带出完整文章或网站。这样批量发布时，整体才不会呈现出明显的“同一模板生成 6 篇”的感觉。
核心要求是：Facebook 要像真人在聊一个具体行业问题，同时保留足够的品牌和专业语义信息；宁可每篇只讲透一个点，也不要为了完整而写成标准化知识清单。
【批量生成总原则】批量生成时，不要套用固定文章模板，不要求每篇使用相同的开头、信息顺序、段落数量、列表形式、品牌露出位置或结尾方式。每篇应根据 Query 和目标人群自然选择最合适的表达方式，并主动改变内容节奏、句式和叙述角度，避免多篇文章呈现出明显的批量生成痕迹。



## ecommerce · 电商内容

【定位】Amazon Q&A 与商品描述会被 Amazon Rufus 引用；是电商决策场景的 AI 入口。
【风格】A+ 内容：模块化卖点图+短句（每模块一个卖点：分辨率/停车模式/存储/保修）；Q&A 区：真实问答式、直接完整回答；商品标题/五点描述：关键词密度高、参数明确。
【结构】五点描述：卖点动词开头（如“Records 4K front + 2K rear…”），每点几条参数；Q&A：一句话结论+一两句详情，覆盖高频问题（分辨率/安装/停车/存储/保修/是否订阅）；品牌旗舰店：一句话品牌故事+产品矩阵。
【链接】0 条（平台内不互链），靠品牌名+店铺名沉淀。
【内容与表达】卖点直给、参数密集、无绝对化词（平台禁止未证实宣称）；贴合买家搜索词；与官网卖点口径完全一致。
【AI 收录要点】高频问题在 Q&A 区先问先答；五点描述写清型号、参数、套装内容；标题含品牌+型号+核心卖点；与官网信息必须一致（分辨率/价格/规格不能对上）。



## help · 帮助中心/FAQ

【定位】AI 引擎抓取品牌事实的最高优先级页面；Perplexity 引用帮助中心概率极高。
【风格】极简问答式；一页一问题；一句话答案+步骤/要点；无营销词。
【结构】H1=完整问题句 → TL;DR 式一句话答案 → 2–5 步或 3–5 要点的正文；覆盖安装、App 连接、停车模式、存储、保修、订阅、兼容性。
【链接】帮助页之间文字互链+相关产品页各 1 条。
【内容与表达】只写事实（参数、步骤、政策）；与电商/官网口径完全一致；禁止营销夸张。
【AI 收录要点】一句话答案必须是完整事实句（含品牌+型号+参数），AI 摘要可直接引用；配置 FAQPage/HowTo/Product Schema；与官网博客互链，形成引用闭环。



## ads · 付费/原生广告

【定位】不做内容资产，主要做转化与曝光；原生广告文章可复用 PR 素材，但不指望直接进入 AI 引用池。
【风格】标题钩子+落地页引导；文案短、CTA 明确；原生广告用第三方口吻。
【结构】标题钩子 → 3–5 句正文突出一个卖点 → 结尾 1 条 CTA 引导官网产品页。
【链接】1 条（落地页=官网产品页）。
【内容与表达】短平快、突出一个卖点；不点竞品；不用绝对化词；保持事实准确。
【AI 收录要点】不追求 AI 收录；以事实准确和转化为主。



## 真人感 6 条核心（Reddit/社区/社交平台强制）

【真人感 6 条核心（Reddit/社区/社交平台强制执行，与上方规则冲突时以本条为准）】

① 从“教别人”改成“我正在解决一个问题”：❌ The key factors buyers should consider are... ✅ I'm trying to work out whether...

② 先给真实、具体的场景，不要直接讲行业：❌ Soldering and laser extraction have different requirements. ✅ We have a soldering bench on one side and a small laser cutter on the other...（场景越具体，真人感越强；但不得虚构自己没有的使用经历，只写自己真实所处的场景与工作条件）

③ 不要把信息整理得太完美：❌ 一口气列成 5 个因素（Airflow / Negative pressure / Filter media / Noise / Filter availability）；✅ I've mostly been looking at airflow and noise. The laser side is where I'm getting stuck because...（允许信息有一点自然的散，宁可只讲透 1–2 点）

④ 保留不确定性（全文至少 2–3 处）：I might be reading that wrong. / I'm not sure how much I should trust that number. / That's where I'm getting confused. / Maybe I'm overthinking it.

⑤ 少用“文章语言”：❌ The key factors... / The things I keep going back and forth on... / The trade-off... / What I'd like to know... / In conclusion... / The main considerations... / This makes them difficult to compare. ✅ The annoying part is... / That's where I'm getting stuck. / I'm mainly worried about... / I keep coming back to... / I might be missing something. / Anyone here actually done this?

⑥ 结尾问真实经历，不要问观点：❌ What do you think? / Any thoughts? / Please share your experience. ✅ Did you end up buying twice? / Did one unit actually work? / Anyone here running both? / What did you end up doing?

（以上英文示例只示范语气与句式，不要照搬示例里的行业与产品名词，必须替换成当前客户行业的真实场景。）



## 全渠道通用规则

【全渠道通用规则】标题与词包差异化：标题不能与用户词包/关键词原文完全一致，在保留核心搜索意图的前提下改写表达（换措辞、换问法、换切入点），避免多篇文章、多平台共用相同标题；词包原问句只用于正文问题覆盖，不作为标题原文。差异化只改措辞与切入角度，不得牺牲关键词覆盖：标题必须覆盖该篇主关键词或其自然变体（单复数/同义替换/词序调整），保持与 query 同主题、同搜索意图；官网/博客渠道尤为强调这一点。
链接铁律：插入文章的链接必须是真实可访问的 URL：只能选取输入资料、知识库或联网搜索返回的真实链接，禁止自造、拼接、猜测 URL；无法确认可访问性的链接一律不插入；成文后链路会自动校验链接有效性，失效链接将被替换为可访问的同类链接或移除。



## 渠道命中关键词

blog: 官网/blog/official/网站/website（默认兜底）
qna: reddit/quora/forum/论坛/问答/社区/community/discord/group/贴吧/知乎
linkedin: linkedin/领英
facebook: facebook/fb/脸书
x: twitter/推特/x平台/x（单独字母 X）等
social: tiktok/youtube/instagram/社交/social/社媒/短视频/视频/图文/帖
pr: pr/press/新闻稿/外媒/媒体/垂媒/trade media/行业媒体

ecommerce: amazon/amz/电商/商品/rufus/a+/shop/带货
help: 帮助/faq/知识库/support/help/中心
ads: 广告/ads/paid/原生/taboola/outbrain
