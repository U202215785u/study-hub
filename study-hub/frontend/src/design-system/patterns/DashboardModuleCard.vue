<template>
  <section class="dashboard-module-card" :data-state="state" :aria-label="title">
    <div v-if="state === 'loading'" class="dashboard-module-card__state">加载中...</div>
    <div v-else-if="state === 'error'" class="dashboard-module-card__state dashboard-module-card__state--error">{{ error }}</div>
    <div v-else-if="state === 'empty'" class="dashboard-module-card__state">{{ emptyText }}</div>
    <slot v-else />
  </section>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ title: { type: String, required: true }, loading: Boolean, error: { type: [String, Boolean], default: '' }, empty: Boolean, emptyText: { type: String, default: '暂无内容' } })
const state = computed(() => props.loading ? 'loading' : props.error ? 'error' : props.empty ? 'empty' : 'content')
</script>

<style scoped>
.dashboard-module-card { position: relative; width: 100%; height: 100%; min-width: 0; min-height: 0; box-sizing: border-box; overflow: hidden; border: 1px solid rgb(245 246 238 / 16%); border-radius: 22px; background: #1b1d1a; box-shadow: 0 18px 34px -8px rgb(0 0 0 / 22%); color: #f5f6ee; }
.dashboard-module-card__state { display: grid; height: 100%; min-height: 120px; place-items: center; color: #8b9186; font-size: 13px; }
.dashboard-module-card__state--error { color: #ff6b78; }
</style>
