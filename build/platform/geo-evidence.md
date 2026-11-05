## 平台落位
- 证据账本 `evidence/ledger.json` 的等价内容放进输出 `notes`（按 claim 列出）或矩阵 Brief 的 `proof_points`；只在正文里写 `verified` 且 `approved_for_publication=true` 的 claim。
- 客户待确认项输出到 `notes` 的 `pending_confirmations`（问题 + 建议默认值），不下「待核验」占位进正文。
- 证据来源优先：抓取页面原文 > 企业知识库 > 产品知识库 > 权威第三方；与抓取页面矛盾的旧信息以抓取页面为准并记录差异。