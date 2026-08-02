<template>
  <section class="greeting-bar" data-visual-anchor="greeting" aria-labelledby="greeting-title">
    <div>
      <h1 id="greeting-title">{{ greeting }}, 章</h1>
      <p>队列、DDL、知识库和创作入口都在这里汇总。优先处理卡片中的异常和今日任务。</p>
    </div>
    <div class="greeting-bar__time"><strong>{{ dateLabel }} {{ timeLabel }}</strong><span>天气：晴朗</span></div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'

const now = ref(new Date())
const timer = setInterval(() => { now.value = new Date() }, 30_000)
onBeforeUnmount(() => clearInterval(timer))
const greeting = computed(() => now.value.getHours() < 12 ? '早上好' : now.value.getHours() < 18 ? '下午好' : '晚上好')
const dateLabel = computed(() => `${now.value.getMonth() + 1}月${now.value.getDate()}日`)
const timeLabel = computed(() => now.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }))
</script>

<style scoped>
.greeting-bar { display: flex; min-height: 69px; box-sizing: border-box; align-items: flex-start; justify-content: space-between; gap: 24px; }
.greeting-bar h1 { margin: 0; color: #f5f6ee; font-size: 30px; line-height: 1.15; }
.greeting-bar p { margin: 10px 0 0; color: #8b9186; font-size: 13px; }
.greeting-bar__time { display: grid; justify-items: end; gap: 9px; padding-top: 3px; }
.greeting-bar__time strong { color: #f5f6ee; font-size: 28px; line-height: 1; }
.greeting-bar__time span { color: #8b9186; font-size: 12px; }
</style>
