---
name: geo-polish
description: 海外 GEO 生文流水线最后阶段（质检与后处理）。对生成的文章做合并容错、违禁词清洗、链接可用性校验与失效替换、社交帖子形态兜底、机械质检，输出可直接发布的最终文章。当文章已生成、需要清洗/校验链接/质量检查时使用。
---

# GEO 质检与后处理（geo-polish）

来源：Dify 工作流「海外GEO生文-wx-360gpt-v18-13」最后阶段（articles-merge 合并输出 → N8-pre 文章清洗 → L-extract/L-verify/L-parse/L-replace 链接校验 → S-post 社交帖子兜底 → N8 结果合并）。

## 执行流程（严格按序）

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
