# 搜索意图分类表

## 一级意图
| intent | 中文 | 典型信号 | 用户阶段 | 常见内容形态 |
|---|---|---|---|---|
| informational | 信息型 | how / what / why / guide / explained / tips / mistakes / benefits / types of / 怎么 / 为什么 | TOFU | 博客、FAQ、类目教育 |
| commercial | 商业调研 | best / top / review / compare / vs / alternatives / which / worth it / for [use case] / 推荐 / 对比 | MOFU | 三方评测/对比、官网购买指南 |
| transactional | 交易型 | buy / price / cost / quote / discount / deal / for sale / near me / shipping / 购买 / 价格 | BOFU | SKU/产品页、落地页、电商 Listing |
| navigational | 导航型 | 品牌名 / 型号 / official / login / download / manual / 官网 | BOFU | SKU/产品页、品牌落地页 |
| support | 支持型 | how to use / install / setup / troubleshoot / error / not working / compatible / warranty / 故障 | 售后 | 帮助中心 FAQ、教程 |
| community | 口碑型 | reddit / forum / experience / is it legit / complaints / anyone used / 真实体验 | MOFU | 社区问答、三方讨论 |
| news | 新闻型 | launch / new / release / partnership / award / funding / 发布 | 认知 | 三方 PR、新闻稿 |
| local | 本地型 | near me / in [city] / service area / local installer / 本地 | BOFU | 本地落地页 |

## 判定顺序（冲突时按此优先级）
1. 品牌/型号 + 购买/价格/规格信号 → `navigational` 或 `transactional`（有明确购买动词取 transactional）
2. 故障/安装/兼容/保修信号 → `support`
3. vs / alternatives / best / review / compare → `commercial`
4. reddit / forum / experience / legit → `community`（若同时有 commercial 信号，仍归 community，渠道不同）
5. launch / release / award / partnership → `news`
6. near me / 城市 + 服务 → `local`
7. how / what / why / guide / types / benefits → `informational`
8. 只有品类词/复数名词 → `commercial`（品类调研）或 `informational`（品类教育），按是否有购买修饰词判断

## 置信度
- `0.90-1.00`：同时命中 2 个以上强信号（如 `buy + price`、`vs + 两个品牌`）
- `0.70-0.89`：命中 1 个强信号 + 上下文一致
- `0.50-0.69`：只有弱信号，需人工复核（`needs_review: true`）
- `<0.50`：不猜，直接进 `gaps`，`reason=intent_unclear`

## 多语言/市场
- 按 `target_market` 与 `article_language` 判断；非英文 query 同样按语义映射，不按字面翻译。
- 西语/德语/日语等的购买词（comprar / kaufen / 購入）按 transactional 处理。
- 本地意图只在 `target_market` 覆盖该地区时成立，否则进 gaps。

## 必须写证据
每个 item 的 `intent_signals` 至少 1 条，写具体词或结构，例如：
- `["contains 'vs'", "two brand entities"]`
- `["starts with 'how to'", "no purchase modifier"]`
- `["brand name + 'price'"]`
禁止只写“根据语义判断”。
