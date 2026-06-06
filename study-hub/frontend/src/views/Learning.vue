<template>
  <div class="flex flex-col gap-6">
    <div v-if="loading" class="text-center py-10 text-text-secondary">加载中…</div>
    <div v-else-if="error" class="text-center py-10 text-text-secondary">加载失败，请稍后重试</div>
    <div v-else class="flex flex-col gap-4">
      <!-- 学习清单卡片 -->
      <router-link to="/learning-checklist" class="block bg-surface border border-border rounded-[12px] p-6 hover:border-accent hover:bg-surface-hover transition-all cursor-pointer relative">
        <div class="text-[28px] mb-2">📋</div>
        <div class="text-base font-semibold mb-1">全栈 Vibe Coding 学习清单</div>
        <div class="text-[13px] text-text-secondary leading-relaxed">213 个知识点，12 个模块，按 Phase 0~5 递进排列。勾选追踪进度，自动保存到浏览器，支持搜索、导入导出和 FSRS 智能复习。</div>
        <div class="flex gap-1.5 mt-2.5 flex-wrap">
          <span class="px-2 py-0.5 rounded-[10px] text-[11px] font-semibold bg-accent-glow text-accent">交互清单</span>
          <span class="px-2 py-0.5 rounded-[10px] text-[11px] font-semibold bg-accent-glow text-accent">进度追踪</span>
          <span class="px-2 py-0.5 rounded-[10px] text-[11px] font-semibold bg-accent-glow text-accent">FSRS 复习</span>
        </div>
        <!-- 复习提醒徽章 -->
        <div v-if="dueReviewCount > 0" class="absolute top-4 right-4 bg-danger text-white text-[11px] px-2.5 py-1 rounded-full font-semibold animate-pulse">
          {{ dueReviewCount }} 待复习
        </div>
      </router-link>

      <!-- 动态计划卡片 -->
      <router-link v-for="(plan, i) in plans" :key="plan.id"
        :to="`/learning-plan?plan=${encodeURIComponent(plan.id)}`"
        class="block bg-surface border border-border rounded-[12px] p-6 hover:border-accent hover:bg-surface-hover transition-all cursor-pointer">
        <div class="text-[28px] mb-2">{{ icons[i % icons.length] }}</div>
        <div class="text-base font-semibold mb-1">{{ plan.title }}</div>
        <div class="text-[13px] text-text-secondary leading-relaxed">{{ plan.desc || '学习计划' }}</div>
        <div class="flex gap-1.5 mt-2.5 flex-wrap">
          <span class="px-2 py-0.5 rounded-[10px] text-[11px] font-semibold bg-accent-glow text-accent">学习计划</span>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings.js'

const settings = useSettingsStore()
const plans = ref([])
const loading = ref(true)
const error = ref(false)
const icons = ['🗓️','🎯','📘','🚀','📕','🧠','🛠️','🎓','📖','💡']

// 计算今日待复习数量
const dueReviewCount = computed(() => {
  const saved = localStorage.getItem('lc_data_v3')
  if (!saved) return 0
  try {
    const d = JSON.parse(saved)
    const plans = Object.values(d.plans || {})
    const now = new Date()
    let count = 0
    for (const plan of plans) {
      for (const topic of plan.topics || []) {
        for (const item of topic.items || []) {
          if (item.done && item.fsrs && item.fsrs.due) {
            const due = new Date(item.fsrs.due)
            if (due <= now) count++
          }
        }
      }
    }
    return count
  } catch { return 0 }
})

onMounted(async () => {
  try {
    const data = await settings.apiGet('/learning/plans')
    plans.value = data
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>
