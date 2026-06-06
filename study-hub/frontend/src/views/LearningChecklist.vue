<template>
  <div class="max-w-[960px]">
    <!-- Header -->
    <div class="bg-gradient-to-br from-[#5a6fd6] to-[#7c8aff] text-white p-7 rounded-[12px] mb-5">
      <h1 class="text-2xl mb-1.5">📋 学习清单</h1>
      <p class="opacity-90 text-sm">多计划切换 · 勾选追踪进度 · 笔记与链接 · 自动保存 · 搜索过滤</p>
    </div>

    <!-- Plan Tabs -->
    <div class="flex gap-2 flex-wrap mb-4 items-center">
      <button v-for="plan in allPlans" :key="plan.id"
        @click="switchPlan(plan.id)"
        class="px-3.5 py-1.5 rounded-[20px] border text-[13px] cursor-pointer transition-all flex items-center gap-1.5 whitespace-nowrap"
        :class="activePlanId === plan.id ? 'bg-accent border-accent text-white' : 'bg-surface border-border text-text-secondary hover:border-accent hover:text-text'">
        <span @dblclick.stop="editPlanName(plan.id)" title="双击编辑名称">{{ plan.name }}</span>
        <span v-if="allPlans.length > 1" @click.stop="deletePlan(plan.id)" class="w-4 h-4 rounded-full items-center justify-center cursor-pointer bg-white/20 hover:bg-danger text-[12px] hidden group-hover:flex">×</span>
      </button>
      <button @click="showAddRow = true" class="px-3 py-1.5 rounded-[20px] border border-dashed border-border text-text-secondary text-[13px] cursor-pointer hover:border-accent hover:text-accent transition-all">+ 新计划</button>
    </div>

    <!-- Add Plan Row -->
    <div v-if="showAddRow" class="flex gap-2 items-center mb-4">
      <input v-model="newPlanName" placeholder="输入计划名称…" maxlength="20" class="px-3 py-2 bg-surface border border-border rounded-[8px] text-text text-[13px] outline-none focus:border-accent max-w-[220px]">
      <button @click="confirmAddPlan" class="px-3.5 py-1.5 bg-accent text-white rounded-[8px] text-[12px] font-semibold hover:opacity-90">添加</button>
      <button @click="showAddRow = false" class="px-3.5 py-1.5 bg-surface border border-border text-text rounded-[8px] text-[12px] hover:bg-surface-hover">取消</button>
    </div>

    <!-- Toolbar -->
    <div class="flex gap-2 flex-wrap mb-4 items-center">
      <button @click="expandAll" class="px-4 py-2 rounded-[8px] text-sm font-semibold cursor-pointer border-none bg-accent text-white hover:opacity-90">📂 全部展开</button>
      <button @click="collapseAll" class="px-4 py-2 rounded-[8px] text-sm font-semibold cursor-pointer border-none bg-surface text-accent border border-border hover:bg-surface-hover">📁 全部折叠</button>
      <button @click="startReview" class="px-4 py-2 rounded-[8px] text-sm font-semibold cursor-pointer border-none bg-warn text-white hover:opacity-90 relative">
        🔄 今日复习
        <span v-if="dueReviewCount > 0" class="absolute -top-1 -right-1 bg-danger text-white text-[10px] px-1.5 py-0.5 rounded-full">{{ dueReviewCount }}</span>
      </button>
      <button @click="exportData" class="px-4 py-2 rounded-[8px] text-sm font-semibold cursor-pointer border-none bg-surface text-accent border border-border hover:bg-surface-hover">💾 导出进度</button>
      <button @click="importData" class="px-4 py-2 rounded-[8px] text-sm font-semibold cursor-pointer border-none bg-surface text-accent border border-border hover:bg-surface-hover">📥 恢复进度</button>
      <button @click="resetData" class="px-4 py-2 rounded-[8px] text-sm font-semibold cursor-pointer border-none bg-surface text-danger border border-danger hover:bg-danger/10">🔄 全部重置</button>
      <input v-model="searchQuery" @input="doSearch" placeholder="🔍 搜索知识点..." class="px-3.5 py-2 border border-border rounded-[8px] text-sm outline-none w-[220px] bg-surface text-text placeholder:text-text-secondary focus:border-accent">
    </div>

    <!-- Stats -->
    <div class="flex gap-3 flex-wrap mb-4">
      <div class="bg-surface p-3 rounded-[10px] border border-border flex-1 min-w-[100px] text-center">
        <div class="text-[1.8rem] font-bold text-accent">{{ activePlan?.topics?.length || 0 }}</div>
        <div class="text-[0.75rem] text-text-secondary mt-0.5">知识模块</div>
      </div>
      <div class="bg-surface p-3 rounded-[10px] border border-border flex-1 min-w-[100px] text-center">
        <div class="text-[1.8rem] font-bold text-accent">{{ totalItems }}</div>
        <div class="text-[0.75rem] text-text-secondary mt-0.5">总知识点</div>
      </div>
      <div class="bg-surface p-3 rounded-[10px] border border-border flex-1 min-w-[100px] text-center">
        <div class="text-[1.8rem] font-bold text-accent">{{ doneItems }}</div>
        <div class="text-[0.75rem] text-text-secondary mt-0.5">已完成</div>
      </div>
      <div class="bg-surface p-3 rounded-[10px] border border-border flex-1 min-w-[100px] text-center">
        <div class="text-[1.8rem] font-bold text-accent">{{ totalItems ? Math.round(doneItems/totalItems*100) : 0 }}%</div>
        <div class="text-[0.75rem] text-text-secondary mt-0.5">完成率</div>
      </div>
      <div class="bg-surface p-3 rounded-[10px] border border-border flex-1 min-w-[100px] text-center">
        <div class="text-[1.8rem] font-bold text-warn">{{ dueReviewCount }}</div>
        <div class="text-[0.75rem] text-text-secondary mt-0.5">今日待复习</div>
      </div>
    </div>

    <!-- Topics -->
    <div v-for="(topic, ti) in filteredTopics" :key="ti" class="bg-surface rounded-[12px] mb-3 overflow-hidden border border-border">
      <div class="px-[18px] py-3.5 cursor-pointer flex justify-between items-center select-none hover:bg-surface-hover transition-colors" @click="toggleSection(ti)">
        <h2 class="text-[0.95rem] text-[#b8b8d0] flex items-center gap-2">
          <span class="bg-accent text-white px-2 py-0.5 rounded-[12px] text-[0.7rem] font-semibold">#{{ topicStartNum(ti) }}-{{ topicEndNum(ti) }}</span>
          {{ topic.topic }}
        </h2>
        <div class="flex items-center gap-2.5">
          <span class="text-[0.78rem] text-[#999]">{{ topic.items.filter(i => i.done).length }}/{{ topic.items.length }}</span>
          <span class="text-[0.7rem] text-text-secondary transition-transform" :class="topic._collapsed ? '' : 'rotate-90'">▶</span>
        </div>
      </div>
      <div v-show="!topic._collapsed" class="px-[18px] pb-3.5">
        <template v-for="(item, ii) in topic.items" :key="ii">
          <div v-if="!item.hidden" class="flex items-start gap-2 py-[7px] px-1.5 border-b border-border last:border-b-0 hover:bg-surface-hover transition-colors rounded"
            :class="item.done ? 'opacity-60' : ''">
            <div class="text-accent font-bold text-[0.8rem] min-w-[28px] text-right pt-0.5">{{ globalIndex(ti, ii) + 1 }}</div>
            <div class="w-[18px] h-[18px] border-2 border-[#555] rounded cursor-pointer flex-shrink-0 mt-0.5 flex items-center justify-center transition-all hover:border-accent hover:bg-accent/10"
              :class="item.done ? 'bg-accent border-accent' : ''" @click="toggleItem(ti, ii)">
              <span v-if="item.done" class="text-white text-[12px] font-bold">✓</span>
            </div>
            <div class="flex-1 text-[0.88rem]" :class="item.done ? 'line-through text-[#555]' : ''">
              {{ item.text }}
              <span v-for="tg in item.tags" :key="tg" class="inline-block px-1.5 rounded-[8px] text-[0.68rem] font-semibold ml-1 align-[1px]"
                :class="tagClass(tg)">{{ tg }}</span>
            </div>
            <a v-if="item.link" :href="item.link" target="_blank" class="w-6 h-6 rounded border border-border flex items-center justify-center text-text-secondary text-[12px] hover:border-accent hover:text-accent transition-all flex-shrink-0">🔗</a>
            <div v-else class="w-6 h-6 rounded border border-border flex items-center justify-center text-text-secondary text-[12px] opacity-30 flex-shrink-0">🔗</div>
            <button @click="toggleNote(ti, ii)" class="w-6 h-6 rounded border border-border flex items-center justify-center text-text-secondary text-[12px] hover:border-accent hover:text-accent transition-all flex-shrink-0"
              :class="item.notes ? 'border-warn text-warn' : ''">
              {{ noteOpen[`${ti}-${ii}`] ? '▲' : '📝' }}
            </button>
          </div>
          <!-- Note Panel -->
          <div v-if="noteOpen[`${ti}-${ii}`] && !item.hidden" class="pl-[36px] pr-2 pb-2">
            <textarea v-model="item.notes" @input="save" placeholder="写点笔记…" class="w-full min-h-[50px] px-2 py-2 bg-surface border border-border rounded-[8px] text-text text-[12px] outline-none focus:border-accent resize-y"></textarea>
            <div class="flex gap-1.5 items-center mt-1">
              <input v-model="item.link" @input="save" placeholder="关联链接…" class="flex-1 px-2 py-1 bg-surface border border-border rounded-[8px] text-text text-[11px] outline-none focus:border-accent">
            </div>
          </div>
        </template>
      </div>
    </div>

    <div v-if="filteredTopics.length === 0" class="text-center py-12 text-text-secondary">
      <div class="text-[2.5rem] mb-2">📄</div>
      <p>没有数据</p>
    </div>

    <!-- 复习弹窗 -->
    <div v-if="showReviewModal" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center" @click.self="showReviewModal = false">
      <div class="bg-surface rounded-[16px] p-6 max-w-[500px] w-[90%] border border-border shadow-xl">
        <h3 class="text-lg font-bold mb-3 text-text">🔄 复习知识点</h3>
        <div class="bg-accent/5 rounded-[10px] p-4 mb-4 border border-accent/20">
          <p class="text-[0.95rem] text-text leading-relaxed">{{ reviewItem?.text }}</p>
          <div v-if="reviewItem?.notes" class="mt-2 text-[0.8rem] text-text-secondary bg-surface-hover rounded-[6px] p-2">
            📝 {{ reviewItem.notes }}
          </div>
        </div>
        <p class="text-sm text-text-secondary mb-4">你还记得这个知识点吗？</p>
        <div class="grid grid-cols-4 gap-2">
          <button @click="submitReview(Rating.Again)" class="py-2.5 rounded-[8px] text-sm font-semibold bg-danger/20 text-danger hover:bg-danger/30 transition-all">
            😵 忘记
            <div class="text-[10px] opacity-70 mt-0.5">&lt; 1m</div>
          </button>
          <button @click="submitReview(Rating.Hard)" class="py-2.5 rounded-[8px] text-sm font-semibold bg-warn/20 text-warn hover:bg-warn/30 transition-all">
            😐 困难
            <div class="text-[10px] opacity-70 mt-0.5">&lt; 6m</div>
          </button>
          <button @click="submitReview(Rating.Good)" class="py-2.5 rounded-[8px] text-sm font-semibold bg-accent/20 text-accent hover:bg-accent/30 transition-all">
            🙂 良好
            <div class="text-[10px] opacity-70 mt-0.5">&lt; 10m</div>
          </button>
          <button @click="submitReview(Rating.Easy)" class="py-2.5 rounded-[8px] text-sm font-semibold bg-success/20 text-success hover:bg-success/30 transition-all">
            😄 简单
            <div class="text-[10px] opacity-70 mt-0.5">&gt; 4d</div>
          </button>
        </div>
        <button @click="showReviewModal = false" class="mt-4 w-full py-2 rounded-[8px] text-sm text-text-secondary hover:bg-surface-hover transition-all">跳过</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useSettingsStore } from '../stores/settings.js'
import { createEmptyCard, Rating, fsrs } from 'ts-fsrs'

const settings = useSettingsStore()
const STORAGE_KEY = 'lc_data_v3'
const tagLabels = { '教程':'📺 学习教程', '概念':'💡 核心概念', '自查':'🔍 自我检查', '项目':'🛠 项目实战', '练习':'✏️ 动手练习', '复习':'🔄 复习回顾', 'AI':'🤖 AI 协作' }

// FSRS 复习系统
const f = fsrs()
const showReviewModal = ref(false)
const reviewItem = ref(null)
const reviewTopicIdx = ref(-1)
const reviewItemIdx = ref(-1)

const activePlanId = ref('plan_vibe')
const allPlans = ref([])
const searchQuery = ref('')
const showAddRow = ref(false)
const newPlanName = ref('')
const noteOpen = ref({})

const activePlan = computed(() => allPlans.value.find(p => p.id === activePlanId.value))

const totalItems = computed(() => activePlan.value?.topics?.reduce((sum, t) => sum + t.items.length, 0) || 0)
const doneItems = computed(() => activePlan.value?.topics?.reduce((sum, t) => sum + t.items.filter(i => i.done).length, 0) || 0)

const filteredTopics = computed(() => {
  if (!activePlan.value) return []
  const q = searchQuery.value.toLowerCase()
  return activePlan.value.topics.map(t => ({
    ...t,
    items: t.items.map(i => ({ ...i, hidden: q && !i.text.toLowerCase().includes(q) }))
  })).filter(t => t.items.some(i => !i.hidden))
})

function globalIndex(ti, ii) {
  let idx = 0
  for (let i = 0; i < ti; i++) idx += activePlan.value.topics[i].items.length
  return idx + ii
}
function topicStartNum(ti) {
  let idx = 1
  for (let i = 0; i < ti; i++) idx += activePlan.value.topics[i].items.length
  return idx
}
function topicEndNum(ti) { return topicStartNum(ti) + activePlan.value.topics[ti].items.length - 1 }

function tagClass(tg) {
  const map = {
    '教程': 'bg-[rgba(245,158,11,0.15)] text-[#f59e0b]',
    '概念': 'bg-[rgba(255,92,122,0.12)] text-[#ff7b93]',
    '自查': 'bg-[rgba(16,185,129,0.12)] text-[#10b981]',
    '项目': 'bg-[rgba(59,130,246,0.12)] text-[#60a5fa]',
    '练习': 'bg-[rgba(139,92,246,0.12)] text-[#a78bfa]',
    'AI': 'bg-[rgba(251,191,36,0.12)] text-[#fbbf24]',
    '复习': 'bg-[rgba(236,72,153,0.12)] text-[#f472b6]',
  }
  return map[tg] || 'bg-accent-glow text-accent'
}

function toggleItem(ti, ii) {
  const item = activePlan.value.topics[ti].items[ii]
  item.done = !item.done
  // 首次完成时初始化 FSRS 卡片
  if (item.done && !item.fsrs) {
    item.fsrs = createEmptyCard()
  }
  save()
}

// ========== FSRS 复习系统 ==========

const dueReviewCount = computed(() => {
  if (!activePlan.value) return 0
  const now = new Date()
  let count = 0
  for (const t of activePlan.value.topics) {
    for (const i of t.items) {
      if (i.done && i.fsrs && i.fsrs.due) {
        const due = new Date(i.fsrs.due)
        if (due <= now) count++
      }
    }
  }
  return count
})

function startReview() {
  if (!activePlan.value) return
  const now = new Date()
  for (let ti = 0; ti < activePlan.value.topics.length; ti++) {
    for (let ii = 0; ii < activePlan.value.topics[ti].items.length; ii++) {
      const item = activePlan.value.topics[ti].items[ii]
      if (item.done && item.fsrs && item.fsrs.due) {
        const due = new Date(item.fsrs.due)
        if (due <= now) {
          reviewItem.value = item
          reviewTopicIdx.value = ti
          reviewItemIdx.value = ii
          showReviewModal.value = true
          return
        }
      }
    }
  }
  alert('🎉 今日没有待复习的知识点！')
}

function submitReview(rating) {
  if (!reviewItem.value || !reviewItem.value.fsrs) return
  const card = reviewItem.value.fsrs
  const now = new Date()
  const scheduling = f.repeat(card, now)
  const nextCard = scheduling[rating].card
  reviewItem.value.fsrs = nextCard
  save()
  showReviewModal.value = false
  reviewItem.value = null
  // 继续下一个
  setTimeout(() => startReview(), 300)
}
function toggleSection(ti) {
  activePlan.value.topics[ti]._collapsed = !activePlan.value.topics[ti]._collapsed
  save()
}
function toggleNote(ti, ii) {
  const key = `${ti}-${ii}`
  noteOpen.value[key] = !noteOpen.value[key]
}
function expandAll() { activePlan.value.topics.forEach(t => t._collapsed = false); save() }
function collapseAll() { activePlan.value.topics.forEach(t => t._collapsed = true); save() }
function resetData() {
  if (!confirm(`确定要重置"${activePlan.value.name}"的所有勾选状态吗？`)) return
  activePlan.value.topics.forEach(t => { t.items.forEach(i => i.done = false); t._collapsed = false })
  save()
}
function switchPlan(id) { activePlanId.value = id; save(); searchQuery.value = '' }
function addPlan(name) {
  const id = 'plan_' + Date.now()
  allPlans.value.push({ id, name, topics: [] })
  activePlanId.value = id
  save()
}
function confirmAddPlan() {
  if (!newPlanName.value.trim()) return alert('请输入计划名称')
  addPlan(newPlanName.value.trim())
  newPlanName.value = ''
  showAddRow.value = false
}
function deletePlan(id) {
  if (allPlans.value.length <= 1) { alert('至少保留一个学习计划'); return }
  const plan = allPlans.value.find(p => p.id === id)
  if (!confirm(`确定删除计划"${plan.name}"？`)) return
  allPlans.value = allPlans.value.filter(p => p.id !== id)
  if (activePlanId.value === id) activePlanId.value = allPlans.value[0].id
  save()
}
function editPlanName(id) {
  const plan = allPlans.value.find(p => p.id === id)
  const name = prompt('修改计划名称：', plan.name)
  if (name && name.trim()) { plan.name = name.trim(); save() }
}
function exportData() {
  const blob = new Blob([JSON.stringify({ plans: allPlans.value, activeId: activePlanId.value, exportedAt: new Date().toISOString() }, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '学习进度_' + new Date().toISOString().slice(0, 10) + '.json'
  a.click()
}
function importData() {
  const inp = document.createElement('input')
  inp.type = 'file'; inp.accept = '.json'
  inp.onchange = e => {
    const f = e.target.files[0]; if (!f) return
    const r = new FileReader()
    r.onload = () => {
      try {
        const d = JSON.parse(r.result)
        if (d.plans && Object.keys(d.plans).length > 0) {
          allPlans.value = Object.values(d.plans)
          activePlanId.value = d.activeId || allPlans.value[0].id
        }
        save()
        alert('进度已恢复！')
      } catch { alert('文件解析失败') }
    }
    r.readAsText(f)
  }
  inp.click()
}
function doSearch() { /* reactive computed handles filtering */ }

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ plans: Object.fromEntries(allPlans.value.map(p => [p.id, p])), activeId: activePlanId.value }))
}

async function loadExternalPlans() {
  try {
    const files = await settings.apiGet('/learning/plans')
    for (const f of files) {
      if (!f.file) continue
      const planId = 'plan_md_' + f.id
      const checklistRes = await settings.apiGet(`/learning/checklist/${encodeURIComponent(f.file)}`)
      const fresh = checklistRes
      const existing = allPlans.value.find(p => p.id === planId)
      const merged = mergeExternalPlan(existing, fresh, planId)
      const idx = allPlans.value.findIndex(p => p.id === planId)
      if (idx >= 0) allPlans.value[idx] = merged
      else allPlans.value.push(merged)
    }
    save()
  } catch (e) { console.error('加载外部计划失败', e) }
}

function mergeExternalPlan(existing, fresh, id) {
  const existingMap = {}
  if (existing && existing.topics) {
    for (const t of existing.topics) {
      for (const i of t.items) existingMap[i.text] = i
    }
  }
  return {
    id, name: fresh.name || '学习计划',
    topics: (fresh.topics || []).map(t => ({
      topic: t.topic,
      items: (t.items || []).map(i => {
        const old = existingMap[i.t]
        return old ? { ...old } : { text: i.t, tags: i.tg ? [i.tg] : [], done: false, notes: '', link: '', fsrs: null }
      })
    }))
  }
}

onMounted(async () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      const d = JSON.parse(saved)
      if (d.plans && Object.keys(d.plans).length > 0) {
        allPlans.value = Object.values(d.plans)
        activePlanId.value = d.activeId || allPlans.value[0].id
      }
    } catch {}
  }
  if (!allPlans.value.length) {
    // Load default data from external
    await loadExternalPlans()
  }
  if (!allPlans.value.length) {
    allPlans.value = [{ id: 'plan_default', name: '默认计划', topics: [] }]
  }
})
</script>
