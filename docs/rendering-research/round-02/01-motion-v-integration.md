# Round 02 POC · Motion for Vue 集成参考

> 文档角色：证据层 / POC。当前决策以 `../综合报告.md` 为准；本文不授权安装依赖或开始实现。
> 独占工作包：W1-A Motion。目标文件：后续实现阶段的 `MotionWrapper` 及其测试、Storybook 配置。
> 研究环境：Vue 3.5、Vite 5、Storybook 8.6、Vitest 2.1、jsdom 25、Electron 28（静态兼容参考）。

## 1. 结论边界

- `MotionWrapper` 是 Phase 1B 的候选设计，只有在用户批准 `motion-v` 与 `@vueuse/core` 的真实构建增量后才实施。
- Phase 1A 不依赖 motion-v；本文件中的安装命令、组件代码和测试代码都是后续实施参考，不代表仓库已经拥有这些文件。
- 页面层只消费 design-system 的 `MotionWrapper`，不直接引入 motion-v。跨路由由 View Transitions（若能力存在）负责，弹层/列表由 Vue Transition 负责；同一元素只由一个系统驱动。
- 研究结论必须区分验证级别：包版本和 registry 元数据为联网查询记录；项目增量尚未做本仓库构建实测；Electron 仅有 Chromium 120 的静态兼容参考，没有实机验收。

## 2. 依赖与体积证据

| 项目 | 结果 | 验证级别 |
|---|---|---|
| `motion-v` | 研究时记录版本 `2.3.0`，peer 需要 Vue 和 `@vueuse/core` | registry / package metadata 查询 |
| `@vueuse/core` | 研究时记录版本 `14.4.0`；目标项目当时未安装 | registry / 本地 package 清单读取 |
| motion-v 全量入口 | 约 59.2 KB gzip | bundlephobia 查询记录，不是本项目构建结果 |
| 实际生产增量 | 只能在安装后通过 Vite 产物比较确认 | 待执行构建实测，不能写成固定值 |

推荐的实测记录格式：

```text
入口 chunk gzip: <bytes>
Home 首次打开的全部 JS 请求 gzip 合计: <bytes>
启用 MotionWrapper 新增异步 chunk gzip: <bytes>
Electron `file://` minified 字节数 / 解析耗时: <bytes> / <ms>
验证环境、命令和日期: <text>
```

## 3. `MotionWrapper` 契约

下面的示例以 `motion.div` 为唯一渲染目标，避免 `tag`、`as` 和动态组件之间出现未验证的 API 差异。`whileHover` 与 `whilePress` 始终是对象属性绑定，不能写成字符串。

```vue
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { motion } from 'motion-v'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  timing: { type: String, default: 'normal' },
  delay: { type: Number, default: 0 },
  initial: { type: [Boolean, Object], default: () => ({ opacity: 0, y: 16 }) },
  animate: { type: [Boolean, Object], default: () => ({ opacity: 1, y: 0 }) },
  exit: { type: [Boolean, Object], default: false },
  whileHover: { type: [Boolean, Object], default: undefined },
  whilePress: { type: [Boolean, Object], default: undefined },
  reducedMotion: { type: String, default: 'user' },
})

const prefersReduced = ref(false)
let mediaQuery

function syncReduced() {
  prefersReduced.value = Boolean(mediaQuery?.matches)
}

onMounted(() => {
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  syncReduced()
  mediaQuery.addEventListener?.('change', syncReduced)
})

onBeforeUnmount(() => mediaQuery?.removeEventListener?.('change', syncReduced))

const reduced = computed(() =>
  props.reducedMotion === 'always' ||
  (props.reducedMotion === 'user' && prefersReduced.value),
)
const resolvedInitial = computed(() => (reduced.value ? false : props.initial))
const resolvedTransition = computed(() =>
  reduced.value
    ? { duration: 0 }
    : { duration: props.timing === 'fast' ? 0.12 : 0.18, delay: props.delay },
)
</script>

<template>
  <motion.div
    v-bind="$attrs"
    :data-motion-state="reduced ? 'final' : 'animated'"
    :initial="resolvedInitial"
    :animate="props.animate"
    :exit="props.exit"
    :while-hover="reduced ? false : props.whileHover"
    :while-press="reduced ? false : props.whilePress"
    :transition="resolvedTransition"
  >
    <slot />
  </motion.div>
</template>
```

公共契约保持最小化：动效属性使用对象、媒体查询变化能够实时更新、reduced 模式直接渲染终态，普通 attrs（`class`、`style`、`data-*`）转发到真实元素。如果实际安装的 motion-v 版本提供了不同的组件绑定方式，必须先验证该 API，再整体更新示例。

首页接入必须同时保留业务 props 和事件转发：

```vue
<MotionWrapper
  v-for="(widget, index) in visibleWidgets"
  :key="widget.id"
  class="home-dashboard-grid__item"
  :data-module-id="widget.id"
  :style="widgetStyle(widget)"
  :delay="index * 0.06"
  :while-hover="{ y: -2 }"
  :while-press="{ scale: 0.98 }"
>
  <component
    :is="registry[widget.id].component"
    v-bind="propsFor(widget.id)"
    v-on="listenersFor(widget.id)"
  />
</MotionWrapper>
```

## 4. Storybook 与测试

Storybook decorator 与组件必须共享同一策略。组件使用 `reducedMotion: 'user'`，全局 motion 配置也使用 `user`；不能让 decorator 强制 `always`，同时组件又声称跟随用户偏好。

测试只断言结构和终态，不依赖动画中间帧：

```js
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import MotionWrapper from './MotionWrapper.vue'

it('passes object motion props and attrs', () => {
  const wrapper = mount(MotionWrapper, {
    attrs: { class: 'item', 'data-module-id': 'knowledge' },
    props: { whileHover: { y: -2 }, whilePress: { scale: 0.98 } },
  })

  expect(wrapper.attributes('class')).toContain('item')
  expect(wrapper.attributes('data-module-id')).toBe('knowledge')
  expect(wrapper.vm.$props.whileHover).toEqual({ y: -2 })
})

it('renders the final state for reduced motion', async () => {
  const wrapper = mount(MotionWrapper, { props: { reducedMotion: 'always' } })
  await nextTick()
  expect(wrapper.attributes('data-motion-state')).toBe('final')
})
```

终态标记属于该示例契约的一部分，因此测试不依赖动画中间帧。Storybook 必须覆盖默认态和 reduced 态，a11y 检查必须确认动效没有增加语义内容。

## 5. 职责与护栏

| 范围 | 所属系统 | 规则 |
|---|---|---|
| Widget hover/press 和可选入场 | MotionWrapper | 只保留一个动效驱动；reduced 模式关闭手势 props |
| 模态框、抽屉和列表进出场 | Vue Transition / TransitionGroup | 不要再用 AnimatePresence 包裹同一元素 |
| 跨路由壳层转场 | 带能力探测的 View Transitions | `startViewTransition` 不存在时直接导航 |
| 首页编辑器拖拽 | 现有拖拽系统 | 正在拖拽的节点不增加 layout 动画 |

本 POC 的验收属于文档级验收：所有片段都使用对象绑定，说明媒体查询变化，测试针对终态，并且没有文字声称 motion-v 已安装或已实现。
