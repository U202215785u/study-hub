<template>
  <nav class="flex items-center gap-4 mb-6">
    <router-link v-if="route.path !== '/'" to="/" class="text-[13px] text-text-secondary hover:text-accent transition-colors">
      ← 仪表盘
    </router-link>
    <h1 class="text-xl font-bold tracking-tight">{{ pageTitle }}</h1>
    <div class="ml-auto flex gap-3">
      <router-link to="/kb" class="text-[13px] text-text-secondary hover:text-accent transition-colors">知识库</router-link>
      <router-link to="/wiki" class="text-[13px] text-text-secondary hover:text-accent transition-colors">Wiki</router-link>
      <router-link to="/learning" class="text-[13px] text-text-secondary hover:text-accent transition-colors">学习</router-link>
      <router-link to="/workflow" class="text-[13px] text-text-secondary hover:text-accent transition-colors">工作流</router-link>
      <router-link to="/ddl" class="text-[13px] text-text-secondary hover:text-accent transition-colors">DDL</router-link>
      <router-link to="/sop" class="text-[13px] text-text-secondary hover:text-accent transition-colors">SOP</router-link>
      <router-link to="/creator" class="text-[13px] text-text-secondary hover:text-accent transition-colors">创作</router-link>
      <router-link to="/skills" class="text-[13px] text-text-secondary hover:text-accent transition-colors">Skill</router-link>
      <router-link to="/journal" class="text-[13px] text-text-secondary hover:text-accent transition-colors">手账</router-link>
      <a href="/second-self/index.html" class="text-[13px] text-text-secondary hover:text-accent transition-colors">自我</a>
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
  '/workflow': '工作流',
  '/ddl': 'DDL 面板',
  '/sop': 'SOP 规范化',
  '/creator': '新媒体创作中心',
  '/skills': 'Skill 市场',
  '/journal': '手账日记'
}
const pageTitle = computed(() => titles[route.path] || '学习中枢')
</script>
