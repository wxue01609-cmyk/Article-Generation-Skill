# ChatGPT 接口配置（直接提问）

> 供「AI 问答结构提取」步骤使用：把词包关键词直接发给 ChatGPT 对话接口拿回答。任何 OpenAI chat/completions 兼容接口均可（OpenAI 官方、OpenRouter、DeepSeek、360、通义等），只需改环境变量。

## 环境变量（配置在运行环境中，绝不写入仓库）

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| CHATGPT_API_KEY | 是 | 接口密钥（如 OpenAI API Key） |
| CHATGPT_API_BASE | 否 | 默认 https://api.openai.com/v1；其他厂商填其 OpenAI 兼容地址 |
| CHATGPT_MODEL | 否 | 默认 gpt-4o-mini；其他厂商填对应模型名 |
| CHATGPT_TIMEOUT | 否 | 单次请求超时秒数，默认 120 |

## 配置方式
- 终端运行：`export CHATGPT_API_KEY=sk-...`，想持久化就写进 `~/.zshrc` 或 `~/.bashrc`。
- Codex 桌面端：在环境变量设置中配置，或由启动本进程的终端注入。
- 脚本读取当前进程的环境变量；不要在仓库里创建并提交含密钥的 `.env`（本仓库 `.gitignore` 已忽略 `.env`）。

## 验证
```bash
python3 scripts/ask_chatgpt.py --question "What is the best LED screen for a warehouse?"
```
成功 → 输出 JSON 数组，每项含该问题的回答；失败 → 输出明确错误（缺密钥 / 网络 / 模型不存在）。

## 常见问题
- 401/403：CHATGPT_API_KEY 无效或额度不足。
- 400/404：CHATGPT_API_BASE 或 CHATGPT_MODEL 与该厂商不匹配。
- 超时：调大 CHATGPT_TIMEOUT，或换响应更快的模型。
