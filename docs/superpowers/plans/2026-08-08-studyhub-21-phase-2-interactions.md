# STUDYHUB-21 Phase 2 交互动效 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不重复驱动既有 Widget、GSAP 或 Vue Transition 的前提下，为首页完成数、自动化完成反馈和页面导航加入可降级的 Phase 2 动效。

**Architecture:** 数字显示由独立的 `AnimatedNumber` 组件使用 `requestAnimationFrame` 驱动，只渲染文字且在减少动态效果时立即呈现终态。队列组合式只识别任务首次进入 `done` 并把该任务交给 Home；Home 在知识库刷新后用现有 Toast 报告完成，并保护正在显示的错误。路由层以一个可单测的导航包装器包住 `push` 和 `replace`，仅在浏览器提供 View Transitions 且用户未要求减少动态效果时启用，否则直接导航。

**Tech Stack:** Vue 3 Composition API、Vue Router 4、Vitest、Vue Test Utils、浏览器 View Transitions API。

---

## 文件职责

- `study-hub/frontend/src/design-system/components/data-display/AnimatedNumber.vue`：独占数值文字的帧动画与 reduced-motion 终态。
- `study-hub/frontend/src/design-system/components/data-display/AnimatedNumber.test.js`：验证数值终态、减少动态效果与卸载清理。
- `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue`：仅把完成数和总数交给 `AnimatedNumber`；不改变 Widget 容器动画。
- `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.test.js`：验证任务统计数传递给数字组件。
- `study-hub/frontend/src/composables/home/useAutomationQueue.js`：仅在任务首次到达 `done` 时发出完成回调，并把任务传出。
- `study-hub/frontend/src/composables/home/useAutomationQueue.test.js`：验证重复轮询不重复反馈、错误不触发成功、重试后的新完成再次反馈。
- `study-hub/frontend/src/composables/useRouteTransition.js`：独占浏览器能力判断与单次路由导航转场协调。
- `study-hub/frontend/src/composables/useRouteTransition.test.js`：验证能力缺失、减少动态效果、View Transition 成功与快速导航退化。
- `study-hub/frontend/src/router/index.js`：将已创建路由器的 `push`/`replace` 接到导航包装器；路由定义不变。
- `study-hub/frontend/src/views/Home.vue`：使用任务完成回调显示一次性成功反馈，并禁止成功提示覆盖可见错误提示。
- `study-hub/frontend/src/views/Home.test.js`：验证队列任务从运行中变为完成后只出现一次成功反馈，且既有 Widget 事件仍可达。

### Task 1: 数字终态动画

**Files:**
- Create: `study-hub/frontend/src/design-system/components/data-display/AnimatedNumber.vue`
- Create: `study-hub/frontend/src/design-system/components/data-display/AnimatedNumber.test.js`
- Modify: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue`
- Create: `study-hub/frontend/src/design-system/widgets/TodayFocusWidget.test.js`

- [ ] **Step 1: 写入会失败的组件测试**

```js
it('在动画结束时呈现目标整数', async () => {
  const frames = []
  vi.stubGlobal('requestAnimationFrame', (callback) => { frames.push(callback); return frames.length })
  const wrapper = mount(AnimatedNumber, { props: { value: 7, duration: 200, reducedMotion: 'never' } })
  frames.shift()(0)
  frames.shift()(200)
  await wrapper.vm.$nextTick()
  expect(wrapper.text()).toBe('7')
})

it('用户要求减少动态效果时立即显示终态', () => {
  const wrapper = mount(AnimatedNumber, { props: { value: 12, reducedMotion: 'always' } })
  expect(wrapper.text()).toBe('12')
})
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `npm run test:unit -- src/design-system/components/data-display/AnimatedNumber.test.js`

Expected: FAIL，原因是 `AnimatedNumber.vue` 尚不存在。

- [ ] **Step 3: 实现最小的数字组件**

```vue
<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useMediaQuery } from '@vueuse/core'

const props = defineProps({ value: { type: Number, default: 0 }, duration: { type: Number, default: 280 }, reducedMotion: { type: String, default: 'user' } })
const prefersReduced = useMediaQuery('(prefers-reduced-motion: reduce)')
const reduced = computed(() => props.reducedMotion === 'always' || (props.reducedMotion === 'user' && prefersReduced.value))
const displayed = ref(0)
let frame

function cancel() { if (frame) cancelAnimationFrame(frame); frame = undefined }
function animate(target) {
  const from = displayed.value
  const startedAt = performance.now()
  const tick = (now) => {
    const progress = Math.min((now - startedAt) / props.duration, 1)
    displayed.value = Math.round(from + (target - from) * progress)
    frame = progress < 1 ? requestAnimationFrame(tick) : undefined
  }
  frame = requestAnimationFrame(tick)
}
watch([() => props.value, reduced], ([value, isReduced]) => { cancel(); isReduced ? displayed.value = Math.round(value) : animate(Math.round(value)) }, { immediate: true })
onBeforeUnmount(cancel)
</script>
<template><span data-animated-number>{{ displayed }}</span></template>
```

- [ ] **Step 4: 运行组件测试确认 GREEN**

Run: `npm run test:unit -- src/design-system/components/data-display/AnimatedNumber.test.js`

Expected: PASS，两个测试通过。

- [ ] **Step 5: 写入 TodayFocus 的失败测试，再接入组件**

```js
it('将完成数和总数交给独立的数字终态组件', () => {
  const wrapper = mount(TodayFocusWidget, { props: { totalTaskCount: 8, completedTaskCount: 3 } })
  expect(wrapper.findAll('[data-animated-number]').map((node) => node.text())).toEqual(['3', '8'])
})
```

将原来的 `<b>{{ completedCount }}/{{ totalCount }}</b>` 替换为只包含两个 `AnimatedNumber` 的 `<b>`。组件只管理文本，不写入容器的 `transform` 或 `opacity`。

- [ ] **Step 6: 运行两个数字相关测试确认 GREEN**

Run: `npm run test:unit -- src/design-system/components/data-display/AnimatedNumber.test.js src/design-system/widgets/TodayFocusWidget.test.js`

Expected: PASS。

### Task 2: 自动化完成的一次性反馈

**Files:**
- Modify: `study-hub/frontend/src/composables/home/useAutomationQueue.test.js`
- Modify: `study-hub/frontend/src/composables/home/useAutomationQueue.js`
- Modify: `study-hub/frontend/src/views/Home.vue`
- Modify: `study-hub/frontend/src/views/Home.test.js`

- [ ] **Step 1: 写入失败的队列状态测试**

```js
it('只在任务首次进入 done 时报告，并在重试后允许下一次完成', async () => {
  const onCompleted = vi.fn()
  const apiGet = vi.fn()
    .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', title: '解析任务', status: 'done' }] })
    .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', title: '解析任务', status: 'done' }] })
    .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', title: '解析任务', status: 'running' }] })
    .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', title: '解析任务', status: 'done' }] })
  const queue = useAutomationQueue({ apiGet, apiPost: vi.fn(), apiDelete: vi.fn(), onCompleted })
  await queue.refresh(); await queue.refresh(); await queue.refresh(); await queue.refresh()
  expect(onCompleted).toHaveBeenCalledTimes(2)
  expect(onCompleted).toHaveBeenLastCalledWith(expect.objectContaining({ task_id: 'q1', status: 'done' }))
})

it('任务首次进入 error 时不触发成功反馈', async () => {
  const onCompleted = vi.fn()
  const queue = useAutomationQueue({ apiGet: vi.fn().mockResolvedValue({ tasks: [{ task_id: 'q1', status: 'error' }] }), apiPost: vi.fn(), apiDelete: vi.fn(), onCompleted })
  await queue.refresh()
  expect(onCompleted).not.toHaveBeenCalled()
})
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `npm run test:unit -- src/composables/home/useAutomationQueue.test.js`

Expected: FAIL，因为当前实现把 error 与 done 混为无参数的完成回调，且首次 done 不能携带任务。

- [ ] **Step 3: 最小化更新队列状态机与 Home 回调**

```js
let completedTask
if (task.status === 'done' && terminalStateByTask.get(taskId) !== 'done') completedTask = task
if (task.status === 'done' || task.status === 'error') terminalStateByTask.set(taskId, task.status)
else terminalStateByTask.delete(taskId)
if (completedTask) await onCompleted(completedTask)
```

Home 的回调必须先 `await knowledgeApi.reload()`，再调用 `showToast`；Toast 函数在可见错误提示存在时忽略新的成功提示，错误提示仍可以覆盖旧成功提示。

- [ ] **Step 4: 运行队列测试确认 GREEN**

Run: `npm run test:unit -- src/composables/home/useAutomationQueue.test.js`

Expected: PASS，轮询重复、错误状态及重试都符合断言。

- [ ] **Step 5: 写入 Home 的失败集成测试并实现**

```js
it('队列任务第一次完成后显示一次成功反馈', async () => {
  // 第一次 /automation/queue/status 返回 running，第二次返回同一任务 done。
  // 推进一个轮询间隔后，断言 .home-toast 只含“解析任务已完成”。
})
```

保留 `listenersFor(widget.id)` 和 `v-bind="propsFor(widget.id)"`，不移动 `MotionWrapper`，以确保九个 Widget 的业务事件和 Phase 1B hover/press 保持可达。

- [ ] **Step 6: 运行 Home 与队列测试确认 GREEN**

Run: `npm run test:unit -- src/composables/home/useAutomationQueue.test.js src/views/Home.test.js`

Expected: PASS。

### Task 3: 具备能力探测的页面转场

**Files:**
- Create: `study-hub/frontend/src/composables/useRouteTransition.js`
- Create: `study-hub/frontend/src/composables/useRouteTransition.test.js`
- Modify: `study-hub/frontend/src/router/index.js`

- [ ] **Step 1: 写入失败的导航包装测试**

```js
it('有 View Transition 能力且未减少动态效果时在转场回调中导航', async () => {
  const navigate = vi.fn().mockResolvedValue(undefined)
  const startViewTransition = vi.fn(async (update) => { await update(); return { finished: Promise.resolve() } })
  await createRouteTransition({ documentRef: { startViewTransition }, matchMedia: () => ({ matches: false }), nextTick: vi.fn() }).navigate(navigate, '/kb')
  expect(startViewTransition).toHaveBeenCalledTimes(1)
  expect(navigate).toHaveBeenCalledWith('/kb')
})

it('能力缺失或减少动态效果时直接导航', async () => {
  const navigate = vi.fn().mockResolvedValue(undefined)
  await createRouteTransition({ documentRef: {}, matchMedia: () => ({ matches: true }) }).navigate(navigate, '/kb')
  expect(navigate).toHaveBeenCalledWith('/kb')
})
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `npm run test:unit -- src/composables/useRouteTransition.test.js`

Expected: FAIL，因为 `useRouteTransition.js` 尚不存在。

- [ ] **Step 3: 实现最小路由包装器并接入 router**

```js
export function createRouteTransition({ documentRef = document, matchMedia = window.matchMedia, nextTick = () => Promise.resolve() } = {}) {
  let running = false
  async function navigate(navigateTo, target) {
    if (running || typeof documentRef?.startViewTransition !== 'function' || matchMedia?.('(prefers-reduced-motion: reduce)')?.matches) return navigateTo(target)
    running = true
    let navigationResult
    try {
      const transition = documentRef.startViewTransition(async () => { navigationResult = await navigateTo(target); await nextTick() })
      await transition?.finished?.catch(() => undefined)
      return navigationResult
    } catch { return navigateTo(target) } finally { running = false }
  }
  return { navigate }
}
```

在 `router/index.js` 保存原始 `router.push`、`router.replace` 绑定后，用同一个 `createRouteTransition()` 实例包装。第二次快速导航在第一次转场尚未结束时直接路由，保证最后一次请求生效且不嵌套 View Transition。

- [ ] **Step 4: 运行路由包装器测试确认 GREEN**

Run: `npm run test:unit -- src/composables/useRouteTransition.test.js`

Expected: PASS。

- [ ] **Step 5: 加入快速导航与异常退化测试，再确认 GREEN**

```js
it('转场进行中时让下一次导航直接执行', async () => {
  // 保持第一条 transition.finished 未完成；第二次 navigate 必须调用普通导航且不新增 View Transition。
})

it('View Transition API 抛错时仍执行普通导航', async () => {
  // startViewTransition 抛错；断言 navigate 仍收到目标。
})
```

Run: `npm run test:unit -- src/composables/useRouteTransition.test.js`

Expected: PASS。

### Task 4: 全量回归与任务交接

**Files:**
- Modify: 本计划中的勾选状态，仅反映已实际完成的步骤。

- [ ] **Step 1: 运行定向测试**

Run: `npm run test:unit -- src/design-system/components/data-display/AnimatedNumber.test.js src/design-system/widgets/TodayFocusWidget.test.js src/composables/home/useAutomationQueue.test.js src/composables/useRouteTransition.test.js src/views/Home.test.js`

Expected: PASS。

- [ ] **Step 2: 运行全量验证**

Run: `npm run test:unit && npm run build && npm run test:home-motion`

Expected: 所有命令退出码为 0；`test:home-motion` 仍确认 MotionWrapper 的 hover/press 与 Widget 事件转发。

- [ ] **Step 3: 检查本阶段改动质量**

Run: `git diff --check -- study-hub/frontend/src/design-system/components/data-display/AnimatedNumber.vue study-hub/frontend/src/design-system/components/data-display/AnimatedNumber.test.js study-hub/frontend/src/design-system/widgets/TodayFocusWidget.vue study-hub/frontend/src/design-system/widgets/TodayFocusWidget.test.js study-hub/frontend/src/composables/home/useAutomationQueue.js study-hub/frontend/src/composables/home/useAutomationQueue.test.js study-hub/frontend/src/composables/useRouteTransition.js study-hub/frontend/src/composables/useRouteTransition.test.js study-hub/frontend/src/router/index.js study-hub/frontend/src/views/Home.vue study-hub/frontend/src/views/Home.test.js`

Expected: 无输出、退出码为 0。

- [ ] **Step 4: 回填任务板并进入审核**

重新读取 `STUDYHUB-21` 的版本号后，添加包含文件、验证命令和风险（浏览器不支持时直接导航）的评论；以最新版本将状态移为 `in_review`。不移动到 `done`，等待用户验收。
