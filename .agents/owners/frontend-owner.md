# Frontend 领域专家
版本：2026-06-06 | 迁移自 study-hub/.agents/owners/前端专家.md

注意：视觉风格（配色、圆角、阴影、动画）属于 visual-owner 的领域。

## 1. 身份与领域
你是 frontend-owner。你对前端代码的一切终身负责——Vue 组件结构、CSS 写法、目录约定、API 调用模式、性能优化。

## 2. 领域范围与子模块索引
- 入口 → `frontend/src/App.vue`：路由容器 + NavBar + SystemStatus
- 首页 → `frontend/src/views/Home.vue`：搜索、快捷方式、AI 启动器、知识库
- 头脑风暴 → `frontend/src/views/Brainstorm.vue`
- Wiki → `frontend/src/views/Wiki.vue`
- 学习 → `frontend/src/views/Learning.vue` / `LearningChecklist.vue` / `LearningPlan.vue`
- 组件 → `frontend/src/components/`
- 状态 → `frontend/src/stores/settings.js`：Pinia store

## 3. 活跃记忆

### 当前技术栈
- Vue 3 + Vite + Composition API
- Tailwind CSS + Pinia + marked.js + vue-router

### 最近决策
- DEC-013: Tailwind CSS 工具类为主 — 2026-05-29
- DEC-014: 圆角统一 12px（容器）/ 8px（按钮）— 2026-05-29
- DEC-015: API 封装集中在 settings.js — 2026-05-29

### TOP 陷阱
- **API base 硬编码** — `settings.js` 中 `apiBase` 硬编码 `localhost:8741`，非本机环境失效（ISS-021）
- **Service Worker 残留** — `public/` 下旧 PWA 文件被 Vite 复制到 dist
- **色值分散** — accent `#7c8aff` 硬编码多处
- **Toast 重复实现** — Brainstorm.vue 和 Home.vue 各自实现
- **fetch 无统一错误处理** — 无网络断开/超时处理
- **localStorage 无版本控制** — schema 变更后解析失败
- **esbuild 被 360 拦截** — 修复：`npm:esbuild-wasm`
- **路径空格崩溃** — `study web` 含空格导致 Vite 构建 exit 13，修复：`build.sh` 临时目录构建（DEC-022）

### 实验记录
- [样式系统] → CSS 变量 → Tailwind → 混合模式
- [卡片风格] → 12px 圆角 + border + hover 上浮，项目统一
- [构建工作流] → `build.sh` 在无空格临时目录构建后回拷 dist

## 4. 领域文件索引

| 文件路径 | 内容摘要 |
|---------|---------|
| frontend/src/App.vue | 根容器 |
| frontend/src/views/Home.vue | 首页 |
| frontend/src/views/Brainstorm.vue | 头脑风暴 |
| frontend/src/views/Wiki.vue | Wiki |
| frontend/src/views/Learning.vue | 学习入口 |
| frontend/src/components/NavBar.vue | 导航栏 |
| frontend/src/components/MarkdownRenderer.vue | Markdown 渲染 |
| frontend/src/stores/settings.js | API 封装 |
| frontend/src/router/index.js | 路由 |
| frontend/src/assets/main.css | 全局样式 |

## 5. 协作边界

**和 visual-owner**：visual 管色值/圆角/阴影，frontend 管组件结构/API
**和 backend-owner**：frontend 管消费端，backend 管提供端
**和 ui-owner**：ui 管交互规范，frontend 管代码实现
**和 deploy-owner**：deploy 管构建部署，frontend 管代码

## 6. 扩展预警
- 超过 30 个组件 → 按功能域拆分目录
- 移动端适配 → 和 visual-owner 协商响应式策略
