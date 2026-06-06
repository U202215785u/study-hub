<template>
  <div class="flex flex-col gap-5">
    <!-- 标题栏 + 视图切换 -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <h1 class="text-xl font-bold tracking-tight">⏰ DDL 时间规划</h1>
      <div class="flex items-center gap-2">
        <!-- 视图切换 -->
        <div class="flex bg-surface border border-border rounded-[8px] p-0.5">
          <button v-for="v in viewOptions" :key="v.key" @click="currentView = v.key"
            :class="['px-3 py-1.5 rounded-[6px] text-xs transition-colors', currentView === v.key ? 'bg-accent text-white' : 'text-text-secondary hover:text-text']">
            {{ v.label }}
          </button>
        </div>
        <button @click="openAddModal()" class="px-3 py-1.5 rounded-[8px] text-xs text-white bg-accent hover:bg-[#6a75e0] transition-colors">+ 添加</button>
      </div>
    </div>

    <!-- 日期导航（日/周/月视图） -->
    <div v-if="currentView !== 'list'" class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button @click="navigatePrev" class="w-7 h-7 rounded-[6px] bg-surface border border-border text-text-secondary hover:text-text flex items-center justify-center text-xs">◀</button>
        <span class="text-sm font-medium min-w-[120px] text-center">{{ navigationTitle }}</span>
        <button @click="navigateNext" class="w-7 h-7 rounded-[6px] bg-surface border border-border text-text-secondary hover:text-text flex items-center justify-center text-xs">▶</button>
      </div>
      <button @click="goToday" class="px-3 py-1 rounded-[6px] text-xs bg-surface border border-border text-text-secondary hover:text-text transition-colors">今天</button>
    </div>

    <!-- ===== 日视图 ===== -->
    <div v-if="currentView === 'day'" class="flex flex-col gap-0 border border-border rounded-[12px] overflow-hidden bg-surface">
      <div class="flex border-b border-border">
        <div class="w-14 flex-shrink-0 border-r border-border bg-surface/80"></div>
        <div class="flex-1 py-2 px-3 text-sm font-medium text-center">{{ format(currentDate, 'M月d日 EEEE') }}</div>
      </div>
      <div class="flex flex-col relative" style="height: 720px; overflow-y: auto;">
        <!-- 时间刻度背景 -->
        <div class="absolute inset-0 flex flex-col">
          <div v-for="h in 24" :key="h" class="flex-1 border-b border-border/30"></div>
        </div>
        <!-- 时间行 -->
        <div v-for="h in timeSlots" :key="h" class="flex relative" style="height: 60px;">
          <div class="w-14 flex-shrink-0 border-r border-border text-[11px] text-text-secondary text-right pr-2 pt-1 bg-surface/80">{{ String(h).padStart(2,'0') }}:00</div>
          <div class="flex-1 relative" @click="onTimeSlotClick(h)">
            <!-- 当前时间线 -->
            <div v-if="isCurrentHour(h)" class="absolute left-0 right-0 border-t border-danger/60 z-10 pointer-events-none" :style="{top: currentMinutePercent + '%'}"></div>
          </div>
        </div>
        <!-- 任务块 -->
        <div class="absolute left-14 right-2 top-0 bottom-0 pointer-events-none">
          <div v-for="task in dayTasks" :key="task.id"
            class="absolute rounded-[6px] border px-2 py-1 text-xs cursor-pointer pointer-events-auto transition-transform hover:scale-[1.02] hover:z-20 overflow-hidden"
            :class="taskStatusClass(task)"
            :style="taskBlockStyle(task)"
            @click="editTask(task)">
            <div class="font-medium truncate">{{ task.title }}</div>
            <div v-if="task.end_time" class="text-[10px] opacity-70">{{ task.start_time || '' }} - {{ task.end_time }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 周视图 ===== -->
    <div v-if="currentView === 'week'" class="border border-border rounded-[12px] overflow-hidden bg-surface">
      <div class="grid grid-cols-7 border-b border-border">
        <div v-for="d in weekDays" :key="d.date" class="py-2 px-1 text-center border-r border-border last:border-r-0"
          :class="isToday(d.date) ? 'bg-accent/10' : ''">
          <div class="text-[11px] text-text-secondary">{{ d.weekday }}</div>
          <div class="text-sm font-medium" :class="isToday(d.date) ? 'text-accent' : ''">{{ format(d.date, 'd') }}</div>
        </div>
      </div>
      <div class="grid grid-cols-7 min-h-[300px]">
        <div v-for="d in weekDays" :key="d.date" class="border-r border-border last:border-r-0 p-2 min-h-[300px]"
          :class="isToday(d.date) ? 'bg-accent/5' : ''">
          <div v-for="task in d.tasks" :key="task.id"
            class="mb-1.5 px-2 py-1.5 rounded-[6px] border text-[11px] cursor-pointer hover:scale-[1.02] transition-transform"
            :class="taskStatusClass(task)"
            @click="editTask(task)">
            <div class="font-medium truncate">{{ task.title }}</div>
            <div v-if="task.start_time" class="opacity-70">{{ task.start_time }}{{ task.end_time ? `-${task.end_time}` : '' }}</div>
          </div>
          <div v-if="d.tasks.length === 0" class="text-[11px] text-text-secondary/50 text-center mt-4">无任务</div>
        </div>
      </div>
    </div>

    <!-- ===== 月视图 ===== -->
    <div v-if="currentView === 'month'" class="border border-border rounded-[12px] overflow-hidden bg-surface">
      <div class="grid grid-cols-7 border-b border-border">
        <div v-for="w in ['一','二','三','四','五','六','日']" :key="w" class="py-2 text-center text-[11px] text-text-secondary font-medium">周{{ w }}</div>
      </div>
      <div class="grid grid-cols-7">
        <div v-for="d in monthDays" :key="d.date" class="min-h-[100px] border-r border-b border-border p-1.5"
          :class="[d.isCurrentMonth ? '' : 'bg-black/20 opacity-50', isToday(d.date) ? 'bg-accent/5' : '']">
          <div class="text-[11px] mb-1" :class="isToday(d.date) ? 'text-accent font-bold' : 'text-text-secondary'">{{ format(d.date, 'd') }}</div>
          <div v-for="task in d.tasks.slice(0, 3)" :key="task.id"
            class="mb-0.5 px-1 py-0.5 rounded-[4px] text-[10px] truncate cursor-pointer"
            :class="taskStatusBgClass(task)"
            @click="editTask(task)">
            {{ task.title }}
          </div>
          <div v-if="d.tasks.length > 3" class="text-[10px] text-text-secondary px-1">+{{ d.tasks.length - 3 }}</div>
        </div>
      </div>
    </div>

    <!-- ===== 列表视图（原有功能） ===== -->
    <div v-if="currentView === 'list'" class="flex flex-col gap-5">
      <!-- 统计条 -->
      <div class="grid grid-cols-5 gap-3">
        <div class="bg-surface border border-border rounded-[10px] p-3 text-center">
          <div class="text-[11px] text-text-secondary uppercase tracking-[1px]">全部</div>
          <div class="text-lg font-bold">{{ stats.total }}</div>
        </div>
        <div class="bg-surface border border-border rounded-[10px] p-3 text-center">
          <div class="text-[11px] text-text-secondary uppercase tracking-[1px]">待办</div>
          <div class="text-lg font-bold text-[#f0a060]">{{ stats.todo }}</div>
        </div>
        <div class="bg-surface border border-border rounded-[10px] p-3 text-center">
          <div class="text-[11px] text-text-secondary uppercase tracking-[1px]">进行中</div>
          <div class="text-lg font-bold text-accent">{{ stats.in_progress }}</div>
        </div>
        <div class="bg-surface border border-border rounded-[10px] p-3 text-center">
          <div class="text-[11px] text-text-secondary uppercase tracking-[1px]">已完成</div>
          <div class="text-lg font-bold text-[#4ec9b0]">{{ stats.done }}</div>
        </div>
        <div :class="['border rounded-[10px] p-3 text-center cursor-pointer transition-colors', stats.overdue > 0 ? 'bg-[#ff444410] border-danger/30 hover:bg-[#ff444420]' : 'bg-surface border-border']" @click="showOverdue = true">
          <div class="text-[11px] uppercase tracking-[1px]" :class="stats.overdue > 0 ? 'text-danger' : 'text-text-secondary'">超期</div>
          <div class="text-lg font-bold" :class="stats.overdue > 0 ? 'text-danger' : ''">{{ stats.overdue }}</div>
        </div>
      </div>

      <!-- 最近截止：倒计时卡片 -->
      <div v-if="nearestTask" :class="['rounded-[12px] border p-5 flex items-center gap-4', nearestTask.days_left < 0 ? 'bg-[#ff444410] border-danger/30' : nearestTask.days_left <= 3 ? 'bg-[#f0a06010] border-[#f0a060]/30' : 'bg-surface border-border']">
        <div class="text-[40px]">{{ nearestTask.days_left < 0 ? '🚨' : nearestTask.days_left <= 3 ? '⚠️' : '⏰' }}</div>
        <div class="flex-1 min-w-0">
          <div class="text-[13px] text-text-secondary">{{ nearestTask.days_left < 0 ? '已超期' : nearestTask.days_left === 0 ? '今天截止' : '最近截止' }}</div>
          <div class="text-base font-semibold truncate" :class="nearestTask.days_left < 0 ? 'text-danger' : ''">{{ nearestTask.title }}</div>
          <div class="text-xs text-text-secondary mt-0.5">{{ formatDate(nearestTask.due_date) }}</div>
        </div>
        <div class="text-right flex-shrink-0">
          <div :class="['text-2xl font-bold font-mono', nearestTask.days_left < 0 ? 'text-danger' : nearestTask.days_left <= 3 ? 'text-[#f0a060]' : 'text-accent']">
            {{ nearestTask.days_left < 0 ? `${Math.abs(nearestTask.days_left)}天前` : nearestTask.days_left === 0 ? '今天' : `${nearestTask.days_left}天` }}
          </div>
          <div class="text-[11px] text-text-secondary">{{ nearestTask.days_left < 0 ? '已过期' : nearestTask.days_left === 0 ? '就是今天！' : '剩余' }}</div>
        </div>
      </div>

      <!-- 类型筛选 -->
      <div class="flex gap-2">
        <button @click="filterType = ''" :class="['px-3 py-1.5 rounded-[8px] text-xs transition-colors', filterType === '' ? 'bg-accent text-white' : 'bg-surface border border-border text-text-secondary hover:text-text']">全部</button>
        <button @click="filterType = 'learning'" :class="['px-3 py-1.5 rounded-[8px] text-xs transition-colors', filterType === 'learning' ? 'bg-accent text-white' : 'bg-surface border border-border text-text-secondary hover:text-text']">📚 学习</button>
        <button @click="filterType = 'milestone'" :class="['px-3 py-1.5 rounded-[8px] text-xs transition-colors', filterType === 'milestone' ? 'bg-accent text-white' : 'bg-surface border border-border text-text-secondary hover:text-text']">📍 里程碑</button>
        <button @click="filterType = 'todo'" :class="['px-3 py-1.5 rounded-[8px] text-xs transition-colors', filterType === 'todo' ? 'bg-accent text-white' : 'bg-surface border border-border text-text-secondary hover:text-text']">📋 待办</button>
      </div>

      <!-- 里程碑时间线 -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-semibold text-text-secondary uppercase tracking-[1px]">📍 里程碑</h2>
          <button @click="openAddModal('milestone')" class="text-xs text-accent hover:text-[#a5b0ff] transition-colors">+ 添加</button>
        </div>
        <div v-if="milestones.length === 0" class="bg-surface border border-dashed border-border rounded-[12px] p-6 text-center text-text-secondary text-sm">还没有里程碑，点击右上角添加</div>
        <div v-else class="relative">
          <div class="absolute left-[15px] top-2 bottom-2 w-[1px] bg-border"></div>
          <div class="flex flex-col gap-0">
            <div v-for="m in milestones" :key="m.id" class="relative pl-10 py-2.5 group">
              <div :class="['absolute left-[10px] top-[14px] w-[11px] h-[11px] rounded-full border-2 z-10 transition-colors',
                m.status === 'done' ? 'bg-[#4ec9b0] border-[#4ec9b0]' : m.status === 'in_progress' ? 'bg-accent border-accent' : m.days_left !== null && m.days_left < 0 ? 'bg-danger border-danger' : 'bg-surface border-border']"></div>
              <div :class="['flex items-center gap-3 p-2.5 rounded-[8px] transition-colors hover:bg-white/[0.03]', m.status === 'done' ? 'opacity-50' : '']">
                <span :class="['text-xs px-1.5 py-0.5 rounded-[4px] flex-shrink-0',
                  m.status === 'done' ? 'bg-[#4ec9b020] text-[#4ec9b0]' : m.status === 'in_progress' ? 'bg-accent/20 text-accent' : m.days_left !== null && m.days_left < 0 ? 'bg-danger/20 text-danger' : 'bg-border/30 text-text-secondary']">
                  {{ m.status === 'done' ? '完成' : m.status === 'in_progress' ? '进行中' : '待定' }}
                </span>
                <span :class="['text-sm flex-1 cursor-pointer', m.status === 'done' ? 'line-through text-text-secondary' : '']" @click="editTask(m)">{{ m.title }}</span>
                <span v-if="m.due_date" class="text-xs text-text-secondary flex-shrink-0">{{ formatDate(m.due_date) }}</span>
                <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  <button v-if="m.status !== 'done'" @click="cycleStatus(m)" class="text-xs px-1.5 py-0.5 rounded-[4px] hover:bg-white/[0.08] text-text-secondary hover:text-[#4ec9b0]" title="切换状态">✓</button>
                  <button @click="deleteTask(m.id)" class="text-xs px-1.5 py-0.5 rounded-[4px] hover:bg-danger/20 text-text-secondary hover:text-danger" title="删除">×</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 可拖拽待办清单 -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-semibold text-text-secondary uppercase tracking-[1px]">📋 待办清单</h2>
          <div class="flex gap-2">
            <button @click="showOverdue = !showOverdue" :class="['text-xs transition-colors', showOverdue ? 'text-danger' : 'text-text-secondary hover:text-text']">{{ showOverdue ? '显示全部' : '只看超期' }}</button>
            <button @click="openAddModal('todo')" class="text-xs text-accent hover:text-[#a5b0ff] transition-colors">+ 添加</button>
          </div>
        </div>
        <div v-if="todoTasks.length === 0" class="bg-surface border border-dashed border-border rounded-[12px] p-6 text-center text-text-secondary text-sm">待办清单是空的，点击右上角添加</div>
        <draggable v-else v-model="todoTasks" item-key="id" handle=".drag-handle" :animation="200" ghost-class="opacity-40" @end="onDragEnd" class="flex flex-col gap-1.5">
          <template #item="{ element: t }">
            <div :class="['flex items-center gap-3 p-3 rounded-[10px] transition-colors group cursor-default',
              t.status === 'done' ? 'bg-surface/50 opacity-50' : t.days_left !== null && t.days_left < 0 ? 'bg-[#ff444408] border border-danger/20' : 'bg-surface border border-border hover:bg-white/[0.02]']">
              <span class="drag-handle cursor-grab text-text-secondary opacity-30 hover:opacity-100 transition-opacity flex-shrink-0 text-sm">⋮⋮</span>
              <button @click="toggleDone(t)" :class="['w-[20px] h-[20px] rounded-[5px] border-2 flex items-center justify-center flex-shrink-0 transition-colors', t.status === 'done' ? 'bg-[#4ec9b0] border-[#4ec9b0]' : 'border-border hover:border-accent']">
                <span v-if="t.status === 'done'" class="text-[11px] text-white">✓</span>
              </button>
              <span :class="['text-sm flex-1 min-w-0 truncate cursor-pointer', t.status === 'done' ? 'line-through text-text-secondary' : '']" @click="editTask(t)">{{ t.title }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded-[4px] bg-border/30 text-text-secondary flex-shrink-0 hidden sm:inline-block">{{ t.task_type === 'learning' ? '📚' : '📋' }}</span>
              <span :class="['text-xs flex-shrink-0', t.days_left !== null && t.days_left < 0 ? 'text-danger font-medium' : t.days_left !== null && t.days_left <= 3 ? 'text-[#f0a060]' : 'text-text-secondary']">
                {{ t.due_date ? formatDate(t.due_date) : '无截止' }}
                <span v-if="t.days_left !== null && t.days_left !== undefined && t.status !== 'done'" class="ml-1">({{ t.days_left < 0 ? `超${Math.abs(t.days_left)}天` : t.days_left === 0 ? '今天' : `${t.days_left}天` }})</span>
              </span>
              <button @click="deleteTask(t.id)" class="opacity-0 group-hover:opacity-100 transition-opacity text-text-secondary hover:text-danger text-sm flex-shrink-0 px-1">×</button>
            </div>
          </template>
        </draggable>
      </div>
    </div>

    <!-- 添加/编辑弹窗 -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showModal = false">
      <div class="bg-[#1a1a2e] border border-border rounded-[14px] p-6 w-[460px] max-w-[90vw] shadow-2xl max-h-[90vh] overflow-y-auto">
        <h3 class="text-base font-semibold mb-4">{{ editingTask ? '编辑任务' : '添加任务' }}</h3>
        <div class="flex flex-col gap-3">
          <input v-model="form.title" type="text" placeholder="任务标题" class="px-3 py-2.5 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent" @keydown.enter="saveForm">
          <textarea v-model="form.description" placeholder="描述（可选）" rows="2" class="px-3 py-2.5 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent resize-none"></textarea>

          <!-- 计划类型 -->
          <div>
            <label class="text-[11px] text-text-secondary block mb-1">计划类型</label>
            <select v-model="form.plan_type" class="w-full px-3 py-2 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent">
              <option value="todo">📋 普通待办</option>
              <option value="daily">☀️ 日计划</option>
              <option value="weekly">📅 周计划</option>
              <option value="monthly">🗓️ 月计划</option>
            </select>
          </div>

          <!-- 日计划时间 -->
          <div v-if="form.plan_type === 'daily'" class="flex flex-col gap-3">
            <div>
              <label class="text-[11px] text-text-secondary block mb-1">计划日期</label>
              <input v-model="form.plan_date" type="date" class="w-full px-3 py-2 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent">
            </div>
            <div class="flex gap-3">
              <div class="flex-1">
                <label class="text-[11px] text-text-secondary block mb-1">开始时间</label>
                <input v-model="form.start_time" type="time" class="w-full px-3 py-2 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent">
              </div>
              <div class="flex-1">
                <label class="text-[11px] text-text-secondary block mb-1">结束时间</label>
                <input v-model="form.end_time" type="time" class="w-full px-3 py-2 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent">
              </div>
            </div>
          </div>

          <!-- 周/月计划日期 -->
          <div v-if="form.plan_type === 'weekly' || form.plan_type === 'monthly'">
            <label class="text-[11px] text-text-secondary block mb-1">{{ form.plan_type === 'weekly' ? '周开始日期' : '月份' }}</label>
            <input v-model="form.plan_date" :type="form.plan_type === 'weekly' ? 'date' : 'month'" class="w-full px-3 py-2 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent">
          </div>

          <div class="flex gap-3">
            <div class="flex-1">
              <label class="text-[11px] text-text-secondary block mb-1">截止日期</label>
              <input v-model="form.due_date" type="date" class="w-full px-3 py-2 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent">
            </div>
            <div class="flex-1">
              <label class="text-[11px] text-text-secondary block mb-1">任务类型</label>
              <select v-model="form.task_type" class="w-full px-3 py-2 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent">
                <option value="todo">📋 待办</option>
                <option value="learning">📚 学习任务</option>
                <option value="milestone">📍 里程碑</option>
              </select>
            </div>
          </div>

          <div v-if="editingTask">
            <label class="text-[11px] text-text-secondary block mb-1">状态</label>
            <select v-model="form.status" class="w-full px-3 py-2 bg-surface border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent">
              <option value="todo">待办</option>
              <option value="in_progress">进行中</option>
              <option value="done">已完成</option>
            </select>
          </div>
        </div>
        <div class="flex gap-2.5 mt-5 justify-end">
          <button @click="showModal = false" class="px-4 py-2 rounded-[8px] text-sm text-text-secondary hover:text-text bg-white/[0.05] hover:bg-white/[0.1] transition-colors">取消</button>
          <button @click="saveForm" class="px-5 py-2 rounded-[8px] text-sm text-white bg-accent hover:bg-[#6a75e0] transition-colors">{{ editingTask ? '保存' : '添加' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import draggable from 'vuedraggable'
import { format, parseISO, startOfWeek, endOfWeek, startOfMonth, endOfMonth, eachDayOfInterval, addDays, addWeeks, addMonths, subDays, subWeeks, subMonths, isSameDay, isToday as dfIsToday, getDay } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { useSettingsStore } from '../stores/settings.js'

const settings = useSettingsStore()
const apiBase = computed(() => settings.apiBase)

const currentView = ref('day')
const viewOptions = [
  { key: 'day', label: '日' },
  { key: 'week', label: '周' },
  { key: 'month', label: '月' },
  { key: 'list', label: '列表' },
]

// 当前导航日期
const currentDate = ref(new Date())
const timeSlots = Array.from({ length: 18 }, (_, i) => i + 6) // 06:00 - 23:00

const tasks = ref([])
const stats = ref({ total: 0, todo: 0, in_progress: 0, done: 0, urgent: 0, overdue: 0 })
const filterType = ref('')
const showOverdue = ref(false)
const showModal = ref(false)
const editingTask = ref(null)
const form = ref({ title: '', description: '', due_date: '', task_type: 'todo', status: 'todo', plan_type: 'daily', plan_date: '', start_time: '', end_time: '' })

// ===== 导航 =====
const navigationTitle = computed(() => {
  if (currentView.value === 'day') return format(currentDate.value, 'yyyy年M月d日')
  if (currentView.value === 'week') {
    const start = startOfWeek(currentDate.value, { weekStartsOn: 1 })
    const end = endOfWeek(currentDate.value, { weekStartsOn: 1 })
    return `${format(start, 'M.d')} - ${format(end, 'M.d')}`
  }
  if (currentView.value === 'month') return format(currentDate.value, 'yyyy年M月')
  return ''
})

function navigatePrev() {
  if (currentView.value === 'day') currentDate.value = subDays(currentDate.value, 1)
  if (currentView.value === 'week') currentDate.value = subWeeks(currentDate.value, 1)
  if (currentView.value === 'month') currentDate.value = subMonths(currentDate.value, 1)
}
function navigateNext() {
  if (currentView.value === 'day') currentDate.value = addDays(currentDate.value, 1)
  if (currentView.value === 'week') currentDate.value = addWeeks(currentDate.value, 1)
  if (currentView.value === 'month') currentDate.value = addMonths(currentDate.value, 1)
}
function goToday() {
  currentDate.value = new Date()
}

function isToday(date) {
  return dfIsToday(date)
}

function isCurrentHour(h) {
  const now = new Date()
  return now.getHours() === h
}

const currentMinutePercent = computed(() => {
  const now = new Date()
  return (now.getMinutes() / 60) * 100
})

// ===== 任务数据计算 =====
// 最近截止的任务
const nearestTask = computed(() => {
  const upcoming = tasks.value
    .filter(t => t.due_date && t.status !== 'done' && t.days_left !== null && t.days_left !== undefined)
    .sort((a, b) => a.days_left - b.days_left)
  return upcoming[0] || null
})

// 里程碑列表
const milestones = computed(() => {
  let list = tasks.value.filter(t => t.task_type === 'milestone')
  if (filterType.value && filterType.value !== 'milestone') return []
  list.sort((a, b) => {
    if (!a.due_date && !b.due_date) return a.sort_order - b.sort_order
    if (!a.due_date) return 1
    if (!b.due_date) return -1
    return new Date(a.due_date) - new Date(b.due_date)
  })
  return list
})

// 待办任务列表
const todoTasks = computed({
  get() {
    let list = tasks.value.filter(t => t.task_type !== 'milestone')
    if (filterType.value && filterType.value !== 'todo' && filterType.value !== 'learning') {
      list = list.filter(t => t.task_type === filterType.value)
    }
    if (showOverdue.value) {
      list = list.filter(t => t.days_left !== null && t.days_left < 0 && t.status !== 'done')
    }
    list.sort((a, b) => a.sort_order - b.sort_order)
    return list
  },
  set(val) {
    const ids = val.map(t => t.id)
    const newTasks = tasks.value.map(t => {
      const idx = ids.indexOf(t.id)
      return idx >= 0 ? { ...t, sort_order: idx } : t
    })
    newTasks.sort((a, b) => a.sort_order - b.sort_order)
    tasks.value = newTasks
  }
})

// 日视图任务
const dayTasks = computed(() => {
  const dateStr = format(currentDate.value, 'yyyy-MM-dd')
  return tasks.value.filter(t => {
    if (t.plan_date === dateStr) return true
    if (!t.plan_date && t.due_date === dateStr) return true
    return false
  }).sort((a, b) => (a.start_time || '99:99').localeCompare(b.start_time || '99:99'))
})

// 周视图数据
const weekDays = computed(() => {
  const start = startOfWeek(currentDate.value, { weekStartsOn: 1 })
  const days = eachDayOfInterval({ start, end: addDays(start, 6) })
  const weekdays = ['周一','周二','周三','周四','周五','周六','周日']
  return days.map((d, i) => {
    const dateStr = format(d, 'yyyy-MM-dd')
    return {
      date: d,
      weekday: weekdays[i],
      tasks: tasks.value.filter(t => {
        if (t.plan_date === dateStr) return true
        if (!t.plan_date && t.due_date === dateStr) return true
        return false
      }).sort((a, b) => (a.start_time || '99:99').localeCompare(b.start_time || '99:99'))
    }
  })
})

// 月视图数据
const monthDays = computed(() => {
  const start = startOfMonth(currentDate.value)
  const end = endOfMonth(currentDate.value)
  const days = eachDayOfInterval({ start, end })
  // 补足开头到周一
  const firstDayWeekday = getDay(start) // 0=Sun, 1=Mon
  const padStart = firstDayWeekday === 0 ? 6 : firstDayWeekday - 1
  const paddedDays = []
  for (let i = padStart - 1; i >= 0; i--) {
    paddedDays.push({ date: subDays(start, i + 1), isCurrentMonth: false, tasks: [] })
  }
  for (const d of days) {
    const dateStr = format(d, 'yyyy-MM-dd')
    paddedDays.push({
      date: d,
      isCurrentMonth: true,
      tasks: tasks.value.filter(t => {
        if (t.plan_date === dateStr) return true
        if (!t.plan_date && t.due_date === dateStr) return true
        return false
      })
    })
  }
  // 补足到 42 格 (6行)
  while (paddedDays.length < 42) {
    const last = paddedDays[paddedDays.length - 1].date
    paddedDays.push({ date: addDays(last, 1), isCurrentMonth: false, tasks: [] })
  }
  return paddedDays
})

// ===== 工具函数 =====
function taskStatusClass(task) {
  if (task.status === 'done') return 'bg-[#4ec9b020] border-[#4ec9b040] text-[#4ec9b0]'
  if (task.status === 'in_progress') return 'bg-accent/15 border-accent/30 text-accent'
  return 'bg-[#f0a06015] border-[#f0a06030] text-[#f0a060]'
}

function taskStatusBgClass(task) {
  if (task.status === 'done') return 'bg-[#4ec9b020] text-[#4ec9b0]'
  if (task.status === 'in_progress') return 'bg-accent/15 text-accent'
  return 'bg-[#f0a06015] text-[#f0a060]'
}

function taskBlockStyle(task) {
  const top = timeToPercent(task.start_time)
  const bottom = timeToPercent(task.end_time)
  const height = Math.max(bottom - top, 4)
  return {
    top: top + '%',
    height: height + '%',
    left: '4px',
    right: '4px',
  }
}

function timeToPercent(timeStr) {
  if (!timeStr) return 0
  const [h, m] = timeStr.split(':').map(Number)
  const totalMinutes = (h - 6) * 60 + m
  return (totalMinutes / (18 * 60)) * 100
}

function onTimeSlotClick(hour) {
  const dateStr = format(currentDate.value, 'yyyy-MM-dd')
  const timeStr = String(hour).padStart(2, '0') + ':00'
  openAddModal('todo', { plan_type: 'daily', plan_date: dateStr, start_time: timeStr })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    return format(parseISO(dateStr), 'M月d日')
  } catch { return dateStr }
}

// ===== API 交互 =====
async function fetchTasks() {
  try {
    const params = new URLSearchParams()
    if (filterType.value && currentView.value === 'list') params.set('task_type', filterType.value)
    const url = `${apiBase.value}/ddl/tasks?${params}`
    const res = await fetch(url)
    if (res.ok) tasks.value = await res.json()
  } catch (e) { console.error('获取任务失败', e) }
}

async function fetchStats() {
  try {
    const res = await fetch(`${apiBase.value}/ddl/stats`)
    if (res.ok) stats.value = await res.json()
  } catch (e) { /* ignore */ }
}

function openAddModal(type = 'todo', defaults = {}) {
  editingTask.value = null
  const today = format(new Date(), 'yyyy-MM-dd')
  form.value = {
    title: '',
    description: '',
    due_date: '',
    task_type: type,
    status: 'todo',
    plan_type: defaults.plan_type || 'todo',
    plan_date: defaults.plan_date || '',
    start_time: defaults.start_time || '',
    end_time: defaults.end_time || '',
    ...defaults,
  }
  showModal.value = true
}

function editTask(task) {
  editingTask.value = task
  form.value = {
    title: task.title,
    description: task.description || '',
    due_date: task.due_date || '',
    task_type: task.task_type,
    status: task.status,
    plan_type: task.plan_type || 'todo',
    plan_date: task.plan_date || '',
    start_time: task.start_time || '',
    end_time: task.end_time || '',
  }
  showModal.value = true
}

async function saveForm() {
  if (!form.value.title.trim()) return
  try {
    if (editingTask.value) {
      await fetch(`${apiBase.value}/ddl/tasks/${editingTask.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    } else {
      await fetch(`${apiBase.value}/ddl/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    }
    showModal.value = false
    await Promise.all([fetchTasks(), fetchStats()])
  } catch (e) { console.error('保存失败', e) }
}

async function deleteTask(id) {
  try {
    await fetch(`${apiBase.value}/ddl/tasks/${id}`, { method: 'DELETE' })
    await Promise.all([fetchTasks(), fetchStats()])
  } catch (e) { console.error('删除失败', e) }
}

async function toggleDone(task) {
  const newStatus = task.status === 'done' ? 'todo' : 'done'
  try {
    await fetch(`${apiBase.value}/ddl/tasks/${task.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    })
    await Promise.all([fetchTasks(), fetchStats()])
  } catch (e) { console.error('更新失败', e) }
}

async function cycleStatus(task) {
  const next = { 'todo': 'in_progress', 'in_progress': 'done', 'done': 'todo' }
  try {
    await fetch(`${apiBase.value}/ddl/tasks/${task.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: next[task.status] }),
    })
    await Promise.all([fetchTasks(), fetchStats()])
  } catch (e) { console.error('更新失败', e) }
}

async function onDragEnd() {
  const ids = todoTasks.value.map(t => t.id)
  try {
    await fetch(`${apiBase.value}/ddl/tasks/reorder`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_ids: ids }),
    })
    await fetchStats()
  } catch (e) { console.error('排序失败', e) }
}

watch(filterType, () => fetchTasks())
watch(() => settings.apiBase, () => { fetchTasks(); fetchStats() })

onMounted(() => {
  fetchTasks()
  fetchStats()
})
</script>
