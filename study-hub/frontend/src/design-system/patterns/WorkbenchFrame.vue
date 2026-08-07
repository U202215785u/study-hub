<template>
  <div ref="viewport" class="workbench-viewport">
    <div class="workbench-frame" data-dashboard-stage :style="{ '--dashboard-stage-scale': scale }">
      <slot name="background" />
      <slot name="navigation" />
      <main class="workbench-frame__main">
        <slot name="greeting" />
        <slot />
      </main>
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const REFERENCE_WIDTH = 1440
const REFERENCE_HEIGHT = 980
const viewport = ref(null)
const scale = ref(1)
let observer

function fitStage() {
  const width = viewport.value?.clientWidth || window.innerWidth
  const height = viewport.value?.clientHeight || window.innerHeight
  if (!width || !height) return
  scale.value = Math.min(width / REFERENCE_WIDTH, height / REFERENCE_HEIGHT)
}

onMounted(() => {
  fitStage()
  if (typeof ResizeObserver !== 'undefined') {
    observer = new ResizeObserver(fitStage)
    observer.observe(viewport.value)
  } else {
    window.addEventListener('resize', fitStage)
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
  window.removeEventListener('resize', fitStage)
})
</script>

<style scoped>
.workbench-viewport {
  position: relative;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: #050604;
}
.workbench-frame {
  --dashboard-nav-height: 72px;
  --dashboard-greeting-height: 69px;
  --dashboard-grid-gap: 14.31px;
  position: absolute;
  top: 50%;
  left: 50%;
  width: 1440px;
  height: 980px;
  box-sizing: border-box;
  overflow: hidden;
  border: 1px solid rgb(245 246 238 / 12%);
  border-radius: 30px;
  background: #090a08;
  color: var(--ui-color-text-strong);
  transform: translate(-50%, -50%) scale(var(--dashboard-stage-scale));
  transform-origin: center;
}
.workbench-frame::before {
  position: absolute;
  top: -1px;
  left: -1px;
  width: 1440px;
  height: 128px;
  background: #242722;
  content: '';
  opacity: .55;
}
.workbench-frame__main {
  position: absolute;
  z-index: 10;
  top: 155px;
  left: 42px;
  width: 1356px;
}
.workbench-frame > :not(.bento-background):not(.workbench-frame__main) {
  z-index: 10;
}
@media (max-width: 767px) {
  .workbench-viewport { height: auto; min-height: 100dvh; overflow-x: hidden; overflow-y: auto; }
  .workbench-frame { position: relative; top: auto; left: auto; width: 100%; height: auto; min-height: 100dvh; overflow: visible; border: 0; border-radius: 0; transform: none !important; }
  .workbench-frame::before { width: 100%; height: 96px; }
  .workbench-frame__main { position: relative; top: auto; left: auto; width: auto; padding: 108px 16px 28px; }
}
</style>
