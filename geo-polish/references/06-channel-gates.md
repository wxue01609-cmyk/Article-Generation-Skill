# 按渠道的质检关卡（改动卡模式）

改动卡模式下，geo-polish 对每张卡的交付物跑五个关卡，结果写入 `qa/<change_id>.json`。脚本 `scripts/check_deliverable.py` 负责确定性检查；标「人工」的项由模型逐项核对后写入 issues。任何关卡为 fail，改动卡置为 `qa_failed` 并退回生产 skill；全部通过后仍需**人工审批**才能置为 `approved`。

## 一、五个关卡

| 关卡 | 脚本检查 | 人工检查 |
|---|---|---|
| Fact 事实 | `claims_used` 全部存在且 verified + approved；正文中的金额、百分比能在所用 claim 中找到；对比页点名竞品时必须用到 `competitor_fact` | 每个参数、认证、政策、客户名、竞品事实与 claim 数值和限定词一致；没有拼接独立事实；型号与规格对应 |
| Evidence 证据 | 证据账本中该卡覆盖为 ok；所用 claim 未过期（价格 ≤30 天） | 引用的来源日期是否仍然有效（竞品信息建议 90 天内） |
| Extractability 可提取 | core_answer 存在、20-120 词、包含品牌或目标对象名、出现在正文中；单一 H1；JSON-LD 可解析 | 每个 H2 首句是结论；关联问题族的核心问法都有直接答案；至少一处限制/不适用说明；正文不依赖 JS 渲染 |
| Channel 渠道 | 占位符、内部标签泄漏；绝对化词；文章中的硬 CTA；第三方简报写明披露要求；geo-offsite 的合规自查记录；竞品点名许可；禁用 claim | 是否符合目标渠道写法（PDP / 落地页 / 博客 / 第三方平台规则）；合规叠加层的表述限制 |
| Distribution 分发 | 目标 URL；落地页/文章的内链计划；业务 KPI；对照组 | 上线位置、负责人、上线时间是否明确；需要同步修改的其他位置（feed、Amazon、目录）是否列出 |

## 二、按资产类型的额外检查

| 资产 | 额外检查 |
|---|---|
| `pdp_rewrite` | 参数表为 HTML 文本；购买信息（物流/退货/保修）可见；评分只来自 `review_stat` claim |
| `product_feed` | `geo-pdp/scripts/check_feed.py` 无 error |
| `product_schema` | `geo-pdp/scripts/check_product_schema.py --feed --page` 无 error |
| `comparison_page` / `alternatives_page` | comparison-rules.md 前置条件满足；`legal_review_required` 标记 |
| 博客文章（geo-write） | 同时跑 `scripts/check_article.py`（词数档位、标题、价格、CTA） |
| geo-offsite 各类 | 披露要求、参与者身份真实、平台规则链接；不得出现代写评论或虚构身份的指示 |
| `tech_ticket` | 问题、影响、修复建议、验收方法齐全 |

## 三、运行
```bash
python3 scripts/check_deliverable.py --project <项目目录> --change <change_id> --write
```
再按资产类型补跑对应脚本，最后把人工检查结论补入 `qa/<change_id>.json` 的 issues。

## 四、人工审批
`human_approval.required` 始终为 true。对比页、合规叠加层、`legal_review_required` 的交付物额外需要法务审核（`legal_review_required: true`）。审批人和时间填入后，改动卡才能置为 `approved`，进入上线与 geo-measure。
