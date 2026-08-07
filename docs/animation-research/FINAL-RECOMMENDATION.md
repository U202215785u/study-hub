# 首页交互动效改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变首页信息架构、业务行为和键盘操作的前提下，为首页增加可降级、可测试、可逐阶段回滚的入场、状态切换、弹层、微交互和 Bento 重排动效。

**Architecture:** CSS/Vue `<Transition>` 负责微交互和组件出入场；GSAP 3.15 core 仅负责首页时间线和数字插值，Flip 仅负责 Bento 布局变化。所有 GSAP import 经过本地 adapter，组件通过小型 composable 使用动画；首页仍由 `Home.vue` 统一编排。

**Tech Stack:** Vue 3.5、Vite 5、Vitest 2、Storybook 8.6、Playwright 1.62、GSAP 3.15 core + Flip、现有 CSS motion tokens。

---

## 0. 已确认决策

- 用户已明确接受 GSAP 3.15 的 `Standard no charge license`。该许可不是 MIT；代码、文档和依赖清单不得再标注为 MIT。
- 不引入 ScrollTrigger、SplitText、Lenis、motion-v 或第二动画引擎。首页没有需要它们解决的场景。
- GSAP 只进入首页懒加载链路。`/` 当前通过 `() => import('../views/Home.vue')` 懒加载，不得把 GSAP 提升到应用入口。
- 动画只改变 `transform` 和 `opacity`；不得动画 `width`、`height`、`top`、`left` 或影响布局的属性。
- `prefers-reduced-motion: reduce` 必须直接呈现最终状态，不播放替代动画。
- Phase 5 数字计数是可选提交；核心验收通过后才能合入。
- 热力图 196 格逐格点亮不在本轮范围。

## 1. 成功标准

全部满足才可宣布完成：

- `npm run test:unit` 全绿，且新增动画单测覆盖清理、毫秒换算、FLIP 调用顺序和四态 key。
- `npm run build` 与 `npm run build:storybook` 通过。
- `animations-*.js` 单独 chunk 的 gzip 大小不超过 45 KiB；超出即停止，不通过调高阈值放行。
- 正常模式下，导航、问候、当前默认 9 个 widget 完成一次错峰入场；接口加载完成不会重新触发入场。若默认布局以后增减，测试从 registry/layout 读取期望数量，不硬编码旧值。
- reduced-motion 模式下，首帧无透明、无位移、无计数过程，最终内容完整可见。
- hide/show/reorder/cancel/restore 都按正确 FLIP 顺序执行；save 不重复播放布局动画。
- 4 个 modal、1 个 drawer、1 个 toast 有出入场；DashboardEditor 作为第 7 个 fixed surface 单独覆盖。
- Tab 循环、Esc 关闭、关闭后焦点恢复和点击遮罩关闭行为与当前版本一致。
- Playwright 在 390x844、942x638、1440x980 三个视口验证终态，无横向溢出或布局漂移。
- 每个实施任务独立提交；任一任务可通过 revert 自身提交回滚。

## 2. 多代理协作协议

### 2.1 开工前强制步骤

协调代理必须先执行：

```bash
bash scripts/check-uncommitted.sh
```

若当前 Windows 环境不能运行 bash，使用 PowerShell 逐个读取 `git worktree list --porcelain` 中的路径，并在每个路径执行 `git status --porcelain`。发现未提交或未跟踪内容时，先提交或 stash，并记录分支、工作树路径和 stash 名称。不得删除任何脏 worktree。

每次实际分派前，协调代理必须：

1. 调用 `butler_create_task_card` 生成五行任务卡。
2. 将返回的五行原样交给执行代理。
3. 执行代理调用 `butler_accept_task_card` 后开工。
4. 执行代理完成后调用 `butler_report_execution_result`，返回提交、文件、测试和未决风险。

### 2.2 文件所有权

- 同一波次内，两个代理不得修改同一文件。
- 真正并行写入的代理必须使用各自独立的 branch/worktree；若协调环境只能共享一个工作目录，则同一时间只允许一个写代理，其他代理仅做只读调查。
- 创建新 worktree 前先完成 2.1 的全量盘点。清理任何 worktree 前再次盘点，并确认该 worktree 的提交已被协调代理接收。
- `Home.vue` 和 `Home.test.js` 只允许任务 6 的集成代理修改。
- `package.json`、`package-lock.json`、`vite.config.js` 只允许任务 1 修改。
- `.storybook/preview.js` 和 `tests/home-motion.mjs` 只允许任务 5 修改。
- 执行代理不得修改本计划、项目记忆或其他任务的测试来绕过失败。
- 发现必须越界时停止，向协调代理报告；不得自行扩大范围。

### 2.3 波次与依赖

| 波次 | 可并行任务 | 前置条件 | 汇合门禁 |
|---|---|---|---|
| Gate | 任务 0：基线与安全盘点 | 无 | 工作树安全、基线测试通过 |
| Wave 1 | 任务 1、2、3 | Gate 通过 | 三个任务各自测试通过并提交 |
| Wave 2 | 任务 4、5；任务 7 可选 | 任务 1 已提交 | composable、浏览器验收脚本完成 |
| Wave 3 | 任务 6：Home 集成 | 任务 1、3、4、5 完成；任务 2 可独立先合入 | Home 单测和 motion e2e 通过 |
| Wave 4 | 任务 8：独立总验收 | 必选任务全部合入 | 全量证据齐全 |

最大并发建议为 3。任务 6 和任务 8 必须串行执行。

### 2.4 命令工作目录

- `npm`、`npx`、`node` 命令均在 `study-hub/frontend` 目录执行。
- `git add/commit/status` 命令均在工作区根目录执行，因此计划中的 Git 路径以 `study-hub/frontend/` 开头。
- 工作树安全检查在工作区根目录执行。执行代理不得因为当前 shell 位于其他目录而改写命令目标。

## 3. 任务 0：协调代理完成基线与 PoC 门禁

**Files:** 不修改源码。

- [ ] 运行工作树安全检查并记录结果。
- [ ] 在 `study-hub/frontend` 运行基线：

```bash
npm run test:unit
npm run build
npm run build:storybook
```

预期：49 个测试文件、111 项测试基线通过；两个构建退出码为 0。数量允许随用户现有改动增加，但不允许减少或出现失败。

- [ ] 记录当前 `Home-*.js` gzip 大小和当前 Git HEAD；这两项是后续体积与回滚证据。
- [ ] 确认端口 `5181` 未占用；占用时选择未使用端口并设置 `STUDY_UI_ORIGIN`，不得终止未知进程。
- [ ] 仅在 Gate 通过后分派 Wave 1。

**代理回传：** 工作树清单、基线命令与退出码、测试数量、Home chunk gzip、选定测试端口。

## 4. 任务 1：GSAP adapter、生命周期与体积门禁

**Owner:** motion-foundation agent

**Files:**

- Create: `study-hub/frontend/src/lib/gsap.js`
- Create: `study-hub/frontend/src/composables/useGsap.js`
- Create: `study-hub/frontend/src/composables/useGsap.test.js`
- Create: `study-hub/frontend/tests/animation-bundle-budget.mjs`
- Modify: `study-hub/frontend/package.json`
- Modify: `study-hub/frontend/package-lock.json`
- Modify: `study-hub/frontend/vite.config.js`

- [ ] 安装并锁定兼容版本：

```bash
npm install gsap@~3.15.0
```

确认 `package.json` 的许可证说明不写成 MIT；依赖版本必须进入 lockfile。

- [ ] 先写 `useGsap.test.js`，覆盖以下失败条件：

```js
expect(readCssTimeSeconds('--ui-duration-slow', root)).toBe(0.26)
expect(readCssTimeSeconds('--ui-duration-fast', root)).toBe(0.12)
expect(matchMedia.revert).toHaveBeenCalledOnce()
expect(context.revert).toHaveBeenCalledOnce()
```

测试需 mock 本地 `../lib/gsap.js`，不要只 mock `gsap` 而漏掉 `gsap/Flip`。

- [ ] 运行定向测试并确认先失败：

```bash
npx vitest run src/composables/useGsap.test.js
```

预期：模块不存在或导出不存在。

- [ ] 创建唯一 adapter：

```js
import { gsap } from 'gsap'
import { Flip } from 'gsap/Flip'

gsap.registerPlugin(Flip)

export { Flip, gsap }
```

- [ ] 实现 `useGsap.js`。公开接口固定为：

```js
export function readCssTimeSeconds(name, element = document.documentElement)
export function useGsap({ scope, setup, onReducedMotion })
```

实现要求：

```js
const resolveScope = (scope) => typeof scope === 'function' ? scope() : scope?.value

export function readCssTimeSeconds(name, element = document.documentElement) {
  const raw = getComputedStyle(element).getPropertyValue(name).trim()
  const value = Number.parseFloat(raw)
  if (!Number.isFinite(value)) return 0
  return raw.endsWith('ms') ? value / 1000 : value
}
```

`useGsap` 必须在 `onMounted` 后 `await nextTick()`，为 no-preference 和 reduce 各注册一个 `gsap.matchMedia()` 分支；no-preference 内建立 `gsap.context`，回调 cleanup 执行 `context.revert()`；组件卸载执行 `matchMedia.revert()`。不得注册全局常驻监听器。

- [ ] 在 `vite.config.js` 使用正确层级：

```js
build: {
  outDir: 'dist',
  emptyOutDir: true,
  rollupOptions: {
    output: {
      manualChunks: {
        animations: ['gsap', 'gsap/Flip'],
      },
    },
  },
},
```

- [ ] 创建 `animation-bundle-budget.mjs`：从 `dist/assets` 找到唯一的 `animations-*.js`，使用 `node:zlib` 的 `gzipSync` 计算实际 gzip，断言 `<= 45 * 1024`；缺少或出现多个 animations chunk 都失败。
- [ ] 在 `package.json` 增加：

```json
"test:animation-budget": "npm run build && node tests/animation-bundle-budget.mjs",
"test:home-motion": "node tests/home-motion.mjs"
```

- [ ] 验证：

```bash
npx vitest run src/composables/useGsap.test.js
npm run test:animation-budget
```

预期：测试通过，animations gzip 不超过 45 KiB。超限时停止任务并回报，不得修改阈值。

- [ ] 提交：

```bash
git add study-hub/frontend/package.json study-hub/frontend/package-lock.json study-hub/frontend/vite.config.js study-hub/frontend/src/lib/gsap.js study-hub/frontend/src/composables/useGsap.js study-hub/frontend/src/composables/useGsap.test.js study-hub/frontend/tests/animation-bundle-budget.mjs
git commit -m "feat(home): add scoped GSAP motion foundation"
```

**代理回传：** commit SHA、animations chunk 原始/gzip 大小、定向测试结果、许可证记录。

## 5. 任务 2：纯 CSS 微交互

**Owner:** micro-interactions agent

**Files:**

- Modify: `study-hub/frontend/src/design-system/patterns/CapsuleNavigation.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/CalendarAgendaWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/DailyMemoryWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/CreationWidget.vue`
- Modify: `study-hub/frontend/src/design-system/widgets/CompactWidgets.test.js`
- Create: `study-hub/frontend/src/design-system/MicroInteractions.motion.test.js`

- [ ] 先扩充测试，确认点击、RouterLink、事件次数和 DOM 数量与基线相同。微交互不得改变可点击元素、tab 顺序或事件目标。
- [ ] 运行定向测试并保存基线结果：

```bash
npx vitest run src/design-system/MicroInteractions.motion.test.js src/design-system/widgets/CompactWidgets.test.js
```

- [ ] 仅在精细指针设备启用 hover：

```css
@media (hover: hover) and (pointer: fine) {
  /* declarations stay inside this media query */
}
```

- [ ] 在 `MicroInteractions.motion.test.js` 挂载四个组件，验证 CapsuleNavigation 事件不变、Calendar 选择事件只发一次、DailyMemory 的覆盖按钮与 RouterLink 仍是两个独立焦点、Creation 条目数量和 open payload 不变。
- [ ] CapsuleNavigation：链接使用 `background-color/color/transform` transition；hover `translateY(-1px)`，active `scale(1.03)`。时长使用 `--ui-duration-fast`，缓动使用 `--ui-ease-standard`。
- [ ] CalendarAgendaWidget：日期按钮 transition transform/background-color；hover `scale(1.04)`，selected `scale(1.06)`。不得改变 38px 稳定尺寸。
- [ ] DailyMemoryWidget：只移动 `.memory-widget__stack` 装饰层，hover/focus-within 为 `translateY(-3px)`；不得移动覆盖整卡的 `.memory-widget__review`。
- [ ] CreationWidget：条目 hover 仅 `translateY(-2px)`；不得加入 CSS 入场 stagger，避免与首页 GSAP 入场重复。
- [ ] 所有 transition 使用现有 `--ui-duration-*` 和 `--ui-ease-standard`；不得硬编码 180ms/260ms。
- [ ] 重新运行定向测试并提交：

```bash
npx vitest run src/design-system/MicroInteractions.motion.test.js src/design-system/widgets/CompactWidgets.test.js
git add study-hub/frontend/src/design-system/patterns/CapsuleNavigation.vue study-hub/frontend/src/design-system/widgets/CalendarAgendaWidget.vue study-hub/frontend/src/design-system/widgets/DailyMemoryWidget.vue study-hub/frontend/src/design-system/widgets/CreationWidget.vue study-hub/frontend/src/design-system/widgets/CompactWidgets.test.js study-hub/frontend/src/design-system/MicroInteractions.motion.test.js
git commit -m "feat(home): add token-based dashboard micro-interactions"
```

**代理回传：** commit SHA、修改的 selector、键盘/触屏保护说明、测试结果。

## 6. 任务 3：卡片四态过渡

**Owner:** card-transition agent

**Files:**

- Modify: `study-hub/frontend/src/design-system/patterns/DashboardModuleCard.vue`
- Modify: `study-hub/frontend/src/design-system/patterns/DashboardModuleCard.stories.js`
- Create: `study-hub/frontend/src/design-system/patterns/DashboardModuleCard.motion.test.js`

任务 3 不修改 `FaithfulDashboardPatterns.test.js`，因此与任务 2 没有共享文件，可以并行执行。

- [ ] 新建 `DashboardModuleCard.motion.test.js`。保存切换前的状态节点 `element`，更新 props 后断言新状态节点不是同一个 element，以证明 `:key="state"` 生效；同时断言类名随 `loading → error → empty → content` 改变，并保持 `data-card-inset="16"`。
- [ ] 运行测试确认失败。
- [ ] 将四个同标签分支改成一个带 key 的过渡节点：

```vue
<Transition name="card-state" mode="out-in">
  <div
    :key="state"
    :class="[
      state === 'content' ? 'dashboard-module-card__content' : 'dashboard-module-card__state',
      { 'dashboard-module-card__state--error': state === 'error' },
    ]"
    :data-card-inset="state === 'content' ? '16' : undefined"
  >
    <slot v-if="state === 'content'" />
    <template v-else-if="state === 'loading'">加载中</template>
    <template v-else-if="state === 'error'">{{ error }}</template>
    <template v-else>{{ emptyText }}</template>
  </div>
</Transition>
```

- [ ] CSS 只使用 opacity + `translateY(6px)`，时长 `--ui-duration-normal`。leave-active 和 enter-active 都必须定义；归零 token 自动处理 reduced-motion。
- [ ] Storybook 保留现有四态 story，并新增一个交互 story 按固定按钮顺序切换状态；不得依赖定时器自动循环。
- [ ] 验证并提交：

```bash
npx vitest run src/design-system/patterns/DashboardModuleCard.motion.test.js src/design-system/patterns/FaithfulDashboardPatterns.test.js
npm run build:storybook
git add study-hub/frontend/src/design-system/patterns/DashboardModuleCard.vue study-hub/frontend/src/design-system/patterns/DashboardModuleCard.motion.test.js study-hub/frontend/src/design-system/patterns/DashboardModuleCard.stories.js
git commit -m "feat(home): animate dashboard card state changes"
```

**代理回传：** commit SHA、四态切换测试、Storybook 构建结果。

## 7. 任务 4：首页入场与 FLIP 领域逻辑

**Owner:** home-motion-logic agent

**Depends on:** 任务 1

**Files:**

- Create: `study-hub/frontend/src/composables/home/useHomeEntrance.js`
- Create: `study-hub/frontend/src/composables/home/useHomeEntrance.test.js`
- Create: `study-hub/frontend/src/composables/home/useDashboardFlip.js`
- Create: `study-hub/frontend/src/composables/home/useDashboardFlip.test.js`

- [ ] 为 `playHomeEntrance` 先写失败测试，固定 selector 顺序：navigation → greeting → widget items。断言 timeline 只创建一次，不引用接口 promise。
- [ ] 实现接口：

```js
export function playHomeEntrance({ gsap, root, duration })
```

实现使用 `gsap.utils.selector(root)`，目标分别为 `[data-home-motion="navigation"]`、`[data-home-motion="greeting"]`、`[data-home-motion="widget"]`。timeline 使用 `from`、`clearProps: 'transform,opacity'`、导航和问候固定 offset、widget `stagger: 0.05`。不得设置持久初始 hidden 样式。

- [ ] 为 `createDashboardFlip` 先写失败测试，严格验证调用顺序：

```text
getTargets -> Flip.getState -> mutate -> nextTick -> Flip.from
```

同时验证 reduced-motion 分支为 `mutate -> nextTick`，且从不调用 Flip。

- [ ] 实现接口：

```js
export function createDashboardFlip({ Flip, gsap, getTargets, nextTick, reducedMotion, duration })
```

返回 `run(mutate)`。正常模式必须在 mutate 前 `Flip.getState(getTargets())`，在 `await nextTick()` 后执行 `Flip.from(state, options)`；不得把 selector 字符串传给 `Flip.from` 代替 state。options 固定包含 `absolute: true`、`duration`、`ease: 'power2.out'`、enter/leave opacity+scale 回调。

- [ ] 覆盖 empty targets、同步 mutation 抛错和连续调用。连续调用时先 kill 上一个 Flip animation，避免叠加 transform。
- [ ] 验证并提交：

```bash
npx vitest run src/composables/home/useHomeEntrance.test.js src/composables/home/useDashboardFlip.test.js
git add study-hub/frontend/src/composables/home/useHomeEntrance.js study-hub/frontend/src/composables/home/useHomeEntrance.test.js study-hub/frontend/src/composables/home/useDashboardFlip.js study-hub/frontend/src/composables/home/useDashboardFlip.test.js
git commit -m "feat(home): add testable entrance and FLIP controllers"
```

**代理回传：** commit SHA、FLIP 顺序断言、连续调用策略、测试结果。

## 8. 任务 5：Storybook 与 Playwright 动效验收

**Owner:** motion-test agent

**Depends on:** 任务 1；可与任务 4 并行。

**Files:**

- Modify: `study-hub/frontend/.storybook/preview.js`
- Create: `study-hub/frontend/tests/home-motion.mjs`

- [ ] 在 Storybook 增加 `reducedMotion` toolbar，但在注释中明确：toolbar 只负责 CSS token 预览，真实 `matchMedia` 分支由 Playwright 验证。
- [ ] decorator 在预览根节点设置 `data-reduced-motion="true"`，并通过继承覆盖三个 duration token 为 `0ms`；切回 normal 时删除属性。不得永久 monkey-patch `window.matchMedia`。
- [ ] 创建 `home-motion.mjs`，复用现有 Playwright 启动 fallback 和 `TEST_PORTS.dashboard`。
- [ ] 正常模式从 `[data-home-motion="widget"]` 实际数量与 dashboard registry/layout 期望数量比对（当前默认 9 个），并验证终态 `opacity: 1`、transform 为 none/单位矩阵；打开并关闭每日复盘后焦点回到触发按钮；编辑器 hide/show/cancel 后所有可见卡片 box 非空。
- [ ] reduced 模式使用浏览器真实能力：

```js
const context = await browser.newContext({
  viewport: { width: 1440, height: 980 },
  reducedMotion: 'reduce',
})
```

在 `domcontentloaded` 后立即断言动效目标没有 `opacity: 0` 或非终态 translate，再在 400ms 后断言布局 box 未变化。

- [ ] 对 390x844、942x638、1440x980 终态截图，文件写入 `test-results/study-ui-motion/`；断言每张截图大于 10KB。
- [ ] 本任务只做脚本语法验证；完整 e2e 在任务 6 集成后运行：

```bash
node --check tests/home-motion.mjs
npm run build:storybook
```

- [ ] 提交：

```bash
git add study-hub/frontend/.storybook/preview.js study-hub/frontend/tests/home-motion.mjs
git commit -m "test(home): add motion and reduced-motion acceptance coverage"
```

**代理回传：** commit SHA、覆盖的浏览器场景、脚本语法和 Storybook 构建结果。

## 9. 任务 6：Home 唯一集成任务

**Owner:** home-integration agent

**Depends on:** 任务 1、3、4、5；任务 2 可独立合入。开始前必须确认没有其他代理正在编辑 Home 文件。

**Files:**

- Modify: `study-hub/frontend/src/views/Home.vue`
- Modify: `study-hub/frontend/src/views/Home.test.js`

- [ ] 先扩充 Home 测试，覆盖：`data-flip-id` 使用真实 widget id；save 不触发 FLIP；hide/show/reorder/cancel/restore 触发；关闭 modal 后而非开始离场时恢复焦点。
- [ ] mock 本地 adapter/composable，不直接依赖真实 requestAnimationFrame。运行测试确认新增断言先失败。
- [ ] 给现有节点增加稳定标识：

```vue
<WorkbenchFrame ref="motionScope">
  <template #navigation>
    <CapsuleNavigation
      data-home-motion="navigation"
      @search="searchFromNavigation"
      @notify="showToast('暂无新通知')"
      @edit="beginEdit"
    />
  </template>
  <template #greeting>
    <GreetingBar data-home-motion="greeting" />
  </template>

  <div class="home-dashboard-grid" data-visual-anchor="grid">
    <BentoDashboardGrid>
      <div
        v-for="widget in visibleWidgets"
        :key="widget.id"
        class="home-dashboard-grid__item"
        data-home-motion="widget"
        :data-module-id="widget.id"
        :data-flip-id="widget.id"
        :style="widgetStyle(widget)"
      >
        <component :is="registry[widget.id].component" v-bind="propsFor(widget.id)" v-on="listenersFor(widget.id)" />
      </div>
    </BentoDashboardGrid>
  </div>
</WorkbenchFrame>
```

传给 `useGsap` 的 scope resolver 使用 `motionScope.value?.$el`。只查询并动画 frame 内部的标记节点，绝不动画 WorkbenchFrame 自身已有的缩放/平移 transform。

`data-flip-id` 必须使用 `:` 动态绑定，不能写成字面量 `widget.id`。

- [ ] 入场在首次 mounted/nextTick 后立即启动，与 `loadDocuments/loadReviewHistory/loadDdlTasks` 的 Promise 完全解耦。数据加载完成不得重播。
- [ ] 为布局 API 保留原始方法，并包装真正改变主网格的操作：hide、show、reorder、cancelEdit、restoreDefault。save 直接调用原方法，不运行 FLIP。
- [ ] DashboardEditor 的拖拽元素与首页卡片不是同一 DOM；不得给编辑器行应用 GSAP。FLIP 只作用于 `.home-dashboard-grid__item`。
- [ ] 分别包裹 4 个 modal、drawer、toast 和 DashboardEditor 的 `<Transition>`。modal/drawer 使用遮罩 opacity + 面板 transform；toast 使用 opacity + translateY；editor 使用 translateX。所有时长引用 token。
- [ ] 修改 `watch(activeSurface)`：只负责打开后的 `nextTick + focusSurface`。移除关闭分支中的立即 `restoreFocus()`。
- [ ] 每个 modal/drawer Transition 使用 `@after-leave="restoreFocusAfterLeave"`。该函数仅在 `activeSurface.value` 为空时调用 `restoreFocus()`，避免一个弹层切换到另一个弹层时焦点回到页面底层。
- [ ] 保持现有 Esc、Tab trap、遮罩点击和 `rememberFocus` 行为；确保每个打开入口先调用 `rememberFocus()`。
- [ ] 定向验证：

```bash
npx vitest run src/views/Home.test.js src/composables/home/useHomeEntrance.test.js src/composables/home/useDashboardFlip.test.js
```

- [ ] 启动独立测试服务器：

```bash
npm run dev -- --port 5181
```

在另一个终端运行：

```bash
npm run test:home-motion
```

预期：normal/reduce、三个视口、焦点和 FLIP 场景全部通过。

- [ ] 提交：

```bash
git add study-hub/frontend/src/views/Home.vue study-hub/frontend/src/views/Home.test.js
git commit -m "feat(home): integrate accessible dashboard motion"
```

**代理回传：** commit SHA、Home 测试、Playwright 结果、截图目录、焦点恢复证据。

## 10. 任务 7：数字计数（可选，核心通过后执行）

**Owner:** counter-motion agent

**Depends on:** 任务 1；不得阻塞核心交付。

**Files:**

- Create: `study-hub/frontend/src/composables/useAnimatedNumber.js`
- Create: `study-hub/frontend/src/composables/useAnimatedNumber.test.js`
- Modify: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue`
- Create: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.motion.test.js`

- [ ] 先写失败测试：正常模式从旧整数插值到新整数；reduce 模式同步写终值；组件卸载 kill tween；值不变不创建 tween。
- [ ] `useAnimatedNumber` 只返回一个只读显示 ref，内部使用 `gsap.to`、`snap: { value: 1 }`；duration 来自 `--ui-duration-slow`。
- [ ] TodayFocusWidget 只替换 header badge 的 completed/total 显示值，不改变业务 computed、DOM 尺寸或 accessible name。计数节点不得设置 `aria-live`，避免逐帧播报。
- [ ] 验证并提交：

```bash
npx vitest run src/composables/useAnimatedNumber.test.js src/design-system/widgets/TodayFocusWidget.motion.test.js
git add study-hub/frontend/src/composables/useAnimatedNumber.js study-hub/frontend/src/composables/useAnimatedNumber.test.js study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue study-hub/frontend/src/design-system/widgets/TodayFocusWidget.motion.test.js
git commit -m "feat(home): animate task counters with reduced-motion fallback"
```

**代理回传：** commit SHA、normal/reduce/cleanup 测试；协调代理可决定不合入此提交。

## 11. 任务 8：独立审查与最终验收

**Owner:** verification agent。不得由任务 6 的集成代理兼任。

**Files:** 默认不修改源码；发现问题时退回原 owner，不直接跨域修复。

- [ ] 检查各提交仅包含声明文件；确认没有代理修改本计划、项目记忆或无关模块。
- [ ] 检查 dependency graph：应用入口 chunk 不得 import GSAP；animations chunk 只随 Home 路由加载。
- [ ] 运行完整验证：

```bash
npm run test:unit
npm run test:animation-budget
npm run build:storybook
```

- [ ] 在 5181 端口启动前端并运行：

```bash
npm run test:home-motion
node tests/home-responsive.mjs
node tests/home-layout-persistence.mjs
node tests/home-visual-overlay.mjs
```

- [ ] 手动/浏览器检查：正常模式、reduce 模式、运行时切换 reduce、Esc、Tab/Shift+Tab、遮罩点击、hide/show/reorder/cancel/restore、快速连续点击。
- [ ] 确认无控制台 error、无残留 inline opacity/transform、离开首页再返回不会累积 matchMedia listener。
- [ ] 输出最终验收表：每条成功标准对应命令、截图或 DOM 证据；任何失败都保持任务未完成。

**代理回传：** 完整命令、退出码、测试数量、chunk gzip、截图路径、失败项和回退到哪个 owner。

## 12. 回滚边界

| 提交 | 可独立回滚 | 回滚影响 |
|---|---|---|
| 任务 1 motion foundation | 是，但须先回滚依赖它的任务 4/6/7 | 移除 GSAP、adapter、chunk 和预算脚本 |
| 任务 2 微交互 | 是 | 仅移除 hover/focus 视觉反馈 |
| 任务 3 卡片状态 | 是 | 四态恢复无过渡切换 |
| 任务 4 motion logic | 是，但须先回滚任务 6 | 移除入场/FLIP controller |
| 任务 5 motion tests | 是 | 只移除验收基础设施，不修复产品问题 |
| 任务 6 Home 集成 | 是 | 首页恢复当前行为，保留未使用 foundation |
| 任务 7 数字计数 | 是 | badge 恢复同步数字 |

禁止用 `git reset --hard` 或覆盖式 checkout 回滚。使用 `git revert <sha>`；执行前再次运行 worktree 未提交检查。

## 13. 最终派发顺序

协调代理按以下顺序操作：

1. 自己完成任务 0。
2. 并行派发任务 1、2、3；任务 2/3 必须使用不同测试文件避免冲突。
3. 任务 1 通过后，并行派发任务 4、5；核心稳定后再决定是否派发任务 7。
4. 合入任务 1、3、4、5 后，单独派发任务 6；任务 2 可在任务 6 前后独立合入。
5. 必选提交集成完成后派发任务 8。
6. 只有任务 8 的全部证据通过，管家才记录 validation passed 并完成 case。

本计划不授权自动发布、部署、删除 worktree 或清理分支；这些操作仍需单独确认。
