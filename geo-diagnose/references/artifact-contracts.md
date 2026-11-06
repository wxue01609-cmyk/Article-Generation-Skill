# 交付物字段定义（自包含，替代原 geo-contract 文档）

本文件定义 geo-diagnose 上下游数据文件的字段，避免依赖仓库外的 geo-contract 目录。

## 一、responses.jsonl（AI 答案原始记录，每行一条）

由 `scripts/normalize_monitoring.py` 从监测平台导出格式归一化得到：

```json
{"query": "原问句", "platform": "chatgpt|gemini|perplexity", "answer": "AI 回答正文",
 "cited_sources": [{"title": "…", "url": "https://…", "domain": "…"}],
 "product_cards": [{"brand": "…", "model": "…", "title": "…", "price": "…"}],
 "brand_mentions": ["…"], "collected_at": "2026-11-06"}
```

## 二、topic_metrics.json（按问题族统计）

由 `scripts/compute_topic_metrics.py` 从 responses.jsonl 聚合：

```json
{"topics": [{"topic": "问题族", "queries": ["…"], "responses": 12,
   "brand_mentions": 5, "mentions_pct": 0.42,
   "cited_domains": [{"domain": "example.com", "count": 3}],
   "product_cards": 2, "cards_pct": 0.17,
   "failure_layers": ["ai_exposure"], "confidence": "high"}],
 "meta": {"generated_at": "2026-11-06", "source_file": "responses.jsonl"}}
```

## 三、diagnosis.json（模型最终诊断）

```json
{"version": "1.0", "diagnosed_at": "2026-11-06",
 "topics": [{"topic": "…", "stage": "ai_exposure|pdp|conversion", "issues": ["unbranded_mentions"],
   "evidence": "一句话依据", "recommend_actions": ["…"]}],
 "summary": {"total_topics": 1, "blocking": 0}}
```

## 四、场景审计项（scenario-packs）

按仓库内 `references/site-audit.md` 执行站点与场景专属审计；无独立 scenario-packs 文件，场景差异项已并入 site-audit.md 与 failure-layers.md。
