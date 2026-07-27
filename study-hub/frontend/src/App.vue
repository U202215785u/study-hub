<template>
  <div class="min-h-screen bg-bg text-text">
    <!-- 全屏布局页面（Wiki / 知识库） -->
    <template v-if="isFullScreenRoute">
      <router-view />
    </template>
    <!-- 其他页面常规布局 -->
    <div v-else class="mx-auto max-w-5xl px-5 py-10 pb-20">
      <NavBar />
      <router-view />
      <SystemStatus />
    </div>
    <!-- 全局反馈组件 -->
    <AppToast />
    <AppConfirm />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import SystemStatus from './components/SystemStatus.vue'
import AppToast from './components/AppToast.vue'
import AppConfirm from './components/AppConfirm.vue'

const route = useRoute()
const isFullScreenRoute = computed(() =>
  route.path.startsWith('/wiki') || route.path.startsWith('/kb')
)
</script>
