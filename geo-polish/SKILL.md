---
name: geo-polish
description: 海外 GEO 质检与后处理。三种模式：①批量模式——对生文线文章做合并容错、违禁词清洗、链接校验替换、社交帖子兜底、机械质检；②改动卡模式——对 SKU 改造交付物跑事实/证据/可提取/渠道/分发五关；③全链路模式——对内容建设按 stage 分组的成稿包做五关质检并出 polish_report.json。当文章或内容资产已生成、需要质检时使用。
---

# GEO 质检与后处理（geo-polish）

来源：Dify 工作流「海外GEO生文-wx-360gpt-v18-13」最后阶段（articles-merge 合并输出 → N8-pre 文章清洗 → L-extract/L-verify/L-parse/L-replace 链接校验 → S-post 社交帖子兜底 → N8 结果合并）。

## 执行流程（严格按序）

> 模式选择：批量生成的文章 → 走下方步骤 1-6（批量模式）；SKU 改造交付物 → 走「改动卡模式」；**内容建设成稿包（按 stage 分组）→ 走文末「全链路模式」**。

### 步骤 1 合并与截断容错
- 聚合标准版 + 品牌版等全部文章为 all_articles；任一文章 JSON 截断未闭合时，用正则提取 title/content/description 兜底，并在 self_review 标记截断。
- 规则见 [references/05-output-merge.md](references/05-output-merge.md)。

### 步骤 2 文章清洗（N8-pre）
- 违禁词替换字典（最字系列/一字系列/级首系列/通用极限词，长词优先替换）
- HTML 规范化：标签名小写、b→strong、斜体脱壳、嵌套 strong 扁平化
- 删除工作流内部标签（结构/开篇/视角/分组标签与内部字段名）与 SKIP 占位标记、残留清理
- 规则与示例见 [references/01-cleaning.md](references/01-cleaning.md)。

### 步骤 3 链接校验（L-*）
1. L-extract：提取文章全部 href + 素材池 URL，去重且只保留 http/https
2. L-verify：逐个 URL 用内置 web_search 确认可访问（原工作流调 360 API，此处规则不变）：能打开且内容有效 → ok；404/域名失效/跳转无关页/搜不到 → dead，并给出替代 URL（与文章上下文关键词匹配，优先同域名，其次品牌官网或权威来源，替代 URL 必须联网确认真实存在）
3. L-parse：解析校验结果，兼容截断 JSON，逐段提取完整对象
4. L-replace：ok 保留；dead 优先用校验给的替代 URL，其次同域名已验证链接，都没有则去掉链接只留文字
- 提示词原文与规则见 [references/02-link-check.md](references/02-link-check.md)。

### 步骤 4 社交帖子兜底（S-post）
- publish_media 命中社交/社区渠道时：整表删除、删 TL;DR 段、h1-h6 去标签留文字、链接去标签留锚文本、加粗斜体去标签、空段落收敛。
- 与写作提示词的帖子模式互为双保险；真人感 6 条（REAL6）见 [references/03-post-shaping.md](references/03-post-shaping.md)。

### 步骤 5 机械质检（N8 结果合并）
- 标题：禁止 [____]/[待补充]/{keyword} 等占位符、禁止营销词、禁止冒号/半截词结尾
- 正文：禁止 ** 残留、占位符泄漏、价格信息、内部骨架标注（approx_words/全文目标字数）、软广免责声明、内部标签、CTA 转化话术（立即购买/加微信等）、绝对化营销词（best/#1/revolutionary/ultimate 等）
- 词包覆盖：正文问句 ≥2；奖项/资质表述与画像核证结果一致
- 主题覆盖（文章 JSON 含 topic 时）：核对文章所属主题的每个 query 在正文有实质覆盖，缺漏的在自评中标记并补足；质检报告注明每篇文章的主题归属
- 机械检查项与 LLM 自评合并为 quality_score
- 完整检查清单见 [references/04-quality-check.md](references/04-quality-check.md)。

## 输出
最终文章 JSON：title / content（HTML，已清洗）/ description / tags / self_review / fact_sources / quality_score，可直接发布。

### HTML 文件组装（保存 articles/第N篇.html 时必须执行）
- 完整 HTML 必须包含 <!DOCTYPE html> 与 <head>（meta charset / viewport / description / title），正文放在 <body><article>。
- <head> 内必须注入表格样式（固定内容，缺则补）：
<style>
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px; }
th, td { border: 1px solid #d0d7de; padding: 6px 10px; text-align: left; vertical-align: top; }
th { background: #f6f8fa; font-weight: 600; }
</style>

### 步骤 6 表格样式校验（追加在机械质检之后）
- 对每一篇含 <table> 的文章 HTML：<head> 内必须已注入上方表格样式，缺则就地补入，再保存。

## 改动卡模式（SKU 改造 / 内容优化交付物）

整套流水线（SKU 改造通道）：geo-contract → geo-diagnose → geo-strategy → geo-evidence → 生产类 → **geo-polish** → geo-measure。

对每张 `status=in_production` 的改动卡：
1. 运行 `python3 scripts/check_deliverable.py --project <项目目录> --change <change_id> --write`，按资产类型补跑对应脚本（博客跑 `scripts/check_article.py`；feed 与 schema 跑 geo-pdp 的 `scripts/check_feed.py` / `scripts/check_product_schema.py`；有外链时跑 `scripts/check_links.py`）。
2. 按 [references/06-channel-gates.md](references/06-channel-gates.md) 完成人工检查项，补入 `qa/<change_id>.json`。
3. 任一关卡 fail：改动卡置为 `qa_failed`，把问题清单退回对应生产 skill；修改后重跑。
4. 全部通过：改动卡为 `qa_passed`，提交人工审批（对比页、合规叠加层、法务要求的交付物另需法务审核）。审批完成后填写 `human_approval` 并把卡置为 `approved`，交给 geo-measure。脚本不会自动审批。

内容建设通道的全链路质检见下节；SKU 资产的证据编号（`evidence_id`）在「全链路第 2 关」按 evidence 账本校验。

## 全链路模式（内容建设成稿包）

适用：`geo-content-write` 产出的 `assets/` + `assets/asset_index.json` + `assets/stage_index.json` + `packs/<stage>/manifest.json`。**按 stage 分单元跑**，每层独立出结论，不因某层不过而卡住其它层。

### 五关（每关都要给 pass / warning / blocking）
| 关 | 检查什么 | blocking 判定 | 修复动作 |
| --- | --- | --- | --- |
| 1 事实 | 正文数字/参数/政策是否能在 brief、知识库或证据账本找到来源 | 出现无来源的具体数字、价格、认证、评分 | 删改无来源内容或降级为定性表述；SKU 改造走 notes |
| 2 证据 | SKU：改后属性带 `evidence_id` 且能在 `evidence/ledger.json` 查到 `verified` + `approved_for_publication=true` 的 claim（有账本时）；普通资产：每条 proof_point 有出处 | 有账本但改后属性无 `evidence_id` / 编号在账本查不到或未通过核验 | 回退该属性或补证据；**无账本（geo-evidence 已注明跳过）时降为 warning**，在 checks 注明「未建账本，仅用抓取值」 |
| 3 可提取 | answer-first：首段是否给结论、H2 是否可被单独引用、是否有可摘取清单/表格 | 首段无结论且全文无结构化要点 | 补结论段/摘要段 |
| 4 渠道 | 官网资产无竞品名与对比表；三方评测有披露；社区问答 0 链接 0 促销 | 官网资产出现竞品名 | 改写为类别级判断 |
| 5 分发 | `asset_index.json` 与磁盘文件一一对应、`stage_index.json` 与 index 一致、字数 ±20%、站外链接 `target="_blank" rel="noopener"` | 索引与文件对不上 / 字数超范围 | 补索引或补内容 |

### 输出 polish_report.json
```json
{
  "version": "1.0",
  "generated_at": "2026-11-04 20:30:00",
  "by_stage": {
    "ai_exposure": {"assets": ["blog-01"], "blocking": [], "warnings": [{"asset_id": "blog-01", "gate": "3", "detail": "首段无结论"}], "pass": false},
    "pdp": {"assets": ["sku-01"], "blocking": [], "warnings": [], "pass": true},
    "conversion": {"assets": ["faq-01"], "blocking": [], "warnings": [], "pass": true}
  },
  "summary": {"blocking": 0, "warnings": 1, "gate_pass_rate": 0.93}
}
```
- 有 `blocking` 的层不得进入交付；`warning` 记入 `checks` 后放行。
- 修复后只重跑该层的质检，已 pass 的层不重复跑。
- 详细检查项与判定话术见 [references/06-content-build-check.md](references/06-content-build-check.md)。
