<template>
  <section class="dashboard-module-card" :data-state="state" :aria-label="title">
    <Transition name="card-state" mode="out-in">
      <div
        :key="state"
        data-card-state
        :class="[
          state === 'content' ? 'dashboard-module-card__content' : 'dashboard-module-card__state',
          { 'dashboard-module-card__state--error': state === 'error' },
        ]"
        :data-card-inset="state === 'content' ? '16' : undefined"
      >
        <slot v-if="state === 'content'" />
        <template v-else-if="state === 'loading'">加载中...</template>
        <template v-else-if="state === 'error'">{{ error }}</template>
        <template v-else>{{ emptyText }}</template>
      </div>
    </Transition>
  </section>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ title: { type: String, required: true }, loading: Boolean, error: { type: [String, Boolean], default: '' }, empty: Boolean, emptyText: { type: String, default: '暂无内容' } })
const state = computed(() => props.loading ? 'loading' : props.error ? 'error' : props.empty ? 'empty' : 'content')
</script>

<style scoped>
.dashboard-module-card { position: relative; width: 100%; height: 100%; min-width: 0; min-height: 0; box-sizing: border-box; overflow: hidden; border: 1px solid rgb(245 246 238 / 16%); border-radius: 22px; background: #1b1d1a; box-shadow: 0 18px 34px -8px rgb(0 0 0 / 22%); color: #f5f6ee; }
@supports (backdrop-filter: blur(1px)) {
  .dashboard-module-card {
    background: rgb(255 255 255 / 6%);
    -webkit-backdrop-filter: blur(12px) saturate(140%);
    backdrop-filter: blur(12px) saturate(140%);
  }
}
@media (prefers-reduced-transparency: reduce) {
  .dashboard-module-card {
    background: #1b1d1a;
    -webkit-backdrop-filter: none;
    backdrop-filter: none;
  }
}
.dashboard-module-card__content { width: 100%; height: 100%; min-width: 0; min-height: 0; box-sizing: border-box; padding: 16px; }
.dashboard-module-card__state { display: grid; height: 100%; min-height: 120px; box-sizing: border-box; place-items: center; padding: 16px; color: #8b9186; font-size: 13px; }
.dashboard-module-card__state--error { color: #ff6b78; }
@media (max-width: 767px) {
  .dashboard-module-card, .dashboard-module-card__content { height: auto; min-height: 0; }
}
.card-state-enter-active, .card-state-leave-active { transition: opacity var(--ui-duration-normal) var(--ui-ease-standard), transform var(--ui-duration-normal) var(--ui-ease-standard); }
.card-state-enter-from, .card-state-leave-to { opacity: 0; transform: translateY(6px); }
</style>
