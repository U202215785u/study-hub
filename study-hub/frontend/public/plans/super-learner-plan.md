# 🎓 超级学习管家 — 全栈 Vibe Coding Engineer 科学学习系统

> **使用方法**：每天打开这个文档，找到当天日期对应的任务，按顺序完成。每完成一项就打 ✅。每周日做周回顾。

---

## 📐 科学学习方法论（每次学习前读一遍）

### 🔁 间隔重复系统（对抗遗忘曲线）

| 复习节点 | 做什么 |
|----------|--------|
| 学后 1 天 | 闭卷回答自查表中的所有问题 |
| 学后 3 天 | 重新做一遍本周项目（不借助旧代码，但可用 AI） |
| 学后 7 天 | 口头解释本周核心概念给「想象中的朋友」听 |
| 学后 14 天 | 用本周学到的技术做一个新功能加到旧项目里 |
| 学后 30 天 | 重新阅读本周笔记，补充新的理解 |

### 🎯 主动回忆（代替被动重读）

- **永远不要**「重新看一遍视频/笔记」——那是无效学习
- **正确做法**：合上笔记，用嘴说出「这周我学了什么」，说不出来的地方再去查
- 每个自查表问题都**先闭卷回答**，答不出来再看答案

### 🏗️ 项目驱动原则

- 每个新概念的学完后 24 小时内，**必须**在一个真实的项目里用出来
- 项目可以很小（一个页面、一个 API），但不能跳过
- 项目做完后写 3 句话：我做了什么、遇到什么困难、怎么解决的

### ⏰ 每日学习节奏（推荐时间表）

```
09:00-09:30  复习前一天学的内容（主动回忆 + 自查表）
09:30-11:30  学习新概念（看视频 + 跟着敲代码）
11:30-12:00  整理笔记（用自己的话写）
12:00-13:00  午休
13:00-16:00  项目实战（做本周项目）
16:00-17:00  遇到问题 → 让 AI 解释，不要直接要代码
17:00-17:30  当日回顾（更新笔记，标记不清楚的概念）
```

---

## 🗺️ Phase 0: 心智热身 — Week 1

**本周目标**：建立学习系统、理解计算机世界的基础地图、学会向 AI 问好问题。

---

### 📅 Day 1（周一）— 开发环境搭建

| 时间 | 任务 | 状态 |
|------|------|------|
| 上午 | 安装 VS Code / Cursor | ☐ |
| 上午 | 安装 Node.js（去 nodejs.org 下载 LTS 版） | ☐ |
| 上午 | 安装 Git（去 git-scm.com 下载） | ☐ |
| 下午 | 注册 GitHub 账号 | ☐ |
| 下午 | 注册 Vercel 账号（用 GitHub 账号登录 vercel.com） | ☐ |
| 晚上 | 打开终端，运行 `node -v`、`npm -v`、`git --version`，确认都正常显示版本号 | ☐ |

**今日教程**：无需视频，跟着官方安装引导走即可。

**今日自查**：
- [ ] 我能成功打开终端并运行一个命令
- [ ] 三个版本号都能正常显示

---

### 📅 Day 2（周二）— 互联网是怎么工作的

| 时间 | 任务 | 状态 |
|------|------|------|
| 上午 | 看 CS50 第一讲（B站搜索「CS50 计算机科学导论 第一讲」） | ☐ |
| 下午 | 看视频：BV1kid5BnEPH（2026 计算机网络教学，只看前 1 小时了解网络分层） | ☐ |
| 晚上 | 在笔记本上画出「浏览器 → DNS → 服务器 → 数据库」的流程图 | ☐ |

**📺 B站教程链接**：
- CS50 计算机科学导论：[B站搜索 CS50](https://search.bilibili.com/all?keyword=CS50%20%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%A7%91%E5%AD%A6%E5%AF%BC%E8%AE%BA)
- 计算机网络入门：[BV1kid5BnEPH](https://www.bilibili.com/video/BV1kid5BnEPH/) — 2026全新计算机网络教学

**🔍 今日自查（闭卷回答）**：
- [ ] 当我在浏览器输入 `google.com` 按下回车，大概发生了什么？（用你自己的话说）
- [ ] 什么是 DNS？为什么需要它？
- [ ] 「前端」和「后端」大概是什么？（不用精确，有概念即可）

---

### 📅 Day 3（周三）— 学会用终端 + 建立笔记系统

| 时间 | 任务 | 状态 |
|------|------|------|
| 上午 | 学习终端基础命令：`cd`、`ls`、`mkdir`、`touch`、`rm` | ☐ |
| 上午 | 练习：在终端里创建项目文件夹结构 | ☐ |
| 下午 | 安装 Notion 或 Obsidian，建立学习笔记库 | ☐ |
| 下午 | 写下第一篇笔记：「我今天知道的最重要的 3 件事」 | ☐ |
| 晚上 | 练习 `npm init` 创建一个空项目，然后用 `npm install` 装一个包 | ☐ |

**📺 B站教程链接**：
- 终端/命令行入门：[B站搜索「命令行入门 2025」](https://search.bilibili.com/all?keyword=%E5%91%BD%E4%BB%A4%E8%A1%8C%E5%85%A5%E9%97%A8%202025)

**🔍 今日自查**：
- [ ] `cd ..` 和 `cd /` 有什么区别？
- [ ] `npm install` 做了什么？
- [ ] 我能在终端里创建一个文件夹并在里面创建一个文件吗？

---

### 📅 Day 4（周四）— 学会向 AI 问好问题

| 时间 | 任务 | 状态 |
|------|------|------|
| 上午 | 找一段你之前项目里 AI 生成的代码，粘贴给 Claude，用提示词：「这段代码在做什么？逐行解释，用简单的比喻」 | ☐ |
| 上午 | 同一个代码，再用提示词：「里面有哪些概念我不懂？每个都用 10 岁小孩能听懂的话解释」 | ☐ |
| 下午 | 练习对比模式：「实现一个用户登录功能有几种方式？至少三种，对比优缺点」 | ☐ |
| 下午 | 练习师徒模式：「我想做一个 Todo List，但不要直接给我代码。用苏格拉底式提问引导我思考」 | ☐ |
| 晚上 | 在笔记里总结：「向 AI 提问的 5 个有效技巧」 | ☐ |

**📺 无需视频，今天完全实战练习与 AI 对话。**

**🔍 今日自查**：
- [ ] 我能用至少 3 种不同的方式让 AI 解释同一段代码
- [ ] 我知道什么时候该让 AI 写代码、什么时候该让 AI 教我装门

---

### 📅 Day 5（周五）— 前端后端初体验

| 时间 | 任务 | 状态 |
|------|------|------|
| 上午 | 看视频了解前端三件套：[BV1MvaVzUEuz](https://www.bilibili.com/video/BV1MvaVzUEuz/) — Pink老师2025前端入门（看前 2 小时） | ☐ |
| 下午 | 用 AI 帮你写一个纯 HTML 的个人介绍页面，逐行理解 | ☐ |
| 晚上 | 在笔记里回答：「前端和后端的区别是什么？」（完全用自己的话） | ☐ |

**🔍 今日自查**：
- [ ] HTML 是干什么的？CSS 是干什么的？JavaScript 是干什么的？
- [ ] 为什么不能只用 HTML 做一个好看的网页？

---

### 📅 Day 6（周六）— 周末第一个小项目

| 时间 | 任务 | 状态 |
|------|------|------|
| 全天 | 用 AI 辅助，从零到一做一个个人 Landing Page | ☐ |
| 全天 | 要求：有头像、名字、简介、3 个技能标签、联系方式 | ☐ |
| 晚上 | 写项目复盘笔记 | ☐ |

**项目检查清单**：
- [ ] 页面在浏览器里能打开
- [ ] 我理解 HTML 结构（`<head>` 和 `<body>` 的区别）
- [ ] 我理解 CSS 是怎么让页面变好看的
- [ ] 我能说出至少 5 个今天用的 HTML 标签

---

### 📅 Day 7（周日）— 周回顾 + 下周预习

| 时间 | 任务 | 状态 |
|------|------|------|
| 上午 | 闭卷完成本周全部自查表问题 | ☐ |
| 上午 | 对答不出的概念，回头查笔记/问 AI | ☐ |
| 下午 | 写周总结：「这周我最大的 3 个收获是什么？最大的 1 个困惑是什么？」 | ☐ |
| 晚上 | 整理下周学习计划，提前看 Phase 1 目录 | ☐ |

**📺 提前了解下周内容**：
- HTML+CSS 完整入门：[BV1wQ5PzNE4W](https://www.bilibili.com/video/BV1wQ5PzNE4W/) — 140集全套前端入门（只看前 20 集）

---

## 🎨 Phase 1: 可见层 — Week 2-5

---

### 📅 Week 2: HTML + CSS 核心概念

#### Day 1-2：HTML 结构

| 任务 | 状态 |
|------|------|
| 看 Pink老师 2025 前端入门 [BV1MvaVzUEuz](https://www.bilibili.com/video/BV1MvaVzUEuz/) | ☐ |
| 或看尚硅谷禹神版 HTML+CSS [B站搜索「尚硅谷前端入门HTML+CSS」](https://search.bilibili.com/all?keyword=%E5%B0%9A%E7%A1%85%E8%B0%B7%E5%89%8D%E7%AB%AF%E5%85%A5%E9%97%A8HTML%2BCSS) | ☐ |
| 理解 DOM 树概念 | ☐ |
| 理解：`<div>`、`<span>`、`<section>`、`<header>`、`<footer>` 的区别 | ☐ |

#### Day 3-4：CSS 核心

| 任务 | 状态 |
|------|------|
| 理解盒模型（margin、border、padding、content） | ☐ |
| 理解 Flexbox 布局（用 AI 生成一个 Flexbox 的可视化演示） | ☐ |
| 理解选择器优先级 | ☐ |
| 理解响应式设计（`@media` 查询） | ☐ |

#### Day 5-6：本周项目 — 精美 Landing Page

| 任务 | 状态 |
|------|------|
| 做一个完整的多段式 Landing Page（Hero、Features、CTA） | ☐ |
| 要求：响应式（手机和电脑都好看） | ☐ |
| 要求：使用 Flexbox 布局 | ☐ |

#### Day 7：周回顾

| 任务 | 状态 |
|------|------|
| 闭卷回答自查表 | ☐ |
| 重做项目（至少重写 CSS 布局部分） | ☐ |

**📺 Week 2 核心教程**：
- ⭐ Pink老师 HTML+CSS：[BV1MvaVzUEuz](https://www.bilibili.com/video/BV1MvaVzUEuz/)
- 备选：140集全套前端：[BV1wQ5PzNE4W](https://www.bilibili.com/video/BV1wQ5PzNE4W/)
- 备选：前端零基础实战：[BV1rXuDzHE82](https://www.bilibili.com/video/BV1rXuDzHE82/)

**🔍 Week 2 自查表**：
- [ ] 什么是 DOM 树？为什么网页是「一棵树」？
- [ ] margin 和 padding 的区别是什么？（画图说明）
- [ ] Flexbox 解决了什么问题？以前用什么布局？
- [ ] 同一个元素上的多个 CSS 规则，谁说了算？为什么？
- [ ] 响应式设计的核心原理是什么？

**🔄 间隔重复提醒**：Week 1 的内容需要在本周三（Day 3）和本周日（Day 7）各复习一次。

---

### 📅 Week 3: JavaScript 核心概念

#### Day 1-2：变量、类型、函数

| 任务 | 状态 |
|------|------|
| 看 JS 2小时速通：[BV12rYYzuE79](https://www.bilibili.com/video/BV12rYYzuE79/) | ☐ |
| 理解：string、number、boolean、array、object | ☐ |
| 理解：函数的参数和返回值 | ☐ |
| 练习：写 10 个小函数（加减乘除、字符串反转等） | ☐ |

#### Day 3-4：异步和 Promise

| 任务 | 状态 |
|------|------|
| 看 JS 完整教程：[BV11NAUeyEAQ](https://www.bilibili.com/video/BV11NAUeyEAQ/)（看异步部分） | ☐ |
| 理解：「同步」和「异步」的区别（用餐厅比喻） | ☐ |
| 理解：Promise 和 async/await | ☐ |
| 练习：用 `fetch` 请求一个免费 API 并在页面上显示数据 | ☐ |

#### Day 5-6：本周项目 — 纯 JS Todo 应用

| 任务 | 状态 |
|------|------|
| 做一个 Todo 应用（增加、删除、标记完成、筛选） | ☐ |
| 数据存在 localStorage（刷新不丢失） | ☐ |
| 不依赖任何框架，纯 HTML+CSS+JS | ☐ |

#### Day 7：周回顾

**📺 Week 3 核心教程**：
- ⭐ JS 2小时速通：[BV12rYYzuE79](https://www.bilibili.com/video/BV12rYYzuE79/)
- JS 完整体系：[BV11NAUeyEAQ](https://www.bilibili.com/video/BV11NAUeyEAQ/)（276集完整版）

**🔍 Week 3 自查表**：
- [ ] `const`、`let`、`var` 有什么区别？什么时候用哪个？
- [ ] array 和 object 最大的区别是什么？各自适合存什么样的数据？
- [ ] `map`、`filter`、`reduce` 分别做什么？各举一个实际例子
- [ ] 什么是异步？用生活中的例子解释
- [ ] Promise 是什么？它解决了什么问题？
- [ ] `async/await` 和 `.then()` 是什么关系？
- [ ] `...`（展开运算符）到底在干什么？举 3 个用法

**🔄 间隔重复**：复习 Week 2 的 CSS 盒模型和 Flexbox（应该本周三做）。

---

### 📅 Week 4: React 核心概念

#### Day 1-2：组件、JSX、Props

| 任务 | 状态 |
|------|------|
| 用 AI 帮你初始化一个 React 项目（Vite + React） | ☐ |
| 理解：什么是组件？为什么拆组件？ | ☐ |
| 理解：JSX 为什么可以把 HTML 写在 JS 里？ | ☐ |
| 理解：Props 怎么把数据从父组件传到子组件？ | ☐ |

#### Day 3-4：State 和 Hooks

| 任务 | 状态 |
|------|------|
| 理解：State 是什么？为什么 UI 是状态的函数？（这是 React 最重要的概念） | ☐ |
| 理解：useState 怎么用？ | ☐ |
| 理解：useEffect 什么时候执行？ | ☐ |
| 练习：做一个计数器、一个输入框实时预览 | ☐ |

#### Day 5-6：本周项目 — React Todo 应用

| 任务 | 状态 |
|------|------|
| 用 React 重写 Week 3 的 Todo 应用 | ☐ |
| 新增功能：分类标签、搜索过滤、统计完成率 | ☐ |

#### Day 7：周回顾

**📺 Week 4 核心教程**：
- React 官方教程（推荐）：[B站搜索「React 官方教程 2025 中文」](https://search.bilibili.com/all?keyword=React%20%E5%AE%98%E6%96%B9%E6%95%99%E7%A8%8B%202025%20%E4%B8%AD%E6%96%87)
- React 源码深度：[BV1FAU5BtEV2](https://www.bilibili.com/video/BV1FAU5BtEV2/)（偏深入，按需看）
- React 项目实战：[B站搜索「React 入门项目实战 2025」](https://search.bilibili.com/all?keyword=React%20%E5%85%A5%E9%97%A8%E9%A1%B9%E7%9B%AE%E5%AE%9E%E6%88%98%202025)

**🔍 Week 4 自查表**：
- [ ] 什么是组件？为什么 React 里的一切都是组件？
- [ ] JSX 和普通 HTML 有什么区别？
- [ ] State 和 Props 的最本质区别是什么？
- [ ] 为什么说「UI 是状态的函数」？用 Todo 应用举例
- [ ] useState 和 useEffect 分别解决什么问题？
- [ ] 什么是虚拟 DOM？它为什么让 React 变快？

**🔄 间隔重复**：复习 Week 3 的 Promise 和 async/await。

---

### 📅 Week 5: Next.js + Tailwind CSS

#### Day 1-2：Next.js 基础

| 任务 | 状态 |
|------|------|
| 看 Next.js 15 快速入门：[BV1SKJazTEKN](https://www.bilibili.com/video/BV1SKJazTEKN/)（1.5 小时） | ☐ |
| 理解：文件路由（文件名就是 URL） | ☐ |
| 理解：服务端组件 vs 客户端组件 | ☐ |
| 看 SaaS 全栈实战：[BV14NaJzYEmi](https://www.bilibili.com/video/BV14NaJzYEmi/)（按需看） | ☐ |

#### Day 3-4：Tailwind CSS

| 任务 | 状态 |
|------|------|
| 看 Tailwind 90分钟入门：[BV1MJMwzoE8X](https://www.bilibili.com/video/BV1MJMwzoE8X/) | ☐ |
| 理解 utility-first 思想 | ☐ |
| 了解 shadcn/ui 组件库 | ☐ |

#### Day 5-6：本周项目 — Markdown 博客

| 任务 | 状态 |
|------|------|
| 用 Next.js + Tailwind + shadcn/ui 做一个博客 | ☐ |
| 博客内容用 Markdown 文件存储 | ☐ |
| 有首页（文章列表）和文章详情页 | ☐ |

#### Day 7：周回顾

**📺 Week 5 核心教程**：
- ⭐ Next.js 15：[BV1SKJazTEKN](https://www.bilibili.com/video/BV1SKJazTEKN/)
- ⭐ Tailwind CSS：[BV1MJMwzoE8X](https://www.bilibili.com/video/BV1MJMwzoE8X/)
- Next.js 旅游 App 实战：[BV1jtnmzwEdw](https://www.bilibili.com/video/BV1jtnmzwEdw/)
- Next.js 全栈进阶：[BV14NaJzYEmi](https://www.bilibili.com/video/BV14NaJzYEmi/)

**🔍 Week 5 自查表**：
- [ ] Next.js 的文件路由是什么意思？`/app/about/page.tsx` 对应什么 URL？
- [ ] 服务端组件和客户端组件有什么区别？什么时候用哪个？
- [ ] Server Actions 解决了什么问题？
- [ ] Tailwind CSS 的「原子化 CSS」思想是什么？为什么它比传统 CSS 更适合独立开发者？
- [ ] shadcn/ui 是什么？怎么用它？

**🔄 间隔重复**：复习 Week 4 的 React State 和 Hooks 概念。

---

## 🗄️ Phase 2: 数据层 — Week 6-9

---

### 📅 Week 6: 数据库基础

#### 学习内容

| 任务 | 教程 | 状态 |
|------|------|------|
| 理解关系型数据库概念 | [BV1Lbt4zxECX](https://www.bilibili.com/video/BV1Lbt4zxECX/) — 57集MySQL教程（看前15集） | ☐ |
| 理解：表、字段、主键、外键 | 同上 | ☐ |
| 学习 SQL 基础（SELECT/INSERT/UPDATE/DELETE） | [BV1eE61YfE7t](https://www.bilibili.com/video/BV1eE61YfE7t/) — 全网最全SQL教程 | ☐ |
| 学习 Prisma ORM | [B站搜索「Prisma 入门 2025」](https://search.bilibili.com/all?keyword=Prisma%20%E5%85%A5%E9%97%A8%202025) | ☐ |

**本周项目**：用 Excel 设计一个 SaaS 数据库结构 → 用 Prisma + SQLite 实现 → 用 Prisma Studio 查看数据

**🔍 Week 6 自查表**：
- [ ] 关系型数据库和 Excel 有什么相同和不同？
- [ ] 什么是主键？什么是外键？它们怎么把表关联起来？
- [ ] SELECT、INSERT、UPDATE、DELETE 分别做什么？
- [ ] 什么是 ORM？为什么我们不直接写 SQL？
- [ ] 一个博客系统至少需要几张表？每张表存什么？

**🔄 间隔重复**：复习 Week 5 的 Next.js 路由和服务端组件。

---

### 📅 Week 7: API 设计

#### 学习内容

| 任务 | 教程 | 状态 |
|------|------|------|
| 理解 RESTful API 概念 | [B站搜索「RESTful API 入门」](https://search.bilibili.com/all?keyword=RESTful%20API%20%E5%85%A5%E9%97%A8) | ☐ |
| 理解 GET/POST/PUT/DELETE 语义 | 同上 | ☐ |
| 理解 JSON 数据格式 | 同上 | ☐ |
| 学习 Next.js API Routes | [BV1SKJazTEKN](https://www.bilibili.com/video/BV1SKJazTEKN/)（回顾 API Routes 部分） | ☐ |

**本周项目**：给 Week 6 的数据库加一套完整的 CRUD API

**🔍 Week 7 自查表**：
- [ ] API 是什么？用餐厅服务员的比喻解释
- [ ] GET 和 POST 最本质的区别是什么？
- [ ] PUT 和 PATCH 有什么区别？
- [ ] 为什么前后端之间需要「合同」（API 规范）？
- [ ] 前端请求一个 API 时，数据是怎么流动的？

**🔄 间隔重复**：复习 Week 6 的数据库表设计和 SQL。

---

### 📅 Week 8: 认证和用户系统

#### 学习内容

| 任务 | 教程 | 状态 |
|------|------|------|
| 学习 NextAuth.js / Auth.js | ⭐ [BV1burTYLEia](https://www.bilibili.com/video/BV1burTYLEia/) — 2025终极Next.js认证指南 | ☐ |
| 理解 JWT 认证流程 | 同上 | ☐ |
| 理解密码哈希（bcrypt） | 看上面视频的理解部分 | ☐ |
| 理解 OAuth（Google 登录） | 同上 | ☐ |

**本周项目**：做一个需要登录才能访问的私人笔记应用

**🔍 Week 8 自查表**：
- [ ] 为什么密码不能明文存在数据库里？bcrypt 做了什么？
- [ ] JWT 的认证流程是怎样的？（从登录到每次请求）
- [ ] OAuth 登录的本质是什么？为什么用「Google 登录」比自己注册更安全？
- [ ] 什么是中间件？为什么认证要在中间件里做？
- [ ] NextAuth.js 帮我们处理了哪些麻烦事？

**🔄 间隔重复**：复习 Week 7 的 REST API 设计。

---

### 📅 Week 9: Python 后端（推荐）

#### 学习内容

| 任务 | 教程 | 状态 |
|------|------|------|
| FastAPI 快速入门 | ⭐ [BV1JTCQBQERg](https://www.bilibili.com/video/BV1JTCQBQERg/) — 1小时学会FastAPI | ☐ |
| FastAPI 深入学习 | [BV1j8a9z5EEu](https://www.bilibili.com/video/BV1j8a9z5EEu/) — 38节课完整版（选看） | ☐ |
| FastAPI 项目实战 | [BV1AB78zDEdJ](https://www.bilibili.com/video/BV1AB78zDEdJ/) — 3天搞定 | ☐ |

**本周项目**：用 FastAPI 给笔记应用写一套后端 API，前端继续用 Next.js

**🔍 Week 9 自查表**：
- [ ] FastAPI 和 Next.js API Routes 做的是同一件事吗？有什么区别？
- [ ] 前后端分离架构的优点是什么？独立开发者适合吗？
- [ ] 「框架和语言不重要，理解了概念就行」——你同意吗？为什么？

**🔄 间隔重复**：复习 Week 8 的认证流程。

---

## 🏗️ Phase 3: 基础设施层 — Week 10-12

---

### 📅 Week 10: Git 和 GitHub

#### 学习内容

| 任务 | 教程 | 状态 |
|------|------|------|
| Git 快速入门 | [BV1KarSY8E8v](https://www.bilibili.com/video/BV1KarSY8E8v/) — 30分钟掌握Git | ☐ |
| Git 系统学习 | [B站搜索「鱼皮 Git 教程」](https://search.bilibili.com/all?keyword=%E9%B1%BC%E7%9A%AEGit%E6%95%99%E7%A8%8B) — 鱼皮2025最新版 | ☐ |
| 玩游戏学 Git 分支 | [learngitbranching.js.org](https://learngitbranching.js.org/?locale=zh_CN) | ☐ |

**本周项目**：把你之前所有项目都用 Git 管理起来，推到 GitHub

**🔍 Week 10 自查表**：
- [ ] `git add`、`git commit`、`git push` 各自做了什么？
- [ ] 什么是分支（branch）？为什么需要分支？
- [ ] `.gitignore` 是干什么的？什么文件不该提交？
- [ ] `git pull` 和 `git fetch` 的区别是什么？

**🔄 间隔重复**：复习 Week 9 的 FastAPI 概念。

---

### 📅 Week 11: 部署和 DevOps 基础

#### 学习内容

| 任务 | 教程 | 状态 |
|------|------|------|
| Vercel 部署 Next.js | ⭐ [BV1EJ2pYHEH8](https://www.bilibili.com/video/BV1EJ2pYHEH8/) — 免费部署演示 | ☐ |
| Vercel 详细教程 | [BV1ak4y1h78y](https://www.bilibili.com/video/BV1ak4y1h78y/) — Next.js 发布到 Vercel | ☐ |
| 了解 DNS + 域名绑定 | [B站搜索「DNS 域名解析 入门」](https://search.bilibili.com/all?keyword=DNS%20%E5%9F%9F%E5%90%8D%E8%A7%A3%E6%9E%90%20%E5%85%A5%E9%97%A8) | ☐ |
| 了解 HTTPS/SSL | 同上 | ☐ |

**本周项目**：把你 Phase 2 的笔记应用部署到 Vercel，买域名绑定

**🔍 Week 11 自查表**：
- [ ] Vercel 是什么？它帮我做了什么？
- [ ] 买了域名之后，为什么还要配置 DNS 才能访问？
- [ ] HTTPS 的那把「小锁」代表什么？
- [ ] 为什么 API 密钥不能写在代码里？应该放哪里？

**🔄 间隔重复**：复习 Week 10 的 Git 工作流。

---

### 📅 Week 12: 集成第三方服务

#### 学习内容

| 任务 | 教程 | 状态 |
|------|------|------|
| Stripe 支付集成 | [BV127xkeQEat](https://www.bilibili.com/video/BV127xkeQEat/) — Stripe订阅支付 Next.js 完整教程 | ☐ |
| 完整 SaaS 含支付 | [BV1vN4y1C7cU](https://www.bilibili.com/video/BV1vN4y1C7cU/) — Next.js 13 构建完整SaaS | ☐ |
| 文件上传 | [B站搜索「Next.js 文件上传」](https://search.bilibili.com/all?keyword=Next.js%20%E6%96%87%E4%BB%B6%E4%B8%8A%E4%BC%A0) | ☐ |

**📖 文字教程补充（Stripe）**：
- [Stripe 支付全指南（中文）](https://blog.wenhaofree.com/posts/technology/stripe-payment-guide/)
- [Vercel 官方 Stripe 指南](https://vercel.com/kb/guide/getting-started-with-nextjs-typescript-stripe)

**本周项目**：给笔记应用加上付费功能（Stripe 测试模式）

**🔍 Week 12 自查表**：
- [ ] Stripe Checkout 的流程是怎样的（创建 Session → 跳转 → Webhook）？
- [ ] 什么是 Webhook？为什么支付系统需要它？
- [ ] 为什么独立开发者应该多用 SaaS 服务而不是自己造轮子？

**🔄 间隔重复**：复习 Week 11 的部署和 DNS。

---

## 🚀 Phase 4: 产品工程 — Week 13-20

---

### 总体说明

从这个阶段开始，你的学习节奏从「学中做」切换到「做中学」。不再有固定的每日课程表，而是：

1. **选一个产品方向** → 2. **快速出 MVP** → 3. **遇到不懂再学** → 4. **每个产品 2-3 周**

---

### 🧰 产品 1: SaaS 工具箱（Week 13-14）

**目标**：一个在线工具合集网站

| 功能 | 涉及技术 | 状态 |
|------|----------|------|
| JSON 格式化/校验 | JavaScript 字符串处理 | ☐ |
| Base64 编解码 | 浏览器 API | ☐ |
| URL 编解码 | `encodeURIComponent` | ☐ |
| Markdown 预览 | 第三方 Markdown 渲染库 | ☐ |
| 好看的 UI | Tailwind + shadcn/ui | ☐ |
| SEO 优化 | Next.js Metadata API | ☐ |
| 部署上线 | Vercel | ☐ |

**工具站参考**：看 [tool.lu](https://tool.lu)、[json.cn](https://json.cn) 等工具站找灵感

---

### 💰 产品 2: 微型 SaaS（Week 15-17）

**目标**：一个完整的、有付费功能的 SaaS 产品

**方向选择**（选一个你最感兴趣的）：

| 方向 | 核心功能 | 状态 |
|------|----------|------|
| 习惯追踪器 | 打卡、统计、连续天数 | ☐ |
| AI 读书笔记 | 导入书籍、写笔记、AI 总结 | ☐ |
| 发票生成器 | 模板、填写信息、导出 PDF | ☐ |
| 自定义方向 | 你想做的任何方向 | ☐ |

**必备功能清单**：
- [ ] 用户注册/登录（NextAuth）
- [ ] 数据库（Prisma + PostgreSQL/SQLite）
- [ ] 核心功能（你的产品卖点）
- [ ] 付费墙（Stripe Checkout）
- [ ] 邮件通知（Resend）
- [ ] 后台管理页
- [ ] 部署上线 + 域名

---

### 🏆 产品 3: 自由选题（Week 18-20）

**目标**：一个你真正想做、觉得有商业潜力的产品

这次你的角色变化：**你来主导设计决策，AI 辅助执行**。

- [ ] Week 18：需求分析 + 技术选型 + 数据库设计
- [ ] Week 19：核心功能开发
- [ ] Week 20：打磨 + 部署 + 发布

**发布上线清单**：
- [ ] 部署到 Vercel
- [ ] 绑定域名 + HTTPS
- [ ] 配置 Stripe 生产环境
- [ ] 写一篇发布文章（发到 Twitter/X、V2EX、即刻等）
- [ ] 提交到 Product Hunt

---

## 🧠 Phase 5: AI 协作精通（贯穿全阶段）

### 每天必练的基础 AI 协作

| 模式 | 提示词 | 使用频率 |
|------|--------|----------|
| 解释模式 | 「逐行解释这段代码，用简单的比喻」 | 每天 |
| 对比模式 | 「实现这个功能有几种方案？对比优缺点」 | 每个功能设计前 |
| 审查模式 | 「审查这段代码：安全性、性能、可维护性」 | 每个项目完成时 |
| 教学模式 | 「用生活中的比喻解释这个概念」 | 遇到不懂概念时 |
| 师徒模式 | 「用苏格拉底式提问引导我思考，别直接给代码」 | 想自己思考时 |

### AI 协作五级进阶自评

| 级别 | 描述 | 我到了吗？ |
|------|------|-----------|
| L1 代码生成者 | AI 写什么我用什么 | ☐ |
| L2 需求翻译者 | 能用精准技术语言描述需求 | ☐ |
| L3 代码审查者 | 能读 AI 代码、判断好坏 | ☐ |
| L4 系统设计者 | 能做架构决策，AI 帮我拆解 | ☐ |
| L5 AI 管理者 | 能同时驱动多个 AI 做不同事 | ☐ |

**每周评估一次，标记你当前在哪一级。**

---

## 📚 完整教程资源索引

### Phase 0-1 资源

| 主题 | 最佳教程 | BV号/链接 |
|------|----------|-----------|
| 计算机基础 | 2026全新计算机网络 | [BV1kid5BnEPH](https://www.bilibili.com/video/BV1kid5BnEPH/) |
| HTML+CSS | Pink老师2025前端 | [BV1MvaVzUEuz](https://www.bilibili.com/video/BV1MvaVzUEuz/) |
| HTML+CSS 备选 | 140集全套前端 | [BV1wQ5PzNE4W](https://www.bilibili.com/video/BV1wQ5PzNE4W/) |
| JavaScript 速通 | 2小时JS快速入门 | [BV12rYYzuE79](https://www.bilibili.com/video/BV12rYYzuE79/) |
| JavaScript 完整 | 276集JS零基础到精通 | [BV11NAUeyEAQ](https://www.bilibili.com/video/BV11NAUeyEAQ/) |
| React | React官方教程 | [B站搜索](https://search.bilibili.com/all?keyword=React%20%E5%AE%98%E6%96%B9%E6%95%99%E7%A8%8B%202025) |
| Next.js 快速 | NextJS 15 完整课程 | [BV1SKJazTEKN](https://www.bilibili.com/video/BV1SKJazTEKN/) |
| Next.js 全栈 | SaaS全栈实战 | [BV14NaJzYEmi](https://www.bilibili.com/video/BV14NaJzYEmi/) |
| Tailwind CSS | 90分钟极速掌握 | [BV1MJMwzoE8X](https://www.bilibili.com/video/BV1MJMwzoE8X/) |

### Phase 2 资源

| 主题 | 最佳教程 | BV号/链接 |
|------|----------|-----------|
| SQL/MySQL | 57集MySQL零基础 | [BV1Lbt4zxECX](https://www.bilibili.com/video/BV1Lbt4zxECX/) |
| SQL 速通 | 全网最全SQL教程 | [BV1eE61YfE7t](https://www.bilibili.com/video/BV1eE61YfE7t/) |
| NextAuth 认证 | 2025终极认证指南 | [BV1burTYLEia](https://www.bilibili.com/video/BV1burTYLEia/) |
| FastAPI 速通 | 1小时学会FastAPI | [BV1JTCQBQERg](https://www.bilibili.com/video/BV1JTCQBQERg/) |
| FastAPI 完整 | 38节课完整版 | [BV1j8a9z5EEu](https://www.bilibili.com/video/BV1j8a9z5EEu/) |
| FastAPI 项目 | 3天搞定FastAPI | [BV1AB78zDEdJ](https://www.bilibili.com/video/BV1AB78zDEdJ/) |

### Phase 3 资源

| 主题 | 最佳教程 | BV号/链接 |
|------|----------|-----------|
| Git 快速 | 30分钟掌握Git | [BV1KarSY8E8v](https://www.bilibili.com/video/BV1KarSY8E8v/) |
| Git 系统 | 鱼皮2025 Git教程 | [B站搜索](https://search.bilibili.com/all?keyword=%E9%B1%BC%E7%9A%AE%20Git%20%E6%95%99%E7%A8%8B) |
| Git 游戏 | Learning Git Branching | [链接](https://learngitbranching.js.org/?locale=zh_CN) |
| Vercel 部署 | 免费部署演示 | [BV1EJ2pYHEH8](https://www.bilibili.com/video/BV1EJ2pYHEH8/) |
| Stripe 支付 | 订阅支付Next.js教程 | [BV127xkeQEat](https://www.bilibili.com/video/BV127xkeQEat/) |
| 完整SaaS | Stripe+Shadcn+NextAuth | [BV1vN4y1C7cU](https://www.bilibili.com/video/BV1vN4y1C7cU/) |

### 重要文字教程

| 主题 | 链接 |
|------|------|
| Stripe 支付全指南 | [blog.wenhaofree.com](https://blog.wenhaofree.com/posts/technology/stripe-payment-guide/) |
| Vercel 官方 Stripe 指南 | [vercel.com](https://vercel.com/kb/guide/getting-started-with-nextjs-typescript-stripe) |
| MDN Web Docs | [developer.mozilla.org](https://developer.mozilla.org/zh-CN/) |
| Next.js 官方文档 | [nextjs.org/docs](https://nextjs.org/docs) |
| Indie Hackers 社区 | [indiehackers.com](https://www.indiehackers.com) |

---

## 📊 总进度追踪表

| Phase | 周数 | 状态 | 完成日期 |
|-------|------|------|----------|
| Phase 0 | Week 1 | ☐ | |
| Phase 1 | Week 2-5 | ☐ | |
| Phase 2 | Week 6-9 | ☐ | |
| Phase 3 | Week 10-12 | ☐ | |
| Phase 4 | Week 13-20 | ☐ | |
| Phase 5 | 持续 | ☐ | |

---

## 🏷️ 间隔重复总提醒日历

| 本周学习 | 1天后复习 | 3天后复习 | 7天后复习 | 14天后复习 | 30天后复习 |
|----------|-----------|-----------|-----------|------------|------------|
| Week 1 | Day 2 | Day 4 | Day 7 | Week 3 | Week 5 |
| Week 2 | Week 2 Day 2 | Week 2 Day 5 | Week 3 | Week 4 | Week 6 |
| Week 3 | Week 3 Day 2 | Week 3 Day 5 | Week 4 | Week 5 | Week 7 |
| Week 4 | Week 4 Day 2 | Week 4 Day 5 | Week 5 | Week 6 | Week 8 |
| Week 5 | Week 5 Day 2 | Week 5 Day 5 | Week 6 | Week 7 | Week 9 |
| Week 6 | Week 6 Day 2 | Week 6 Day 5 | Week 7 | Week 8 | Week 10 |
| Week 7 | Week 7 Day 2 | Week 7 Day 5 | Week 8 | Week 9 | Week 11 |
| Week 8 | Week 8 Day 2 | Week 8 Day 5 | Week 9 | Week 10 | Week 12 |

---

## ⚡ 每日启动清单（每天开始学习前做）

- [ ] 我今天的 3 个目标是什么？
- [ ] 昨天有什么概念不清楚？先花 15 分钟回顾
- [ ] 今天要做的项目是什么？（不能只是「看视频」）
- [ ] 今天打算让 AI 帮我什么？打算自己思考什么？

## 🌙 每日收尾清单（每天结束学习前做）

- [ ] 今天我学到的最重要的 3 件事是什么？（写在笔记里）
- [ ] 有什么概念还不清楚？（标记为明天优先复习）
- [ ] 今天我做了项目吗？遇到了什么困难？怎么解决的？
- [ ] 今天用了几种 AI 协作模式？（解释/对比/审查/教学/师徒）

---

*这个学习管家是你自己的工具。每天打开它，打勾，推进。不要一口气看完就不管了——用得越多，效果越好。*
