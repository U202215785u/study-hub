---
name: browser-extension-login-session
description: 浏览器插件利用用户已登录态采集数据，比服务端爬虫更稳定
metadata:
  type: reference
---

## 模式：浏览器插件 + 用户登录态采集

当需要从需要登录的网站批量采集数据时，优先用浏览器插件方案而非服务端爬虫。

**Why:** 服务端爬虫需要模拟登录、维护 Cookie、处理验证码，且随时被反爬机制封禁。浏览器插件直接利用用户已有的登录会话，天然绕过这些问题。

**How to apply:**
1. 在已有 Chrome 扩展中新增针对目标网站的内容脚本逻辑
2. 扩展检测用户是否在目标页面 → 提供一键采集按钮
3. 内容脚本直接操作 DOM 提取数据（用户已登录，页面数据完整）
4. 扩展通过 background.js 代理请求发送到后端 API

**已成功应用的案例:**
- [[douyin-favorites-import]] — 抖音收藏页批量采集视频链接
