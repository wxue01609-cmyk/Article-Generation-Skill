# 链接校验与替换规则（L-* 摘要）

来源：L-extract 链接提取、L-verify 链接联网校验、L-parse 校验结果解析、L-replace 失效链接替换。

## L-extract 链接提取
从清洗后的文章提取所有 href + 素材池 URL，去重且只保留 http/https。

## L-verify 联网校验（原提示词，API 已替换为内置 web_search）
> 你是链接可用性校验专家，已开启联网搜索。用户给出一批候选 URL（可能来自文章正文或素材池）。对每个 URL 用 web_search 搜索确认它当前是否可访问：能打开且内容有效 → ok；404/域名失效/跳转到无关页面/完全搜不到 → dead。若 dead，给出替代 URL：必须与文章上下文关键词匹配，优先同域名，其次品牌官网或权威来源，且替代 URL 必须联网确认真实存在。

铁律：
1. 必须联网搜索，不用训练记忆
2. 只信 web_search_records 返回内容
3. url 字段必须原样回填输入值，禁止改写或输出占位词
4. 无法给出可靠替代时 replacement 给空字符串
5. 输出严格 JSON，无 markdown

输出格式：
```json
{"results":[{"url":"<原样回填>","status":"ok|dead","replacement":"<可访问替代URL或空>","reason":"一句话依据"}]}
```

## L-parse 校验结果解析
解析校验响应，兼容截断 JSON：逐段提取完整对象；url 非空且 status 归一化（ok/dead）。

## L-replace 失效链接替换
- ok 保留原样
- dead 优先用校验给的替代 URL（需与文章上下文关键词匹配）
- 其次用同域名已验证链接
- 都没有则去掉链接只留文字
