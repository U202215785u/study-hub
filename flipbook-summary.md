# Flipbook爆火：UI的未来是无限视觉

> 来源：[B站视频](https://www.bilibili.com/video/BV1TioSBwEUP) | 解析时间：2026-05-02 06:48

---

## 内容概要

Flipbook 是一个由前 OpenAI 研究员 Zain Shah 团队打造的"无限视觉浏览器"原型——没有 HTML、没有代码，所有界面元素由 AI 实时用像素生成，点击画面任意区域即可深入探索。它不仅引发了 Andrej Karpathy、Shopify CEO Tobi Lütke 等行业领袖的转发，更让人们开始认真思考：我们习以为常的固定界面，是否即将被 AI 实时生成的动态视觉体验所取代。

---

## 核心内容

### 要点一：Flipbook 是什么——一本可以无限深入探索的"魔法百科全书"

Flipbook 的核心体验是：你在搜索栏输入一个主题，AI 实时用像素生成一张类似百科全书风格的动态插画，画面上的文字也是像素组成，没有任何 HTML 或代码。点击画面上的任何区域——比如巴黎圣母院的建筑、一道泰北咖喱面——它会丝滑放大，展示更详细的内部结构、价格、来源等信息。

> *"目前画面上看到的一切都只是像素，AI 实时根据你想要的东西用像素组成的一幅画，包括这些文字没有任何的 HTML，任何代码都没有。"*

### 要点二：技术颠覆——从"预先设计"到"实时生成"

目前我们使用的微信、抖音、小红书等所有界面，都是设计工程师提前设计好、写好代码的固定页面。Flipbook 展示了一个截然不同的范式转变：每个界面都是 AI 专为你、专为当下这个时刻的需求实时生成的。它背后的技术原理包括：

- **无 HTML/CSS/DOM**：所有界面元素（文字、图标、按钮）均由 AI 模型以像素形式直接渲染
- **底层模型**：基于 Lightricks 的 LTX Video 开源视频生成模型（DiT 架构），通过 WebSocket 将 1080p 24fps 视频流推送到屏幕
- **工程优化**：激活缓存复用、FP16→INT8 量化、torch.compile、CUDA Graph 内存快照
- **后端算力**：运行在 Modal Labs 的服务器 GPU 上

> *"我们每个人只需要配置一个 AI agent，配置一个你自己的贾维斯。早上起来想知道今天的天气、谁给我发了微信、工作上有什么消息、想去哪里旅游——就只需要问我的 AI，让它实时生成一个界面。"*

### 要点三：行业反响与未来信号

该帖子在 X（Twitter）上获得 **480 多万浏览、2.3 万点赞、2.1 万收藏**，多位业界大佬转发：

- **Andrej Karpathy**（前特斯拉 AI 总监）转发
- **Tobi Lütke**（Shopify CEO）转发时评价："This is the beginning of something really big."
- **Dan Hollick**（Cursor 设计工程师）表示自己曾本能地质疑"这太漂亮了不现实"，但回顾计算机历史后意识到：**在 2026 年的今天，不能轻易相信自己的直觉，什么事情都有可能发生。**

### 要点四：创作过程的元叙事——视频脚本本身也由 AI 生成

视频作者提到，她关于"哪些大佬在转发"的视频脚本并非自己手动搜集，而是将 Flipbook 的原帖链接发给自己的 AI 助手 **Startout**，一键连接 Twitter 账号后，AI 自动生成了完整的分析报告。

> *这个细节本身就在佐证视频的核心论点：AI 正在改变我们获取信息和创作内容的方式。*

### 要点五：当前局限与未来展望

创始团队坦承 Flipbook 目前仍处于**实验测试阶段**：
- **算力瓶颈**：每次交互需等待数秒至 20 秒，服务器端 GPU 推理成本是文本流的 50-150 倍
- **规模化的经济可行性**：短期内无法实现大规模普及
- **信息准确性**：与 ChatGPT/Gemini 水平相当，偶有幻觉
- **文字不可复制**：像素渲染的文字无法直接选取

但正如创始团队所言，未来方向的信号已经足够清晰——随着模型能力提升和推理成本下降（预计每年降为原来的 10-20%），这种交互模式可能在 5-10 年内变得经济可行。

---

## 提到的资源

| 名称 | 类型 | 地址/说明 |
|:---|:---|:---|
| Flipbook | 项目官网 | [flipbook.page](https://flipbook.page) — 无限视觉浏览器原型 |
| Zain Shah | 创始人主页 | [tarzain.com](http://tarzain.com/about/) — 前 OpenAI 研究员/三星创意技术专家，个人简介写有 "I help machines meet us where we are" |
| Andrej Karpathy | 行业人物 | 前特斯拉 AI 总监、OpenAI 联合创始人，转发 Flipbook |
| Tobi Lütke | 行业人物 | Shopify CEO，转发并评价 "This is the beginning of something really big" |
| Dan Hollick | 行业人物 | Cursor 设计工程师，从质疑 Flipbook 到反思直觉不可靠 |
| Startout AI | AI 工具 | 视频作者使用的 AI 社交媒体助手（未找到公开链接） |
| LTX Video | 开源模型 | [Lightricks](https://github.com/Lightricks/LTX-Video) — Flipbook 底层依赖的视频生成模型 |
| Modal Labs | 云平台 | [modal.com](https://modal.com) — 提供后端服务器 GPU 算力 |

---

## 扩展阅读

- **[Apple's HyperCard comes back to life in the form of this cool new animated browser](https://www.fastcompany.com/91532926/flipbook-animated-browser-inspired-by-apple-hypercard)**（Fast Company, 2026-04）— Flipbook 被描述为"HyperCard 的现代转世"，深入分析其设计哲学与历史渊源

- **[最近刷屏的 Flipbook，想把互联网彻底变成实时生成的无限世界](https://www.woshipm.com/ai/6386554.html)**（人人都是产品经理, 2026-04）— 中文深度解读，涵盖团队背景、技术架构、适用场景与局限性

- **[我们熟知的用户界面已死，四种方式助你迎接"一次性"UI时代](https://ai.zhiding.cn/2026/0429/3185455.shtml)**（至顶网, 2026-04-29）— WorkOS 创始人 Michael Grinich 提出"一次性 UI"概念，探讨 GenUI 对传统界面的替代路径

- **[生成式UI，AI交互的下一个十年？](https://bbs.huaweicloud.com/blogs/476620)**（华为云博客, 2026）— 剖析 GenUI 核心原理（结构化输出、流式增量渲染、缓冲保护区），探讨设计范式从 UX 到 AX 的迁移

- **[2026 UI/UX 领域 7 大设计趋势](https://www.uisdc.com/2026-ui-ux-ai-trends)**（优设网, 2026）— 涵盖生成式 UI、AI 优先设计工作流、空间化设计等趋势，91% 设计师表示 AI 已改善设计质量

---

## 思考

Flipbook 真正的颠覆不在于技术本身，而在于它让"界面不再被设计而是被生成"这个未来变得可感知——当每块像素都是为你此刻的需求而生，传统的 APP 形态自然瓦解。
