<template>
  <div class="flex h-[calc(100vh-64px)] overflow-hidden">
    <!-- 左侧：日历 + 时光轴 -->
    <aside class="w-[240px] min-w-[240px] bg-surface border-r border-border flex flex-col overflow-hidden">
      <!-- 头部 -->
      <div class="px-4 py-3 border-b border-border flex items-center justify-between">
        <h2 class="text-base font-bold" style="font-family: 'TsangerJinKai02', serif;">📔 陪自己度过漫长岁月</h2>
        <router-link to="/" class="text-[13px] text-text-secondary hover:text-accent transition-colors no-underline">
          ←
        </router-link>
      </div>

      <!-- 统计 -->
      <div class="px-4 py-3 border-b border-border">
        <div class="grid grid-cols-2 gap-2">
          <div class="text-center">
            <div class="text-[11px] text-text-secondary">已记录</div>
            <div class="text-lg font-bold text-accent">{{ stats.total }}<span class="text-xs font-normal text-text-secondary">天</span></div>
          </div>
          <div class="text-center">
            <div class="text-[11px] text-text-secondary">连续</div>
            <div class="text-lg font-bold text-[#f0a060]">{{ stats.streak }}<span class="text-xs font-normal text-text-secondary">天</span></div>
          </div>
        </div>
      </div>

      <!-- 年月选择 -->
      <div class="px-4 py-2 flex items-center justify-between border-b border-border">
        <button @click="prevMonth" class="text-text-secondary hover:text-accent transition-colors text-lg">‹</button>
        <span class="text-sm font-medium">{{ currentYear }} . {{ String(currentMonth).padStart(2,'0') }}</span>
        <button @click="nextMonth" class="text-text-secondary hover:text-accent transition-colors text-lg">›</button>
      </div>

      <!-- 日历 -->
      <div class="px-3 py-2">
        <div class="grid grid-cols-7 gap-0 text-center text-[10px] text-text-secondary mb-1">
          <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
        </div>
        <div class="grid grid-cols-7 gap-0">
          <div
            v-for="d in calendarDays"
            :key="d.date"
            @click="selectDate(d.date)"
            :class="[
              'aspect-square flex items-center justify-center cursor-pointer text-[12px] transition-all relative rounded-full mx-0.5',
              d.isCurrentMonth ? 'text-text' : 'text-text-secondary/30',
              d.date === selectedDate ? 'bg-accent text-white' : 'hover:bg-surface-hover',
              d.hasEntry && d.date !== selectedDate ? 'font-bold' : ''
            ]"
          >
            <span>{{ d.day }}</span>
            <span v-if="d.hasEntry && d.date !== selectedDate" class="absolute bottom-0.5 w-1 h-1 rounded-full bg-accent"></span>
          </div>
        </div>
      </div>

      <!-- 时光轴 -->
      <div class="flex-1 overflow-y-auto px-3 py-2">
        <div class="text-[10px] text-text-secondary uppercase tracking-[2px] mb-2 px-1">时光轴</div>
        <div v-if="filteredEntries.length === 0" class="text-center py-4 text-text-secondary text-xs">
          这个月还没有写字
        </div>
        <div class="relative">
          <div class="absolute left-[7px] top-1 bottom-1 w-[1px] bg-border"></div>
          <div
            v-for="entry in filteredEntries.slice(0, 15)"
            :key="entry.id"
            @click="loadEntry(entry)"
            :class="[
              'relative pl-5 py-1.5 cursor-pointer transition-colors rounded-[6px] mb-0.5',
              selectedEntryId === entry.id ? 'bg-accent-glow' : 'hover:bg-white/[0.02]'
            ]"
          >
            <div class="absolute left-[4px] top-[9px] w-[7px] h-[7px] rounded-full border border-border z-10"
              :class="selectedEntryId === entry.id ? 'bg-accent border-accent' : 'bg-surface'"></div>
            <div class="flex items-center gap-1.5">
              <span class="text-[11px] text-text-secondary">{{ formatDay(entry.date) }}</span>
              <span class="text-sm">{{ moodEmoji(entry.mood) }}</span>
            </div>
            <p class="text-[11px] text-text-secondary line-clamp-1 mt-0.5">{{ entry.content || '（空白）' }}</p>
          </div>
        </div>
      </div>

      <!-- 写今日 -->
      <div class="px-3 py-2 border-t border-border">
        <button
          @click="createToday"
          class="w-full py-2 rounded-[8px] text-[13px] text-text-secondary border border-dashed border-border transition-colors hover:bg-surface-hover hover:text-accent hover:border-accent"
        >
          + 写今日
        </button>
      </div>
    </aside>

    <!-- 主内容：日记本页面 -->
    <main class="flex-1 overflow-y-auto bg-bg relative">
      <!-- 装饰背景 -->
      <div class="absolute inset-0 opacity-[0.02] pointer-events-none" style="background-image: url('data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'1\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E');"></div>

      <div class="max-w-[680px] mx-auto px-8 py-8">
        <!-- 日期头 -->
        <div class="text-center mb-8">
          <div class="text-[11px] text-text-secondary tracking-[3px] uppercase">{{ formatDateYear(selectedDate) }}</div>
          <div class="text-[42px] font-bold leading-tight mt-1" style="font-family: 'TsangerJinKai02', serif;">
            {{ formatDateDay(selectedDate) }}
          </div>
          <div class="text-[13px] text-text-secondary mt-1">{{ formatDateWeek(selectedDate) }}</div>
          <div v-if="selectedDate === today" class="inline-block mt-2 px-3 py-0.5 rounded-full bg-accent-glow text-accent text-[11px]">今天</div>
        </div>

        <!-- 天气 地点 心情 -->
        <div class="flex items-center justify-center gap-4 mb-6 flex-wrap">
          <div class="flex items-center gap-1.5 bg-surface border border-border rounded-full px-3 py-1.5">
            <input v-model="currentEntry.weather" placeholder="天气" class="bg-transparent text-[12px] text-text outline-none w-[50px] text-center" />
          </div>
          <div class="flex items-center gap-1.5 bg-surface border border-border rounded-full px-3 py-1.5">
            <input v-model="currentEntry.location" placeholder="地点" class="bg-transparent text-[12px] text-text outline-none w-[80px] text-center" />
          </div>
          <div class="flex items-center gap-1">
            <button
              v-for="m in moods"
              :key="m.value"
              @click="currentEntry.mood = m.value"
              :title="m.label"
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-lg transition-all',
                currentEntry.mood === m.value ? 'bg-accent-glow scale-110' : 'hover:bg-surface-hover opacity-40 hover:opacity-100'
              ]"
            >
              {{ m.emoji }}
            </button>
          </div>
        </div>

        <!-- 贴纸 -->
        <div class="flex items-center justify-center gap-1 mb-6 flex-wrap">
          <span class="text-[10px] text-text-secondary mr-1">贴纸</span>
          <button
            v-for="s in stickers"
            :key="s"
            @click="currentEntry.sticker = currentEntry.sticker === s ? '' : s"
            :class="[
              'text-base px-1.5 py-0.5 rounded-[6px] transition-all',
              currentEntry.sticker === s ? 'bg-accent-glow scale-110' : 'hover:bg-surface-hover opacity-50 hover:opacity-100'
            ]"
          >
            {{ s }}
          </button>
        </div>

        <!-- 贴纸展示 -->
        <div v-if="currentEntry.sticker" class="text-center mb-4 text-4xl animate-bounce-slow">
          {{ currentEntry.sticker }}
        </div>

        <!-- 正文编辑器 -->
        <div class="relative">
          <!-- 左侧装订线装饰 -->
          <div class="absolute left-0 top-0 bottom-0 w-8 border-r border-dashed border-border/30"></div>
          
          <textarea
            v-model="currentEntry.content"
            placeholder="亲爱的自己，今天发生了什么？&#10;不用很长，像安东尼那样，随便写点什么就好..."
            class="w-full min-h-[360px] bg-transparent pl-10 pr-4 py-4 text-text text-[15px] leading-[2] outline-none resize-y"
            style="font-family: 'TsangerJinKai02', 'Source Han Serif SC', 'Noto Serif CJK SC', Georgia, serif;"
          ></textarea>
        </div>

        <!-- 标签 -->
        <div class="mt-6 pl-10">
          <div class="flex items-center gap-2 flex-wrap">
            <span v-for="(tag, i) in currentEntry.tags" :key="i"
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] bg-surface border border-border text-text-secondary transition-colors hover:border-accent hover:text-accent">
              # {{ tag }}
              <button @click="removeTag(i)" class="text-[10px] hover:text-danger ml-0.5">×</button>
            </span>
            <input
              v-model="tagInput"
              @keydown.enter.prevent="addTag"
              placeholder="+ 标签"
              class="px-2.5 py-1 bg-transparent border border-dashed border-border rounded-full text-text text-[11px] outline-none w-[80px] focus:border-accent transition-colors"
            />
          </div>
        </div>

        <!-- 底部操作 -->
        <div class="flex items-center justify-between mt-8 pl-10">
          <div class="text-[11px] text-text-secondary">
            {{ currentEntry.id ? '上次保存 ' + formatTime(currentEntry.updated_at) : '还未保存' }}
          </div>
          <div class="flex gap-2">
            <button
              v-if="currentEntry.id"
              @click="deleteEntry"
              class="px-4 py-2 rounded-full border border-danger/30 text-danger text-[12px] hover:bg-danger/10 transition-colors"
            >
              删除
            </button>
            <button
              @click="saveEntry"
              :disabled="saving"
              class="px-6 py-2 rounded-full bg-accent text-white text-[12px] hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- 右侧：心情统计 + 随机回顾 -->
    <aside class="w-[200px] min-w-[200px] bg-surface border-l border-border flex flex-col overflow-hidden">
      <!-- 心情分布 -->
      <div class="px-4 py-3 border-b border-border">
        <div class="text-[10px] text-text-secondary uppercase tracking-[2px] mb-3">心情分布</div>
        <div class="flex flex-col gap-1.5">
          <div v-for="m in moodStats" :key="m.mood" class="flex items-center gap-2">
            <span class="text-sm">{{ moodEmoji(m.mood) }}</span>
            <div class="flex-1 h-[4px] bg-bg rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all" :style="{ width: m.percent + '%', background: m.color }"></div>
            </div>
            <span class="text-[10px] text-text-secondary w-6 text-right">{{ m.count }}</span>
          </div>
        </div>
      </div>

      <!-- 随机回顾 -->
      <div class="px-4 py-3 border-b border-border flex-1 overflow-y-auto">
        <div class="text-[10px] text-text-secondary uppercase tracking-[2px] mb-3">随机回顾</div>
        <div v-if="randomEntry" @click="loadEntry(randomEntry)"
          class="p-3 bg-bg border border-border rounded-[10px] cursor-pointer hover:border-accent transition-colors">
          <div class="flex items-center justify-between mb-1">
            <span class="text-[11px] text-text-secondary">{{ formatDateShort(randomEntry.date) }}</span>
            <span class="text-sm">{{ moodEmoji(randomEntry.mood) }}</span>
          </div>
          <p class="text-[12px] text-text leading-relaxed line-clamp-4">{{ randomEntry.content }}</p>
        </div>
        <div v-else class="text-center py-4 text-text-secondary text-xs">
          多写一些，就会有回忆
        </div>
        <button @click="refreshRandom" class="mt-2 text-[11px] text-accent hover:text-[#a5b0ff] transition-colors w-full text-center">
          ↻ 换一篇
        </button>
      </div>

      <!-- 常用标签 -->
      <div class="px-4 py-3">
        <div class="text-[10px] text-text-secondary uppercase tracking-[2px] mb-2">常用标签</div>
        <div class="flex flex-wrap gap-1">
          <button
            v-for="tag in allTags.slice(0, 10)"
            :key="tag"
            @click="addTagFromCloud(tag)"
            class="px-2 py-0.5 rounded-full text-[10px] bg-bg border border-border text-text-secondary hover:border-accent hover:text-accent transition-colors"
          >
            # {{ tag }}
          </button>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings.js'

const store = useSettingsStore()

const today = new Date().toISOString().split('T')[0]
const selectedDate = ref(today)
const selectedEntryId = ref(0)
const saving = ref(false)
const tagInput = ref('')
const lastSavedSnapshot = ref(null)

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)

const entries = ref([])
const stats = ref({ total: 0, streak: 0 })
const allTags = ref([])
const randomEntry = ref(null)

const moods = [
  { value: 'happy', emoji: '😊', label: '开心', color: '#f0a060' },
  { value: 'excited', emoji: '🤩', label: '兴奋', color: '#7c8aff' },
  { value: 'calm', emoji: '😌', label: '平静', color: '#4ec9b0' },
  { value: 'neutral', emoji: '😐', label: '一般', color: '#8888a0' },
  { value: 'tired', emoji: '😴', label: '疲惫', color: '#6b6a64' },
  { value: 'sad', emoji: '😢', label: '难过', color: '#5a8abf' },
  { value: 'angry', emoji: '😠', label: '生气', color: '#ff5c7a' },
  { value: 'loved', emoji: '🥰', label: '被爱', color: '#e070a0' },
]

const stickers = ['🌸', '🌿', '☕', '📚', '✨', '🌙', '🎵', '🍵', '🐱', '🌈', '🍂', '❄️', '🌊', '📷']

const currentEntry = ref({
  id: 0,
  date: today,
  content: '',
  mood: 'neutral',
  tags: [],
  weather: '',
  location: '',
  sticker: ''
})

function moodEmoji(mood) {
  const m = moods.find(x => x.value === mood)
  return m ? m.emoji : '😐'
}

function captureSnapshot() {
  return {
    content: currentEntry.value.content,
    mood: currentEntry.value.mood,
    tags: [...currentEntry.value.tags],
    weather: currentEntry.value.weather,
    location: currentEntry.value.location,
    sticker: currentEntry.value.sticker
  }
}

function hasUnsavedChanges() {
  if (!lastSavedSnapshot.value) return false
  const cur = currentEntry.value
  const snap = lastSavedSnapshot.value
  return cur.content !== snap.content ||
    cur.mood !== snap.mood ||
    JSON.stringify(cur.tags) !== JSON.stringify(snap.tags) ||
    cur.weather !== snap.weather ||
    cur.location !== snap.location ||
    cur.sticker !== snap.sticker
}

function formatDay(dateStr) {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function formatDateShort(dateStr) {
  const d = new Date(dateStr)
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2,'0')}.${String(d.getDate()).padStart(2,'0')}`
}

function formatDateYear(dateStr) {
  const d = new Date(dateStr)
  return `${d.getFullYear()} . ${String(d.getMonth() + 1).padStart(2,'0')}`
}

function formatDateDay(dateStr) {
  const d = new Date(dateStr)
  return String(d.getDate()).padStart(2, '0')
}

function formatDateWeek(dateStr) {
  const d = new Date(dateStr)
  const week = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return week[d.getDay()]
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const startWeekday = firstDay.getDay()
  const daysInMonth = lastDay.getDate()

  const days = []
  const prevLast = new Date(year, month - 1, 0)
  for (let i = startWeekday - 1; i >= 0; i--) {
    const d = prevLast.getDate() - i
    const dateStr = `${prevLast.getFullYear()}-${String(prevLast.getMonth() + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    days.push({ day: d, date: dateStr, isCurrentMonth: false, hasEntry: entries.value.some(e => e.date === dateStr) })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    days.push({ day: d, date: dateStr, isCurrentMonth: true, hasEntry: entries.value.some(e => e.date === dateStr) })
  }
  const remaining = (7 - (days.length % 7)) % 7
  for (let d = 1; d <= remaining; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    days.push({ day: d, date: dateStr, isCurrentMonth: false, hasEntry: entries.value.some(e => e.date === dateStr) })
  }
  return days
})

const filteredEntries = computed(() => {
  return entries.value.filter(e => {
    const d = new Date(e.date)
    return d.getFullYear() === currentYear.value && d.getMonth() + 1 === currentMonth.value
  })
})

const moodStats = computed(() => {
  const counts = {}
  entries.value.forEach(e => {
    counts[e.mood] = (counts[e.mood] || 0) + 1
  })
  const total = entries.value.length
  return moods.map(m => ({
    mood: m.value,
    emoji: m.emoji,
    count: counts[m.value] || 0,
    percent: total ? ((counts[m.value] || 0) / total * 100) : 0,
    color: m.color
  })).filter(m => m.count > 0).sort((a, b) => b.count - a.count)
})

function prevMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

const { confirm } = useConfirm()

async function selectDate(dateStr) {
  // 检查是否有未保存的修改
  if (hasUnsavedChanges()) {
    const save = await confirm({
      title: '未保存的修改',
      message: '当前日记有未保存的内容，是否保存后再切换？\n\n"确认" = 保存并切换\n"取消" = 留在此页'
    })
    if (save) {
      await saveEntry()
    } else {
      return  // 留在此页，不切换
    }
  }

  selectedDate.value = dateStr
  const found = entries.value.find(e => e.date === dateStr)
  if (found) {
    loadEntry(found)
  } else {
    currentEntry.value = {
      id: 0,
      date: dateStr,
      content: '',
      mood: 'neutral',
      tags: [],
      weather: '',
      location: '',
      sticker: ''
    }
    selectedEntryId.value = 0
    lastSavedSnapshot.value = captureSnapshot()
  }
}

function createToday() {
  selectDate(today)
}

function loadEntry(entry) {
  currentEntry.value = { ...entry, tags: [...(entry.tags || [])] }
  selectedEntryId.value = entry.id
  selectedDate.value = entry.date
  const d = new Date(entry.date)
  currentYear.value = d.getFullYear()
  currentMonth.value = d.getMonth() + 1
  lastSavedSnapshot.value = captureSnapshot()
}

function addTag() {
  const t = tagInput.value.trim()
  if (t && !currentEntry.value.tags.includes(t)) {
    currentEntry.value.tags.push(t)
  }
  tagInput.value = ''
}

function addTagFromCloud(tag) {
  if (!currentEntry.value.tags.includes(tag)) {
    currentEntry.value.tags.push(tag)
  }
}

function removeTag(i) {
  currentEntry.value.tags.splice(i, 1)
}

async function saveEntry() {
  saving.value = true
  try {
    const payload = {
      date: selectedDate.value,
      content: currentEntry.value.content,
      mood: currentEntry.value.mood,
      tags: currentEntry.value.tags,
      weather: currentEntry.value.weather,
      location: currentEntry.value.location,
      sticker: currentEntry.value.sticker
    }
    const result = await store.apiPost('/journal/entries', payload)
    if (result.error) {
      toast.error('保存失败：' + result.error)
      return
    }
    currentEntry.value = { ...result, tags: [...(result.tags || [])] }
    selectedEntryId.value = result.id
    lastSavedSnapshot.value = captureSnapshot()
    await fetchEntries()
    await fetchStats()
    await fetchTags()
    refreshRandom()
  } finally {
    saving.value = false
  }
}

async function deleteEntry() {
  if (!currentEntry.value.id) return
  const ok = await confirm({ message: '确定要删除这篇日记吗？', danger: true })
  if (!ok) return
  await store.apiDelete(`/journal/entries/${currentEntry.value.id}`)
  currentEntry.value = {
    id: 0,
    date: selectedDate.value,
    content: '',
    mood: 'neutral',
    tags: [],
    weather: '',
    location: '',
    sticker: ''
  }
  selectedEntryId.value = 0
  lastSavedSnapshot.value = captureSnapshot()
  await fetchEntries()
  await fetchStats()
  await fetchTags()
  refreshRandom()
}

function refreshRandom() {
  if (entries.value.length === 0) {
    randomEntry.value = null
    return
  }
  const idx = Math.floor(Math.random() * entries.value.length)
  randomEntry.value = entries.value[idx]
}

async function fetchEntries() {
  const data = await store.apiGet(`/journal/entries?year=${currentYear.value}&month=${currentMonth.value}`)
  entries.value = data || []
}

async function fetchStats() {
  const data = await store.apiGet('/journal/stats')
  stats.value = data || { total: 0, streak: 0 }
}

async function fetchTags() {
  const data = await store.apiGet('/journal/tags')
  allTags.value = data || []
}

watch([currentYear, currentMonth], fetchEntries)

onMounted(async () => {
  await fetchEntries()
  await fetchStats()
  await fetchTags()
  refreshRandom()
  const todayEntry = entries.value.find(e => e.date === today)
  if (todayEntry) {
    loadEntry(todayEntry)
  } else {
    lastSavedSnapshot.value = captureSnapshot()
  }
})
</script>

<style scoped>
@keyframes bounce-slow {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
.animate-bounce-slow {
  animation: bounce-slow 3s ease-in-out infinite;
}
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
