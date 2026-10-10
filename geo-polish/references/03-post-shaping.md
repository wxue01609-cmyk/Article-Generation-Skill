# 社交帖子形态兜底（S-post 摘要）

来源：S-post 社交帖子形态兜底（与写作提示词的帖子模式互为双保险）。

## 触发渠道
publish_media 含：reddit / quora / forum / 论坛 / 问答 / 社区 / community / discord / group / 贴吧 / 知乎 / 社交 / social / tiktok / youtube / instagram / twitter / 短视频 / 视频 / 图文 / x平台 / 帖

## 确定性清洗（按序）
1. 整表删除（社交/社区渠道不允许表格）
2. TL;DR 段落删除
3. 所有 h1-h6：去标签留文字
4. 链接：去标签留锚文本（社交渠道 0 链接）
5. strong / b / em / i：去标签留文字
6. 空段落删除、多余空行收敛

## 真人感 6 条核心（REAL6，Reddit/社区/社交平台强制执行）
① 从「教别人」改成「我正在解决一个问题」：❌ The key factors buyers should consider are... ✅ I'm trying to work out whether...
② 先给真实、具体的场景，不要直接讲行业（场景越具体越好；不得虚构自己没有的使用经历）
③ 不要把信息整理得太完美，允许自然发散，宁可只讲透 1-2 点
④ 保留不确定性（全文至少 2-3 处）：I might be reading that wrong. / I'm not sure how much I should trust that number. / Maybe I'm overthinking it.
⑤ 少用「文章语言」（❌ The key factors... / In conclusion... / The main considerations...；✅ The annoying part is... / I keep coming back to... / I might be missing something.）
⑥ 结尾问真实经历，不要问观点：❌ What do you think? / Any thoughts? ✅ Did you end up buying twice? / Anyone here running both? / What did you end up doing?
（英文示例只示范语气与句式，不得照搬示例里的行业与产品名词，必须替换成当前客户行业的真实场景。）
