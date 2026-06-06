<template>
  <div class="flex flex-col gap-6">
    <!-- 标题区 -->
    <div class="text-center mb-1">
      <h1 class="text-[22px] font-bold tracking-tight">🧩 Skill 市场</h1>
      <p class="text-xs text-text-secondary mt-1">
        浏览社区 Skill，一键安装到本地
        <span v-if="syncStats.total">· 已收录 {{ syncStats.total }} 个</span>
      </p>
    </div>

    <!-- 标签页 -->
    <div class="flex gap-1 bg-bg border border-border rounded-[10px] p-1 w-fit">
      <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
        class="px-4 py-1.5 rounded-[8px] text-sm transition-all"
        :class="activeTab === tab.id ? 'bg-accent text-white' : 'text-text-secondary hover:text-text'">
        {{ tab.name }}
        <span v-if="tab.id === 'installed' && localSkills.length" class="text-[11px] ml-1 opacity-80">
          {{ localSkills.length }}
        </span>
      </button>
    </div>

    <!-- 发现页：搜索 + 筛选 -->
    <template v-if="activeTab === 'discover'">
      <div class="flex gap-3 flex-wrap">
        <input v-model="searchQuery" @keydown.enter="doSearch" placeholder="搜索 Skill…"
          class="flex-1 min-w-[200px] px-3.5 py-2.5 bg-surface border border-border rounded-[10px] text-text text-sm outline-none focus:border-accent">
        <select v-model="selectedCategory" @change="doSearch"
          class="px-3 py-2.5 bg-surface border border-border rounded-[10px] text-text text-sm outline-none cursor-pointer focus:border-accent">
          <option value="">全部分类</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        <button @click="syncSkills" :disabled="syncing"
          class="px-4 py-2.5 rounded-[10px] border border-border bg-surface text-text text-sm hover:bg-surface-hover hover:border-accent disabled:opacity-50">
          {{ syncing ? '同步中…' : '🔄 同步' }}
        </button>
      </div>

      <!-- 同步状态提示 -->
      <div v-if="syncStats.last_sync && syncStats.last_sync !== '从未同步'" class="text-[11px] text-text-secondary">
        上次同步：{{ syncStats.last_sync }}
      </div>
      <div v-else-if="!syncStats.total" class="bg-surface border border-border rounded-[12px] p-6 text-center">
        <div class="text-text-secondary text-sm mb-3">暂无 Skill 数据，请先点击「同步」从社区获取</div>
        <button @click="syncSkills" :disabled="syncing"
          class="px-5 py-2.5 rounded-[10px] bg-accent text-white text-sm hover:opacity-90 disabled:opacity-50">
          {{ syncing ? '同步中…' : '立即同步' }}
        </button>
      </div>

      <!-- Skill 列表 -->
      <div v-if="communitySkills.length" class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div v-for="skill in communitySkills" :key="skill.id"
          class="bg-surface border border-border rounded-[12px] p-4 flex flex-col gap-2 transition-all hover:border-accent">
          <div class="flex items-start gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-semibold text-sm truncate">{{ skill.display_name }}</span>
                <span v-if="skill.installed" class="text-[10px] px-1.5 py-0.5 rounded-full bg-green-500/15 text-green-400">已安装</span>
              </div>
              <div class="text-[11px] text-text-secondary mt-0.5">{{ skill.author_name }} · {{ skill.license || '未知许可' }}</div>
            </div>
            <div class="flex items-center gap-1 text-[12px] text-text-secondary flex-shrink-0">
              <span>⭐</span>
              <span>{{ formatStars(skill.stars) }}</span>
            </div>
          </div>
          <div class="text-[12px] text-text-secondary line-clamp-2">{{ skill.description }}</div>
          <div class="flex items-center gap-2 mt-1">
            <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-accent/10 text-accent">{{ skill.category }}</span>
            <span v-if="skill.sub_category" class="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-hover text-text-secondary">{{ skill.sub_category }}</span>
            <div class="ml-auto flex gap-2">
              <a :href="skill.primary_link" target="_blank" rel="noopener noreferrer"
                class="text-[11px] px-2.5 py-1 rounded-[6px] border border-border bg-bg text-text-secondary hover:border-accent transition-colors no-underline">
                GitHub →
              </a>
              <button v-if="!skill.installed" @click="installSkill(skill)"
                class="text-[11px] px-2.5 py-1 rounded-[6px] bg-accent text-white hover:opacity-90">
                安装
              </button>
              <button v-else disabled
                class="text-[11px] px-2.5 py-1 rounded-[6px] border border-green-500/30 text-green-400 opacity-60">
                已装
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="communitySkills.length && hasMore" class="text-center">
        <button @click="loadMore" :disabled="loading"
          class="px-5 py-2 rounded-[10px] border border-border bg-surface text-text text-sm hover:bg-surface-hover disabled:opacity-50">
          {{ loading ? '加载中…' : '加载更多' }}
        </button>
      </div>
    </template>

    <!-- 已安装页 -->
    <template v-if="activeTab === 'installed'">
      <div class="flex gap-2">
        <button @click="scanLocal" :disabled="scanning"
          class="px-4 py-2 rounded-[10px] border border-border bg-surface text-text text-sm hover:bg-surface-hover disabled:opacity-50">
          {{ scanning ? '扫描中…' : '🔄 重新扫描' }}
        </button>
      </div>

      <div v-if="localSkills.length" class="flex flex-col gap-2">
        <div v-for="skill in localSkills" :key="skill.id"
          class="bg-surface border border-border rounded-[12px] p-4 flex items-center gap-3 transition-all hover:border-accent">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="font-semibold text-sm">{{ skill.display_name || skill.name }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="skill.enabled ? 'bg-green-500/15 text-green-400' : 'bg-border text-text-secondary'">
                {{ skill.enabled ? '启用' : '禁用' }}
              </span>
              <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-accent/10 text-accent">{{ skill.source }}</span>
            </div>
            <div class="text-[11px] text-text-secondary mt-0.5">{{ skill.install_path }}</div>
          </div>
          <div class="flex gap-2">
            <button @click="toggleSkill(skill)"
              class="text-[11px] px-2.5 py-1 rounded-[6px] border border-border bg-bg hover:border-accent transition-colors">
              {{ skill.enabled ? '禁用' : '启用' }}
            </button>
            <button @click="uninstallSkill(skill)"
              class="text-[11px] px-2.5 py-1 rounded-[6px] border border-danger text-danger hover:bg-danger hover:text-white transition-colors">
              卸载
            </button>
          </div>
        </div>
      </div>
      <div v-else class="bg-surface border border-border rounded-[12px] p-8 text-center text-text-secondary text-sm">
        暂无本地 Skill，前往「发现」页安装
      </div>
    </template>

    <!-- 收藏页 -->
    <template v-if="activeTab === 'favorites'">
      <div class="bg-surface border border-border rounded-[12px] p-8 text-center text-text-secondary text-sm">
        收藏功能开发中…
      </div>
    </template>

    <!-- Toast -->
    <div v-if="toastVisible" class="fixed bottom-6 left-1/2 -translate-x-1/2 px-5 py-2.5 rounded-[8px] text-sm border z-[200] transition-opacity"
      :class="toastError ? 'border-danger text-danger' : 'border-border text-text bg-surface'">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings.js'

const settings = useSettingsStore()

// ===== 标签页 =====
const tabs = [
  { id: 'discover', name: '发现' },
  { id: 'installed', name: '已安装' },
  { id: 'favorites', name: '收藏' },
]
const activeTab = ref('discover')

// ===== 发现页状态 =====
const searchQuery = ref('')
const selectedCategory = ref('')
const categories = ref([])
const communitySkills = ref([])
const syncStats = ref({ total: 0, last_sync: '' })
const syncing = ref(false)
const loading = ref(false)
const hasMore = ref(true)
const offset = ref(0)
const LIMIT = 50

// ===== 已安装页状态 =====
const localSkills = ref([])
const scanning = ref(false)

// ===== Toast =====
const toastVisible = ref(false)
const toastMessage = ref('')
const toastError = ref(false)
let toastTimer = null

function showToast(msg, isError = false) {
  toastMessage.value = msg
  toastError.value = isError
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2500)
}

// ===== 格式化 =====
function formatStars(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toString()
}

// ===== API 调用 =====
async function doSearch() {
  loading.value = true
  offset.value = 0
  try {
    const params = new URLSearchParams()
    params.append('limit', LIMIT)
    params.append('offset', 0)
    if (searchQuery.value) params.append('search', searchQuery.value)
    if (selectedCategory.value) params.append('category', selectedCategory.value)
    params.append('sort', 'stars')

    const data = await settings.apiGet(`/skills/community?${params}`)
    communitySkills.value = data || []
    hasMore.value = (data || []).length >= LIMIT
  } catch (e) {
    showToast('获取 Skill 列表失败', true)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  offset.value += LIMIT
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('limit', LIMIT)
    params.append('offset', offset.value)
    if (searchQuery.value) params.append('search', searchQuery.value)
    if (selectedCategory.value) params.append('category', selectedCategory.value)
    params.append('sort', 'stars')

    const data = await settings.apiGet(`/skills/community?${params}`)
    const newItems = data || []
    communitySkills.value.push(...newItems)
    hasMore.value = newItems.length >= LIMIT
  } catch (e) {
    showToast('加载更多失败', true)
  } finally {
    loading.value = false
  }
}

async function syncSkills() {
  syncing.value = true
  try {
    const result = await settings.apiPost('/skills/community/sync')
    if (result.success) {
      showToast(`同步成功！新增 ${result.added} 个，更新 ${result.updated} 个`)
      await loadStats()
      await loadCategories()
      await doSearch()
    } else {
      showToast(result.error || '同步失败', true)
    }
  } catch (e) {
    showToast('同步请求失败', true)
  } finally {
    syncing.value = false
  }
}

async function loadStats() {
  try {
    syncStats.value = await settings.apiGet('/skills/community/stats')
  } catch { /* ignore */ }
}

async function loadCategories() {
  try {
    categories.value = await settings.apiGet('/skills/community/categories')
  } catch { categories.value = [] }
}

async function installSkill(skill) {
  try {
    const result = await settings.apiPost('/skills/local/install', {
      skill_id: skill.id,
      install_type: 'light'
    })
    if (result.success) {
      showToast(result.message || '安装成功')
      skill.installed = true
    } else {
      showToast(result.error || '安装失败', true)
    }
  } catch (e) {
    showToast('安装请求失败', true)
  }
}

// ===== 本地 Skill =====
async function loadLocalSkills() {
  try {
    localSkills.value = await settings.apiGet('/skills/local')
  } catch {
    localSkills.value = []
  }
}

async function scanLocal() {
  scanning.value = true
  try {
    await settings.apiPost('/skills/local/scan')
    await loadLocalSkills()
    showToast('扫描完成')
  } catch (e) {
    showToast('扫描失败', true)
  } finally {
    scanning.value = false
  }
}

async function toggleSkill(skill) {
  try {
    const result = await settings.apiPost(`/skills/local/${skill.id}/toggle`, {
      enabled: !skill.enabled
    })
    if (result.success) {
      skill.enabled = result.enabled
      showToast(result.enabled ? '已启用' : '已禁用')
    } else {
      showToast(result.error || '操作失败', true)
    }
  } catch (e) {
    showToast('操作失败', true)
  }
}

async function uninstallSkill(skill) {
  if (!confirm(`确定要卸载「${skill.display_name || skill.name}」吗？`)) return
  try {
    const result = await settings.apiDelete(`/skills/local/${skill.id}`)
    if (result.success) {
      localSkills.value = localSkills.value.filter(s => s.id !== skill.id)
      showToast('卸载成功')
    } else {
      showToast(result.error || '卸载失败', true)
    }
  } catch (e) {
    showToast('卸载请求失败', true)
  }
}

// ===== 初始化 =====
onMounted(async () => {
  await loadStats()
  await loadCategories()
  await doSearch()
  await loadLocalSkills()
})
</script>
