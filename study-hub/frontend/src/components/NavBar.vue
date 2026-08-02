<template>
  <nav class="mb-6 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-3">
    <router-link v-if="route.path !== '/'" to="/" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">
      ← 仪表盘
    </router-link>
    <h1 class="min-w-0 text-xl font-bold tracking-tight">{{ pageTitle }}</h1>
    <div class="flex min-w-0 max-w-full flex-wrap gap-x-3 gap-y-2 sm:ml-auto sm:justify-end">
      <router-link to="/kb" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">知识库</router-link>
      <router-link to="/wiki" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">Wiki</router-link>
      <router-link to="/learning" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">学习</router-link>
      <router-link to="/memory" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">记忆</router-link>
      <router-link to="/workflow" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">工作流</router-link>
      <router-link to="/ddl" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">DDL</router-link>
      <router-link to="/sop" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">SOP</router-link>
      <router-link to="/creator" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">创作</router-link>
      <router-link to="/skills" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">Skill</router-link>
      <router-link to="/journal" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">手账</router-link>
      <router-link to="/workbench" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">工作台</router-link>
      <router-link to="/settings" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">设置</router-link>
      <a href="/second-self/index.html" class="shrink-0 text-[13px] text-text-secondary transition-colors hover:text-accent">自我</a>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const titles = {
  '/': '学习中枢',
  '/kb': '知识库管理',
  '/wiki': 'Wiki 知识库',
  '/brainstorm': 'AI 头脑风暴',
  '/learning': '学习路线',
  '/learning-checklist': '学习清单',
  '/learning-plan': '学习计划',
  '/memory': '记忆系统',
  '/workflow': '工作流',
  '/ddl': 'DDL 面板',
  '/sop': 'SOP 规范化',
  '/creator': '新媒体创作中心',
  '/skills': 'Skill 市场',
  '/journal': '手账日记',
  '/workbench': '工作台',
  '/settings': '设置中心'
}
const pageTitle = computed(() => titles[route.path] || '学习中枢')
</script>
