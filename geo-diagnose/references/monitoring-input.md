# 监测结果输入规范（geo-diagnose 只读不采）

答案数据由 **geo-monitoring 或客户使用的监测平台** 导出，本流水线不自行采样、不调用 AI 接口。`normalize_monitoring.py` 把各种导出格式映射成统一的 `diagnosis/responses.jsonl`（字段见本目录 [`artifact-contracts.md`](artifact-contracts.md) 第一节）。

## 一、支持的文件格式
- `.jsonl`：每行一条答案记录。
- `.json`：数组，或含 `results` / `responses` / `data` / `items` / `records` 数组的对象。
- `.csv` / `.tsv`：每行一条答案记录（UTF-8，可带 BOM）。

## 二、最低字段要求

| 标准字段 | 必需 | 说明 |
|---|---|---|
| `question_id` 或 `question_text` | 必需其一 | 用来关联问题文件；只有问句文本时按归一化文本匹配 `monitoring_prompt` / `user_question` |
| `engine` | 必需 | 平台名；可用 `engine_values` 映射成标准取值 |
| `answer_text` | 必需 | 答案全文；缺失时无法推断提及与排位 |
| `run_index` | 建议 | 第几次采样；用于确认每题采样次数 |
| `collected_at` | 建议 | 采集日期；用于基线与观察窗口 |
| `market` | 可选 | 缺省取问题的 `region` 或 contract 第一个市场 |
| `citations` | 强烈建议 | 引用 URL 列表；没有它就无法做来源诊断 |
| `brand_mentioned` / `brand_position` / `brands_mentioned` | 可选 | 平台已计算时直接使用，否则从 `answer_text` 推断 |
| `product_cards` | 电商强烈建议 | 商品卡列表（标题、品牌、商家、URL、价格、位置）；电商场景缺失时无法判定 `not_in_product_pool` |
| `sentiment` | 可选 | positive / neutral / negative |
| `accuracy_flags` | 可选 | 平台或人工标注的事实错误 |

## 三、字段映射文件（mapping.json）

导出字段名与标准字段不同时，在 `contract.inputs.monitoring_results[].mapping` 指向一份映射文件：

```json
{
  "fields": {
    "question_id": "prompt_id",
    "question_text": "prompt",
    "engine": "platform",
    "run_index": "run",
    "collected_at": "date",
    "answer_text": "response",
    "market": "country",
    "brand_position": "brand_rank",
    "sentiment": "sentiment"
  },
  "engine_values": {"ChatGPT Search": "chatgpt", "Google AI Overview": "google_aio"},
  "brand_mentioned": {"field": "brand_visible", "true_values": ["yes", "true", "1"]},
  "citations": {"field": "sources", "format": "json"},
  "brands_mentioned": {"field": "mentioned_brands", "format": "delimited", "delimiter": ","},
  "product_cards": {"field": "shopping_results", "format": "json"},
  "accuracy_flags": {"field": "errors", "format": "delimited", "delimiter": "|"}
}
```

- `format: json`：单元格内是 JSON 数组（元素可以是 URL 字符串或对象）；`format: delimited`：按 `delimiter` 切分的字符串。
- 对象元素的字段名会自动识别：引用 `url` / `link` / `href`、`title`、`position`；商品卡 `title` / `brand` / `merchant`（或 `seller`）/ `url` / `price` / `position`。

## 四、首次接入新平台的步骤
1. 让使用者提供一份真实导出样例（至少 20 行）放到 `inputs/monitoring/`。
2. 对照第二节写 mapping.json；字段含义不确定时向使用者确认，不猜。
3. 运行 `normalize_monitoring.py`，检查输出摘要：`unmatched_questions` 应为空，`engines` 计数与导出一致，`derived_mentions` 占比合理。
4. 抽查 5 条 responses.jsonl 记录与原始导出逐字段核对，再进入指标计算。
5. 把验证过的 mapping.json 保存为该平台的固定映射，后续项目复用。

## 五、数据充分性
- 每个问题建议 ≥3 次采样、覆盖目标市场的主要平台；问题文件为 `locked` 状态。达不到时诊断的 `evidence_level` 只能是 `hypothesis`。
- 单次采样的结论不得写成“AI 不推荐品牌”这类确定表述，只能写“本次采样中未出现”。
