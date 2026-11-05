## 平台落位
- 调用工具 `geo_render_html`：mode=asset 出整页、mode=modules 出商品页模块片段、mode=compare 出改前改后对比页；把渲染结果放进 `assets` / `sku_changes` 对应字段。
- 渲染只按规则做结构与样式，不改写正文事实。