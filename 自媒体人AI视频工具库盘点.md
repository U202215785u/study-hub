# 自媒体人的skill盘点 整理了一周的AI视频工具库！从调研到复盘，这一条视频全讲透（附文档领取）
#AI工具 #skill  #短视频制作 #人工智能 #干货分享

> 来源：[抖音视频](https://www.douyin.com/video/7657864594769169702) | 解析时间：2026-08-02 15:42

---

## 内容概要

做短视频不是不会做，而是流程乱了。本期视频将视频制作拆解为选题调研 → 文案脚本 → 字幕配音 → 画面剪辑 → 发布复盘五个环节，逐一匹配对应 AI 工具和 Agent Skill，核心主张：好选题不是灵感，是数据里长出来的；字幕和配音不是装饰，是完播率的基础设施。

---

## 核心内容

### 要点一：选题调研 —— 让数据代替直觉

> "好选题不是灵感，是数据、爆款内容和评论区反馈里长出来的。"

- **全网调研**：用 Agent 类搜索 Skill 跨平台（GitHub、B 站、小红书、YouTube）扫描最近被讨论最多的工具、星标最高的项目、中文互联网上的热议话题，而非手动逐平台扒资料。
- **爆款拆解与评论分析**：用 MediaCrawler（GitHub 5.3 万星）覆盖抖音、小红书、快手等平台，抓取内容与评论，拆解爆款规律，辅助判断选题值不值得做。
- **补充工具**：其他选题调研类 Skill 按需纳入工具箱即可，关键是把"调研 → 选题决策"变成固定流程。

### 要点二：文案脚本 —— 从选题到能念出口的稿子

> "AI 写出来的东西经常看起来很完整，一念出来就假。"

- **Copywriting（表达层）**：解决标题、前三秒钩子、卖点提炼、结尾引导（收藏/评论/关注）等短视频核心表达问题。
- **Blobost / Content Repurposer（复用层）**：把一篇文章、一份资料、一段长脚本拆成短视频脚本、小红书正文、推文等多平台版本——一份资料多平台分发的中间节点。
- **Herminator / Humanizer（去 AI 味）**：GitHub 1.2 万星（Hermes Agent 体系），专门去掉文案中的"AI 味"，改成像真人说出口的话，适合放在文案处理的最后阶段。
- **风控检查**：文案写完后必须做事实核查、来源检查、平台风险检查——"胡说一次，信任就没了"。

### 要点三：字幕与配音 —— 完播率的基础设施

> "字幕和配音不是装饰，它们是完播率的基础设施。"

- **pyvideotrans**（GitHub 1.8 万星）：把视频翻译、字幕生成、AI 配音、音画同步全部打包，可先用本地工具跑通基本流程，后续再接入高级模型追求更好音质。
- **WhisperX**：更适合精准字幕和词级时间戳。
- **豆包 TTS**（字节跳动/火山引擎）：适合中文配音，支持音色复刻与情感控制。
- **ChatTTS**（GitHub ~4 万星）：免费配音方案中效果较好的一款，支持中英文，对话场景自然度高。

### 要点四：画面剪辑 —— 用代码替代手动拖素材

> "它们都不是在时间线上手动拖素材，而是用代码生成视频。"

- **Typeframes**（GitHub 3.1 万星）与 **Remotion**（GitHub 5.2 万星）底层逻辑相似：用代码（React）生成视频，让 AI 按脚本自动填充内容、自动出动画、自动出特效、自动出成片。知识分享视频、AI 工具演示、数据图卡、动态字幕卡都适用。
- 传统做法是标题自己排版、转场自己加、字幕动效自己调、数据图步骤卡一步一步点——每条视频都这样做，时间成本高且难以批量复刻。代码生成方案解决了批量化和可复用问题。
- **补充工具**：按赛道选择，有口播剪辑类、混剪类、知识动画类等。

### 要点五：发布复盘 —— 发布之后才是真正的反馈循环

> "评论区不是结束，是下一轮选题的入口。"

- **多平台分发**：AI 辅助准备各平台（抖音、快手、B 站、小红书、视频号、公众号、TikTok、YouTube）的标题、简介、标签、封面文案和发布清单，人在发布前再过一遍。
- **评论复盘**：用 MediaCrawler 把评论区的问题抓回来，复盘哪里讲清楚、哪里没讲清楚，下一条如何补充。
- **同类工具**：偏抖音创作运营的 Skill、自动回复评论的 Skill 可按需补充。

### 要点六：全流程项目 —— 从"一键生成"理解完整链路

> "全流程不是魔法，只是把选题、文案、素材、配音、字幕、剪辑、合成全部打包在一起。"

- **MoneyPrinterTurbo**（GitHub 9.3 万星）：从主题到短视频完整流程——脚本生成、素材搜索、配音、字幕、BGM、视频合成全自动跑。最大价值是帮你理解一键生成短视频的完整流程，但需要配好大模型 API、素材 API、TTS 等。
- **OpenMontage**（GitHub 2.6 万星）：接近 AGI 的视频生产系统，研究脚本、素材生成、检索、剪辑、字幕、配音、Remotion 合成、Typeframes 合成全覆盖，能力完整但更复杂，适合进阶。
- **NarratoAI**（GitHub 1 万星）：偏向 AI 解说剪辑，适合影视解说、短剧解说、二创解说工作流。
- **建议**：先理解单点工具，再接触全流程项目，才不会误以为"AI 做视频就是按一个按钮的事"。

### 要点七：装机必备 Skill —— 让 AI 内容系统长期稳定运行的底座

> "这三类，一个负责学风格，一个负责自升级，一个负责安全审查。他们不一定直接生产视频，但决定了你的 AI 内容生产系统能不能长期稳定地跑。"

- **风格学习类（"真牛 Skill"）**：把目标作者的作品投给 AI，提炼其选题角度、开头方式、语言节奏、观点结构，后续让 AI 按此风格帮你改选题、脚本、口播——解决风格学习和表达迁移问题。
- **自升级类（SkillMaxxing / Hermes Self-Evolution）**：记录运行中反复出现的问题（漏风控、标题不适配平台、字幕错位等），反过来升级流程——不是帮你做某个视频，而是让 Skill 系统越用越顺。
- **安全审查类（Skill Vetter）**：安装第三方 Skill 前做安全检查（检测 curl 外发、SSH 密钥读取、eval/exec 等危险模式），不是可选项，是必装项。

---

## 提到的资源

| 名称 | 类型 | 地址/说明 |
|:---|:---|:---|
| MediaCrawler | GitHub 项目 | https://github.com/NanmiCoder/MediaCrawler — 小红书/抖音/快手/B站/微博多平台爬虫，~53k stars |
| Humanizer（Herminator） | Agent Skill | https://github.com/blader/humanizer — 去掉文案 AI 味，Hermes Agent 体系内置，~1.2k stars |
| pyvideotrans | GitHub 项目 | https://github.com/jianchang512/pyvideotrans — 视频翻译+字幕+配音全套，~18k stars |
| WhisperX | GitHub 项目 | https://github.com/m-bain/whisperX — 词级时间戳精准字幕，wav2vec2 强制对齐 |
| 豆包 TTS | 云服务 | https://www.volcengine.com/docs/6561/2535751 — 字节跳动语音合成，中文效果好，支持音色复刻 |
| ChatTTS（HTTS） | GitHub 项目 | https://github.com/2noise/ChatTTS — 免费中文 TTS，对话场景自然度高，~39.6k stars |
| Remotion | GitHub 项目 | https://github.com/remotion-dev/remotion — React 代码生成视频，~52k stars |
| Typeframes | GitHub 项目 | 代码生成视频工具，~31k stars，与 Remotion 同类（具体仓库未验证） |
| MoneyPrinterTurbo | GitHub 项目 | https://github.com/harry0703/MoneyPrinterTurbo — 一键全流程 AI 短视频生成，~93k stars |
| OpenMontage | GitHub 项目 | https://github.com/calesthio/OpenMontage — 智能体驱动全流程视频生产，~26k+ stars |
| NarratoAI | GitHub 项目 | https://github.com/linyqh/NarratoAI — AI 解说剪辑，影视解说/二创场景，~10k stars |
| Postiz（Ai-too 类） | GitHub 项目 | https://github.com/gitroomhq/postiz-app — 多平台社交媒体排期发布，~28k stars |
| content-repurposer（Blobost 类） | Agent Skill | openclaw/skills/content-repurposer — 一份内容输出多平台文案 |
| SkillMaxxing | GitHub 项目 | https://github.com/Bennyoooo/skillmaxxing — 自进化 Agent Skill，自动创建和改进技能 |
| Skill Vetter | Agent Skill | clawhub.ai/spclaudehome/skill-vetter — 第三方 Skill 安装前安全审查 |
| last30days-skill（Agent Rich 类） | Agent Skill | https://github.com/mvanhorn/last30days-skill — 跨 10+ 平台全网调研搜索 Skill，~44k stars |

---

## 扩展阅读

- **Agent Skills 生态系统全景（2026）** — 截至 2026-08，Skills.sh 聚合约 65,000+ 个技能、ClawHub 约 24,000+、Smithery 约 14,000+，Agent Skill 正从"辅助工具"进化为"内容生产流水线"的核心编排层。
- **GitHub Copilot Agent Finder 上线**（[GitHub Blog](https://github.blog/changelog/2026-06-17-agent-finder-for-github-copilot-now-available/)）— 2026 年 6 月 GitHub 官方推出 Agent 资源发现功能，支持 ARD 开放规范，Agent Skills 生态走向标准化。
- **Proteus：Skill 安全审计的对抗攻击研究**（[arXiv:2605.11891](https://arxiv.org/abs/2605.11891)）— 红队框架对 Skill Vetter 类审计工具实现 93% 绕过率，提示"安全审查不能只靠语义扫描"。
- **Remotion + Claude Code = 代码视频时代**（[腾讯云开发者](https://cloud.tencent.com.cn/developer/article/2639527)）— Remotion Agent Skills 发布后，视频制作从"手动剪辑"变成"描述需求 → AI 写 React 组件 → 渲染出片"。
- **OpenMontage：用 12 条流水线重构 AI 视频生产**（[虎嗅](https://m.huxiu.com/article/4871160.html)）— 截至 2026-06，支持 52+ 工具、400+ 可组合 Skill、14+ 视频生成 API，Pixar 风格 60 秒短片成本约 $1.33。

---

## 行动建议

1. **先跑通单点工具链再做全流程**：建议从"MediaCrawler 调研 → Humanizer 去 AI 味 → pyvideotrans 字幕配音 → Remotion 画面"四步最小闭环开始，验证每个环节产出质量后，再考虑 MoneyPrinterTurbo 或 OpenMontage 做全流程自动化。
2. **必装 Skill Vetter 再做第三方 Skill 安装**：当前 Agent Skill 生态缺乏统一安全标准，学术研究已证明纯语义审查可被对抗样本绕过。建议安装任何第三方 Skill 前先用 Skill Vetter 扫描，同时关注 `safe-install` 脚本（沙箱安装）的社区进展。
