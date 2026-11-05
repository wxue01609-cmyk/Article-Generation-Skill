# 站点与场景审计清单

`audit_site.py` 覆盖可自动检查的部分；下表中标「人工」的项由模型根据页面内容、客户资料或使用者确认完成，结果写入 diagnosis.json 的 `site_findings` 或对应 topic 的 `scenario_findings`。

## 一、内核审计（所有场景）

| 项 | 方式 | 不通过的影响 |
|---|---|---|
| robots.txt 对搜索类 AI 爬虫（OAI-SearchBot、ChatGPT-User、PerplexityBot、Claude-SearchBot、Googlebot、Bingbot）放行 | 脚本 | 页面无法进入 AI 搜索结果，判 `crawl_blocked` |
| 训练类爬虫（GPTBot、ClaudeBot、CCBot、Google-Extended）是否放行 | 脚本记录 | 属客户策略选择，不判失败；在方案中说明利弊 |
| 爬虫 UA 是否被 WAF/CDN 拦截（`--bot-check`） | 脚本 | 同上，判 `crawl_blocked` |
| 页面状态码、跳转链、noindex、canonical | 脚本 | 页面不可收录或权重被转移 |
| 原始 HTML 正文词数（不执行 JS） | 脚本 | 低于 150 词提示内容依赖 JS 渲染，部分 AI 爬虫读不到 |
| title / meta description / 单一 H1 | 脚本 | 主题识别弱 |
| JSON-LD 类型与解析错误 | 脚本 | 实体与商品信息不可机读 |
| sitemap 可访问 | 脚本 | 新页面发现慢 |
| llms.txt | 脚本记录 | 目前没有证据表明它影响引用，只记录，不作为问题 |
| 问题族是否有对应的自有页面、页面是否直接回答核心问法 | 人工 | `not_selected` / `cited_not_mentioned` 的主要原因 |
| 品牌名、品类、核心能力在官网各页面描述是否一致 | 人工 | 实体混淆、描述错误 |

## 二、场景审计

### dtc_ecommerce
| 项 | 方式 |
|---|---|
| Product + Offer（price / priceCurrency / availability）是否存在 | 脚本（`product` 字段） |
| GTIN 是否存在 | 脚本 + feed 导出核对 |
| 页面价格、schema 价格、feed 价格是否一致 | 人工（对照 PDP 导出 / feed 导出） |
| 价格、标题、参数是否在原始 HTML 中（非 JS 渲染） | 脚本词数 + 人工抽查 |
| 变体 URL 是否直接落到对应变体（颜色/尺寸） | 人工 |
| 物流、退货、保修信息在 PDP 可见 | 人工 |
| 评分 schema 与页面展示的评论一致（不得只在 schema 中出现） | 人工 |
| 商品卡上的商家是官网还是 Amazon/零售商 | responses 中的 `product_cards.merchant` |
| Merchant Center / 平台商品目录状态 | 向客户确认 |

### b2b_leadgen / saas_selfserve
| 项 | 方式 |
|---|---|
| 每个方案/产品线是否有独立页面，写明适用行业、规格范围、认证、交付能力 | 人工 |
| 定价页是否可抓取、结构是否清楚（SaaS） | 脚本 + 人工 |
| 集成页、文档是否可抓取（SaaS） | 脚本 |
| G2 / Capterra / Clutch / 行业目录资料是否存在且一致 | 人工（引用来源 + 公开检索） |
| 询盘 / 预约 / 注册入口是否可用 | 人工 |

### local_service
| 项 | 方式 |
|---|---|
| 每个门店是否有独立页面，含 NAP 与营业时间 | 脚本 + 人工 |
| 官网、Google 商家资料、地图、目录站 NAP 是否一致 | 人工 |
| LocalBusiness schema | 脚本 |

### marketplace_seller
| 项 | 方式 |
|---|---|
| AI 答案中的商品卡与引用指向哪个平台 | responses |
| 平台 listing 与品牌站口径是否一致 | 人工（对照 listing 导出） |

### brand_awareness
| 项 | 方式 |
|---|---|
| Organization schema、品牌事实页 | 脚本 + 人工 |
| Wikipedia / Wikidata 等参考来源是否存在、是否准确 | 人工（只记录，不建议营销性编辑） |

## 三、写法
- 网络受限导致 `unreachable` 的页面，写“审计环境无法访问，需人工复核”，不判失败。
- 每条 `site_findings` 写明 URL、问题、严重度（block / high / medium / low）、对应失败层。
