import { createRouter, createWebHistory, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/Home.vue') },
  { path: '/kb', name: 'kb', component: () => import('../views/KnowledgeBase.vue') },
  { path: '/wiki', name: 'wiki', component: () => import('../views/Wiki.vue') },
  { path: '/wiki/:slug', name: 'wikiPage', component: () => import('../views/WikiPage.vue') },
  { path: '/brainstorm', name: 'brainstorm', component: () => import('../views/Brainstorm.vue') },
  { path: '/learning', name: 'learning', component: () => import('../views/Learning.vue') },
  { path: '/learning-checklist', name: 'checklist', component: () => import('../views/LearningChecklist.vue') },
  { path: '/learning-plan', name: 'learningPlan', component: () => import('../views/LearningPlan.vue') },
  { path: '/workflow', name: 'workflow', component: () => import('../views/Workflow.vue') },
  { path: '/ddl', name: 'ddl', component: () => import('../views/DDL.vue') },
  { path: '/sop', name: 'sop', component: () => import('../views/SOP.vue') },
  { path: '/creator', name: 'creator', component: () => import('../views/CreatorHub.vue') },
  { path: '/skills', name: 'skills', component: () => import('../views/SkillMarket.vue') },
  { path: '/journal', name: 'journal', component: () => import('../views/JournalView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

// Electron 环境使用 hash history (兼容 file:// 协议)
// 浏览器环境使用 web history (更干净的 URL)
const isElectron = !!(import.meta.env.VITE_ELECTRON) || !!(window.electronAPI)
const router = createRouter({
  history: isElectron ? createWebHashHistory() : createWebHistory(),
  routes
})

export default router
