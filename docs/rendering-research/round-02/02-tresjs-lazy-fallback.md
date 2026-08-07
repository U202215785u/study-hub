# Round 02 POC · WebGL 懒加载、降级与生命周期参考

> 文档角色：证据层 / POC。当前决策以 `../综合报告.md` 为准；默认不实施 WebGL。
> 独占工作包：W1-B WebGL。本文只定义未来 Phase 3 的接口和验证方式，不安装依赖、不修改业务代码。
> 研究对象：Vue 3.5、Vite 5、jsdom 25、Electron 28（静态兼容参考）。

## 1. 研究事实与验证级别

| 事实 | 记录 | 验证级别 |
|---|---|---|
| jsdom 未安装 canvas 时 `getContext()` 返回 `null` | WebGL 分支应自然进入 CSS fallback | 本机 jsdom 源码/行为读取 |
| three / TresJS / regl 的体积 | 原笔记记录了 bundlephobia 与 registry 查询数字 | 联网查询；不是本项目构建实测 |
| Electron 28 对应 Chromium 120 | 可用于 CSS/API 静态兼容判断 | 静态版本映射；没有 Electron 实机验收 |
| WebGL context 上限 | 不使用“8-16”作为项目保证值 | 浏览器/驱动相关经验，未作为硬事实 |

体积报告必须同时列出入口 chunk gzip、Home 首次打开的全部 JS 请求 gzip、启用模式新增异步 chunk gzip，以及 Electron `file://` 下 minified 字节数和解析耗时。懒加载只证明代码不在入口 chunk；保存的模式若在 Home 首次渲染时立即请求，仍属于首次加载成本。

## 2. 懒加载边界

首版建议只使用动态 import，不添加 `manualChunks`。父级必须持有 `resolvedMode`，并在加载失败时先切回 CSS，再让异步组件进入失败态：

```vue
<script setup>
import { defineAsyncComponent, ref } from 'vue'

const resolvedMode = ref('webgl')
const fallbackReason = ref(null)
const WebGLLayer = defineAsyncComponent({
  loader: () => import('./BentoWebGLLayer.vue'),
  loadingComponent: { template: '<div data-fallback="webgl-loading" aria-hidden="true" />' },
  errorComponent: { template: '<div data-fallback="webgl-load-error" aria-hidden="true" />' },
  onError(error, retry, fail, attempts) {
    if (attempts < 2) {
      retry()
      return
    }
    resolvedMode.value = 'css'
    fallbackReason.value = 'load-error'
    fail(error)
  },
})
</script>

<template>
  <div class="bento-background" :data-fallback-reason="fallbackReason || undefined">
    <WebGLLayer v-if="resolvedMode === 'webgl'" />
    <div
      v-else
      class="bento-background__fallback"
      data-fallback="css"
      aria-hidden="true"
    />
  </div>
</template>
```

loader 必须解析为组件，或使用明确的 error component。不能使用 `catch(() => undefined)`，因为 undefined 异步结果会生成空层并隐藏 fallback 原因。上面的 `onError` 在最后一次重试失败时执行 `resolvedMode.value = 'css'`，模板随即渲染可见的 CSS fallback。

## 3. 模式状态与能力注入

以下状态必须保持不同含义：

- `preferredMode`：用户选择（`css`、`particles`、`webgl` 或 `auto`），只有这个值持久化。
- `resolvedMode`：当前 renderer（`css`、`particles` 或 `webgl`），属于运行时状态。
- `fallbackReason`：稳定的降级原因，例如 `reduced-motion`、`unsupported`、`load-error`、`context-lost` 或 `budget`。

`auto` 只有用户明确启用动态背景时才有效。初始默认值和所有失败路径都必须是 CSS。

```js
import { ref } from 'vue'

export function detectWebgl(canvas = document.createElement('canvas')) {
  try {
    const context = canvas.getContext('webgl2') || canvas.getContext('webgl')
    if (!context) return false
    context.getExtension?.('WEBGL_lose_context')?.loseContext?.()
    return true
  } catch {
    return false
  }
}

export function useWebglSupport(detect = detectWebgl) {
  const supported = ref(null)
  const probe = () => {
    supported.value = Boolean(detect())
    return supported.value
  }

  return { supported, probe }
}
```

返回的 ref 必须可写，并且属于当前 composable 实例。测试和 Story 注入 `() => true` 或 `() => false`，不能共享模块级不可重置结果。如果探测创建临时 context，必须像上面一样释放；生产实现也可以直接在真实渲染 canvas 上探测，但必须把该 context 的所有权交给 renderer，不能再创建第二个 context。

## 4. 统一 renderer 生命周期

唯一接受的初始化契约如下。初始化器自己注册并持有 context、可见性和尺寸监听；`stop` 只暂停帧循环，恢复入口由 `webglcontextrestored` 和 `visibilitychange` 显式调用 `restart`：

```js
export function initBackground(canvas, gl, {
  slotRelease = () => {},
  onContextLost = () => {},
  onContextRestored = () => {},
} = {}) {
  let running = false
  let disposed = false
  let contextLost = false
  let frameId = 0
  let renderer = null
  const resizeObserver = new ResizeObserver(() => resize())
  const listeners = []

  function resize() {
    // 在这里调用 renderer.setSize(...) 和 renderer.setPixelRatio(...)
  }
  function tick() {
    if (!running || disposed) return
    frameId = requestAnimationFrame(tick)
    // 在这里调用 renderer.render(...)
  }
  function start() {
    if (disposed || running) return
    running = true
    tick()
  }
  function stop() {
    if (!running) return
    running = false
    cancelAnimationFrame(frameId)
  }
  function restart() {
    if (disposed || contextLost) return
    stop()
    start()
  }
  function handleContextLost(event) {
    event.preventDefault()
    contextLost = true
    stop()
    onContextLost()
  }
  function handleContextRestored() {
    if (disposed) return
    contextLost = false
    onContextRestored({ restart })
  }
  function handleVisibilityChange() {
    if (document.hidden) stop()
    else restart()
  }

  listeners.push(
    [canvas, 'webglcontextlost', handleContextLost],
    [canvas, 'webglcontextrestored', handleContextRestored],
    [document, 'visibilitychange', handleVisibilityChange],
  )
  for (const [target, type, handler] of listeners) target.addEventListener(type, handler)

  function dispose() {
    if (disposed) return
    disposed = true
    stop()
    // 先移除监听，再主动释放 context，避免 loseContext 再触发 lost 回调。
    for (const [target, type, handler] of listeners) target.removeEventListener(type, handler)
    resizeObserver.disconnect()
    renderer?.dispose?.()
    gl.getExtension?.('WEBGL_lose_context')?.loseContext?.()
    slotRelease()
  }

  resizeObserver.observe(canvas.parentElement)
  start()
  return { get renderer() { return renderer }, resize, stop, dispose }
}
```

真实 renderer 在返回前赋给 `renderer`；调用方始终使用同一层级的对象。context 恢复时只有明确的回调决定是否调用 `restart`，不会因浏览器事件自动重建场景：

```js
const lifecycle = initBackground(canvas, gl, {
  slotRelease: () => releaseWebglSlot('background'),
  onContextLost: () => setCssFallback('context-lost'),
  onContextRestored: ({ restart }) => {
    if (shouldRecoverWebgl()) restart()
  },
})
onBeforeUnmount(() => lifecycle.dispose())
```

初始化器拥有 `ResizeObserver` 和全部外部监听；调用方只接入返回的生命周期。调用方不能写 `const { dispose } = ...; dispose.renderer` 或解构不存在的嵌套对象。`dispose` 负责停止帧循环、移除监听、断开 `ResizeObserver`、释放 renderer 资源和归还 slot。

## 5. context lost 与恢复

context lost 路径立即停止帧循环、调用 `preventDefault()`、设置 CSS fallback，并且不会静默重建 renderer。独立的明确恢复动作最多重试三次；`restart` 只负责重新开始现有循环，不负责绕过恢复上限：

```js
let recoveryAttempts = 0

function handleContextLost() {
  setCssFallback('context-lost')
}

function handleContextRestored({ restart }) {
  if (recoveryAttempts >= 3) return setCssFallback('context-lost-limit')
  recoveryAttempts += 1
  if (!shouldRecoverWebgl()) return setCssFallback('recovery-declined')
  clearCssFallback()
  restart()
}

const lifecycle = initBackground(canvas, gl, {
  onContextLost: handleContextLost,
  onContextRestored: handleContextRestored,
})
```

`visibilitychange` 可以在不销毁 context 的情况下暂停并恢复帧循环。reduced-motion、能力不足、加载失败和预算驱逐都直接使用 CSS fallback，不尝试恢复 WebGL。

## 6. WebGL 预算与真实驱逐

项目目标是最多两个活跃 context，硬上限为三个。这是项目门禁，不是浏览器保证。预算驱逐时必须先通知真实 renderer 停止并释放，再删除记录；正常释放只删除自己的记录，不能调用驱逐回调。

```js
const slots = new Map()

export function acquireWebglSlot(id, { priority = 1, onEvict = () => {}, max = 3 } = {}) {
  if (slots.has(id)) return () => releaseWebglSlot(id)
  if (slots.size >= max) {
    const victim = [...slots.values()]
      .filter((slot) => slot.priority < priority)
      .sort((a, b) => a.lastUsed - b.lastUsed)[0]
    if (!victim) return null
    slots.delete(victim.id)
    victim.onEvict()
  }

  slots.set(id, { id, priority, lastUsed: Date.now(), onEvict })
  return () => releaseWebglSlot(id)
}

export function releaseWebglSlot(id) {
  return slots.delete(id)
}
```

驱逐时先删除记录，再调用 `onEvict`，因此 `onEvict -> dispose -> releaseWebglSlot` 不会递归。父组件正常卸载时只调用 `releaseWebglSlot`，不会触发 `onEvict`。背景 slot 优先级最高，但父组件卸载时仍必须释放自身。测试必须 spy `onEvict`、`stop`、`dispose` 和 context-loss 通知；只检查 `slots.size` 不够。

## 7. 验收证据

- jsdom 测试：注入 `() => false` 时渲染 `data-fallback="webgl-unavailable"` 且没有 canvas；不同测试之间没有模块级探测状态泄漏。
- 生命周期测试：`initBackground` 返回 `renderer`、`resize`、`stop`、`dispose`；`dispose` 取消帧、断开 observer、移除监听并归还 slot。
- context 测试：可取消的 `webglcontextlost` 事件被阻止，帧循环停止，CSS fallback 可见，明确恢复重试不超过三次；可见性恢复会进入 `restart`。
- 构建测试：分别报告四项体积数字，并确认哪些请求发生在 Home 首次渲染期间。
- Electron 结果：目标机器实测完成前，只标记为静态兼容。
