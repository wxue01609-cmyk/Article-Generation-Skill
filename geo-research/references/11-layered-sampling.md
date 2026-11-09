# 分层采样（按转化路径）

> 把词包 query 先按转化路径分到三层，再逐条向 ChatGPT（或任意 OpenAI 兼容接口）提问，产出**按层聚合的基线数据**：客户品牌提及率、引用域名、竞品提及、信号（价格/评分/库存/政策）。分层结果同时决定这条 query 的内容应归哪个 stage 生产，与「按转化节点编排生产器」的设计一致。

## 三层定义

| stage | 客户状态 | 典型 query |
| --- | --- | --- |
| `ai_exposure` AI 曝光 | 还没听说过你 | best / top / review / vs / how to / guide |
| `pdp` 转化层（商品详情页） | 已经在看你的产品 | 品牌+型号 + price / specs / what's included |
| `conversion` 对比决策 | 想买但犹豫 | return / refund / warranty / shipping / policy / is it good for |

## 打标规则（打分制，可解释、可人工覆盖）

- 每层一组信号词，命中加分：AI 曝光（best/review/vs/how to/guide +3~2），转化层（price/specs/buy +3~2），对比决策（return/warranty/shipping/policy/support +3，适用性疑虑 +2）。
- 品牌+型号精确命中只是**加成**（+2~+3 pdp、+2 exposure），不决定层级：它只回答「是不是产品相关」，不回答「写在哪」。
- 特殊消解：`best/top ... to buy` → 榜单意图归曝光，抵消 pdp 的 buy 权重；`how to + return/cancel/claim` → 归转化，`how to + install/setup` → 归曝光。
- 主层级 = 最高分；次层级 = 第二高分且 ≥2 分、与主层级不同（次层级只做「引用位/原问句嵌入」，不单独造文）。
- 并列时优先级：`ai_exposure > conversion > pdp`。
- 人工覆盖：矩阵确认时把 query 从一层拖到另一层 → 记一条覆盖规则 `query → stage`，优先级高于打分。

## 运行

```bash
# 在 geo-research 技能目录内；环境变量同 ask_chatgpt.py
python3 scripts/sample_by_stage.py \
  --queries-file queries.txt \
  --brand Botslab --model G980H \
  --competitors "70mai,Vantrue,Thinkware" \
  --out research/sampling.json
```

参数：
- `--queries-file` 必填，词包文件每行一条 query
- `--brand` / `--model` 客户品牌与主力型号（提及检测 + 打标加成）
- `--competitors` 竞品白名单（逗号分隔），用于统计 AI 答案里提到哪些竞品
- `--limit N` 最多采样 N 条（调试/控制成本）
- `--out` 输出路径，默认 `research/sampling.json`

## 输出结构

```json
{
  "generated_at": "2026-11-04 20:00:00",
  "model": "gpt-4o-mini",
  "brand": "Botslab",
  "stages": {
    "ai_exposure": { "count": 2, "mention_rate": 0.5, "cited_domains": [], "brands_mentioned": ["Vantrue"] },
    "pdp": { "count": 1, "mention_rate": 1.0, "cited_domains": [], "brands_mentioned": [] },
    "conversion": { "count": 1, "mention_rate": 1.0, "cited_domains": ["botslab.com", "amazon.com"], "brands_mentioned": [] }
  },
  "items": [
    {
      "query": "Botslab G980H return policy",
      "question": "What is the Botslab G980H return policy?",
      "stage": "conversion",
      "secondary_stage": "pdp",
      "scores": { "ai_exposure": 2, "pdp": 4, "conversion": 6 },
      "answer_summary": "…",
      "mentions_client": true,
      "brands_mentioned": [],
      "cited_urls": ["https://www.botslab.com/..."],
      "cited_domains": ["botslab.com"],
      "signals": { "price_mentioned": false, "rating_mentioned": false, "availability_mentioned": false, "policy_mentioned": true },
      "error": ""
    }
  ]
}
```

字段说明：
- `stages.*.mention_rate`：该层 query 的 AI 回答里提及客户品牌/型号的比例（0~1）
- `stages.*.cited_domains` / `brands_mentioned`：引用域名 Top8 / 竞品提及 Top8，供诊断判断「引用来源集」和「竞品席位」
- `items[].signals`：价格/评分/库存/政策是否被 AI 提及，转化层看价格与评分、对比决策层看政策
- `items[].secondary_stage`：次层级，只做引用位/原问句嵌入

## 谁消费这份数据

- `geo-plan` / `geo-content-plan`：按 `stage` 决定 query 归哪层生产；`secondary_stage` 决定在哪层资产里嵌入原问句
- `geo-diagnose`：分层基线（上线前）与下线后监测对比，判断卡在哪一层——曝光不足 / 商品卡没上 / 转化弱
- 写入任务目录 `research/sampling.json`，随任务存档，可回放对比

## 注意事项

- 采样模型默认 `gpt-4o-mini`，只代表「当前采样模型的答案」，不代表真实用户在所有平台看到的结果；需要更接近真实基线时换 `CHATGPT_MODEL` 或用监测平台导出数据。
- 回答原文只做核验与基线统计，**不直接写入下游文章**；`answer_summary` 用于追溯。
- 引用链接默认只记录；平台侧采样可选择抓取被引用页面摘要，落到 `research/citations.json`（`items` 含 `title`/`url`/`domain`/`stage`/`headings`/`excerpt`/`status`），供 `geo-content-plan` 的 `reference_citations` 与 `geo-diagnose` 回流使用；无抓取能力时省略该文件，不阻塞主流程。
- 引用内容只允许借鉴结构与证据点类型，禁止把原文句子写进下游成稿。
