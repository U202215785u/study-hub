<template>
  <main class="min-w-0 w-full">
    <header class="min-w-0 border-b border-border pb-5">
      <div class="flex min-w-0 flex-wrap items-start justify-between gap-4">
        <div class="min-w-0">
          <p class="text-[11px] uppercase tracking-[0.16em] text-text-secondary">Study-Hub</p>
          <h2 class="mt-1 truncate text-2xl font-semibold tracking-tight">工作台</h2>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-text-secondary">
            将常用的学习、知识和自动化入口集中在一个可扩展的工作区。
          </p>
        </div>
        <span class="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs text-accent">
          {{ activeModule.label }}
        </span>
      </div>
    </header>

    <div class="mt-6 lg:grid lg:grid-cols-[13rem_minmax(0,1fr)] lg:gap-6">
      <aside class="hidden min-w-0 lg:flex lg:flex-col lg:gap-2" aria-label="工作台模块">
        <p class="px-3 text-[11px] font-medium uppercase tracking-[0.14em] text-text-secondary">模块</p>
        <button
          v-for="module in modules"
          :key="module.id"
          type="button"
          class="flex min-w-0 items-center gap-3 rounded-[8px] border px-3 py-2.5 text-left text-sm transition-colors"
          :class="module.id === activeTab
            ? 'border-accent bg-accent/10 text-text'
            : 'border-transparent text-text-secondary hover:border-border hover:bg-surface hover:text-text'"
          :aria-current="module.id === activeTab ? 'page' : undefined"
          @click="selectModule(module.id)"
        >
          <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] bg-surface text-xs text-accent">
            {{ module.index }}
          </span>
          <span class="min-w-0 truncate">{{ module.label }}</span>
        </button>
      </aside>

      <div class="min-w-0">
        <div class="space-y-3 lg:hidden">
          <label class="block text-xs font-medium text-text-secondary" for="workbench-module">当前模块</label>
          <select
            id="workbench-module"
            class="w-full min-w-0 rounded-[8px] border border-border bg-surface px-3 py-2.5 text-sm text-text outline-none focus:border-accent"
            :value="activeTab"
            @change="selectModule($event.target.value)"
          >
            <option v-for="module in modules" :key="module.id" :value="module.id">{{ module.label }}</option>
          </select>
          <nav class="flex min-w-0 gap-2 overflow-x-auto pb-1" aria-label="工作台模块标签">
            <button
              v-for="module in modules"
              :key="`mobile-${module.id}`"
              type="button"
              class="shrink-0 rounded-full border px-3 py-1.5 text-xs transition-colors"
              :class="module.id === activeTab
                ? 'border-accent bg-accent text-white'
                : 'border-border bg-surface text-text-secondary hover:text-text'"
              :aria-current="module.id === activeTab ? 'page' : undefined"
              @click="selectModule(module.id)"
            >
              {{ module.label }}
            </button>
          </nav>
        </div>

        <section class="mt-5 min-w-0 overflow-hidden rounded-[12px] border border-border bg-surface lg:mt-0">
          <div class="border-b border-border px-4 py-4 sm:px-5">
            <p class="text-xs font-medium text-accent">{{ activeModule.index }} / {{ modules.length }}</p>
            <h3 class="mt-1 text-lg font-semibold">{{ activeModule.label }}</h3>
            <p class="mt-1 text-sm text-text-secondary">{{ activeModule.description }}</p>
          </div>

          <div class="min-w-0 p-4 sm:p-5">
            <component
              :is="activeModule.component"
              @navigate="handleModuleNavigation"
            />
          </div>
        </section>
      </div>
    </div>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ApprovalsPanel from './workbench/ApprovalsPanel.vue'
import CasesPanel from './workbench/CasesPanel.vue'
import EnvironmentPanel from './workbench/EnvironmentPanel.vue'
import OverviewPanel from './workbench/OverviewPanel.vue'
import RoadmapPanel from './workbench/RoadmapPanel.vue'
import VersionsPanel from './workbench/VersionsPanel.vue'

const route = useRoute()
const router = useRouter()

const modules = [
  { id: 'overview', index: '01', label: '总览', description: '查看工作台入口与近期状态。', component: OverviewPanel },
  { id: 'tasks', index: '02', label: '案件', description: '只读查看案件事实、审查与验证记录。', component: CasesPanel },
  { id: 'approvals', index: '03', label: '审批', description: '处理需要确认后才能继续的工作台操作。', component: ApprovalsPanel },
  { id: 'versions', index: '04', label: '版本', description: '查看正式版本、测试版本与发布审批条件。', component: VersionsPanel },
  { id: 'environment', index: '05', label: '环境', description: '查看脱敏运行环境与健康检查结果。', component: EnvironmentPanel },
  { id: 'roadmap', index: '06', label: '规划', description: '查看项目规划来源、时间和 Markdown 内容。', component: RoadmapPanel },
]

const moduleIds = new Set(modules.map((module) => module.id))

const activeTab = computed(() => {
  const tab = Array.isArray(route.query.tab) ? route.query.tab[0] : route.query.tab
  return moduleIds.has(tab) ? tab : 'overview'
})

const activeModule = computed(() => modules.find((module) => module.id === activeTab.value) || modules[0])

function selectModule(tab) {
  if (!moduleIds.has(tab) || tab === activeTab.value) return
  router.push({
    name: 'workbench',
    query: { ...route.query, tab },
  })
}

function handleModuleNavigation({ module } = {}) {
  if (moduleIds.has(module)) selectModule(module)
}
</script>
