---
name: geo-asset-render
description: 资产 HTML 渲染。把内容文本（Markdown 或结构化内容）渲染成完整可发布 HTML，以及衍生的模块片段、整页模板与改前改后对比页骨架；所有样式内联、响应式、无外链依赖。
---

# 资产 HTML 渲染（geo-asset-render）

## 任务
把内容文本（Markdown 或结构化内容）渲染成**完整可发布 HTML**，以及衍生的模块片段、整页模板与对比页骨架。所有样式内联，无外链依赖。

## 输入
- 正文内容（Markdown 或 HTML 片段）
- `asset_type`（blog / landing / sku / category / pr / review / community / social / listing / faq）
- `title`（页面标题）；需要时提供站点名/导航/页脚用于整页模板

## 输出

### 1. 完整 HTML（普通资产）
```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>标题</title>
<style>/* 全部内联样式，响应式 */</style>
</head>
<body>…语义化正文…</body>
</html>
```

### 2. 模块片段（SKU 用）
按 `<!-- module: 标题 -->` / `<!-- module: 核心答案 -->` 等注释分块输出；动态商品字段用 `{{product.title}}`、`{{price}}` 占位，静态文案直接写好，可直接粘贴进商品页后台。

### 3. 整页模板（接商品系统）
站点壳（站点名、导航、页脚）+ 商品页模块；动态字段全部 `{{...}}` 占位，顶部加一段数据映射说明注释（`product.title → {{product.title}}`）。

### 4. 改前改后对比页
左右切换/上下对照展示「改前原文 vs 改后文案」，绿色高亮改动点，顶部图例说明标注含义，底部逐项依据表（模块 / 改前 / 改后 / 解决的问题）。

## 渲染规则
- 正文用语义化标签 `h1/h2/h3/p/ul/ol/table/blockquote`；CTA 用可见按钮样式。
- 禁止外链 CSS/JS/字体；图片用 `<img src="真实URL" alt="…">`，没有真实图就占位不编造。
- 所有指向站外的链接（CTA、商品页、政策页、第三方来源）必须带 `target="_blank" rel="noopener"`：页面可能被嵌在预览 iframe 中，站外站点会拒绝被嵌入而显示「拒绝连接」。
- 移动端可读（响应式断点）；表格可横向滚动。
- 输出完整闭合标签；禁止残留 Markdown 符号（`**`、`| 表格 |`）。
- 内容不在本次渲染范围内的部分不得改动。
