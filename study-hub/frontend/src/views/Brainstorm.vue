<template>
  <div class="w-full max-w-[700px] mx-auto flex flex-col gap-6 py-10 px-5">
    <!-- Nav -->
    <div class="flex items-center gap-4 mb-1">
      <router-link to="/" class="text-[13px] text-text-secondary hover:text-accent transition-colors">← 仪表盘</router-link>
      <h1 class="text-xl font-bold">AI 头脑风暴</h1>
    </div>

    <!-- Step Indicator -->
    <div class="flex flex-col items-center gap-2">
      <div class="flex gap-1.5 items-center justify-center">
        <template v-for="i in 3" :key="i">
          <div
            class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all"
            :class="stepClass(i)"
          >
            {{ step > i ? '✓' : i }}
          </div>
          <div v-if="i < 3" class="w-8 h-0.5 transition-all" :class="step > i ? 'bg-success' : 'bg-border'" />
        </template>
      </div>
      <div class="text-xs text-text-secondary">{{ stepLabels[step - 1] }}</div>
    </div>

    <!-- ====== Step 1: Mode Selection ====== -->
    <template v-if="step === 1">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        <div
          class="bg-surface border-2 rounded-[12px] p-7 cursor-pointer text-center transition-all duration-200 hover:border-accent hover:bg-surface-hover hover:-translate-y-0.5"
          :class="mode === 'idea' ? 'border-accent shadow-[0_0_20px_rgba(124,138,255,0.15)]' : 'border-border'"
          @click="selectMode('idea')"
        >
          <div class="text-4xl mb-2.5">💡</div>
          <div class="text-[17px] font-bold mb-1">想法发散</div>
          <div class="text-[13px] text-text-secondary mb-2">给我一个起点，帮你展开</div>
          <div class="text-[11px] text-text-secondary opacity-70">变体 · 组合 · 跨界 · 反转</div>
        </div>
        <div
          class="bg-surface border-2 rounded-[12px] p-7 cursor-pointer text-center transition-all duration-200 hover:border-accent hover:bg-surface-hover hover:-translate-y-0.5"
          :class="mode === 'prompt' ? 'border-accent shadow-[0_0_20px_rgba(124,138,255,0.15)]' : 'border-border'"
          @click="selectMode('prompt')"
        >
          <div class="text-4xl mb-2.5">✨</div>
          <div class="text-[17px] font-bold mb-1">提示词优化</div>
          <div class="text-[13px] text-text-secondary mb-2">告诉我你想让 AI 做什么</div>
          <div class="text-[11px] text-text-secondary opacity-70">目标 · 格式 · 风格 · 约束</div>
        </div>
      </div>

      <div v-if="mode" class="bg-surface border border-border rounded-[12px] p-5 mt-4">
        <div class="font-semibold mb-1">{{ mode === 'idea' ? '给我一个起点' : '描述你的需求' }}</div>
        <div class="text-[13px] text-text-secondary mb-3">
          {{ mode === 'idea' ? '一个词、一句话、一个方向都可以' : '越具体越好，我会帮你打磨成精准的提示词' }}
        </div>
        <textarea
          v-model="ideaInput"
          :placeholder="mode === 'idea' ? '输入你的想法起点…一个词、一句话、一个方向都可以' : '描述你想让 AI 完成的任务…越具体越好，我会帮你打磨成精准的提示词'"
          class="w-full p-4 rounded-[12px] border-2 border-border bg-surface text-text text-[15px] outline-none resize-y min-h-[100px] leading-relaxed transition-colors focus:border-accent focus:shadow-[0_0_20px_rgba(124,138,255,0.15)]"
        />
        <div class="mt-3">
          <button
            class="px-5 py-2.5 rounded-[8px] text-sm font-semibold cursor-pointer border transition-all duration-150 bg-accent border-accent text-white hover:bg-[#6a78e8] disabled:opacity-50 disabled:cursor-not-allowed"
            @click="startBrainstorm"
          >
            开始 →
          </button>
        </div>
      </div>
    </template>

    <!-- ====== Step 2: Conversation ====== -->
    <template v-if="step === 2">
      <div class="flex flex-col gap-3.5">
        <div
          v-for="(m, idx) in messages"
          :key="idx"
          class="p-4 rounded-[12px] animate-[fadeIn_0.3s_ease-out]"
          :class="m.role === 'user'
            ? 'bg-[rgba(124,138,255,0.08)] border border-[rgba(124,138,255,0.2)] self-end max-w-[85%]'
            : 'bg-surface border border-border'"
        >
          <div v-if="m.role === 'user'" class="text-[11px] font-bold text-text-secondary mb-1.5 uppercase tracking-wider">你</div>
          <div v-else class="text-[11px] font-bold text-text-secondary mb-1.5 uppercase tracking-wider">
            AI {{ m.round ? '# ' + m.round : '' }}
          </div>

          <div v-if="m.role === 'user'" class="text-[15px]">{{ m.content }}</div>

          <template v-else>
            <div class="text-[15px] font-semibold mb-3 leading-relaxed">
              <span v-if="m.round" class="inline-block bg-accent text-white text-[11px] px-1.5 py-0.5 rounded-lg mr-1.5 font-bold align-[2px]">{{ m.round }}</span>
              {{ m.questions?.[0] || '' }}
            </div>
            <div v-if="m.options" class="flex flex-col gap-2">
              <template v-for="(opt, oi) in m.options" :key="oi">
                <div v-if="opt === '✏️ 其他' || opt.includes('其他')" class="flex gap-2 items-center mt-1">
                  <input
                    v-model="customInputs[idx]"
                    placeholder="输入你的想法…"
                    class="flex-1 px-3 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] outline-none focus:border-accent"
                    @keydown.enter.prevent="chooseCustom(idx)"
                  />
                  <button
                    class="px-4 py-2 rounded-[8px] text-xs font-semibold cursor-pointer border transition-all duration-150 bg-surface border-border hover:bg-surface-hover hover:border-accent"
                    @click="chooseCustom(idx)"
                  >
                    发送
                  </button>
                </div>
                <button
                  v-else
                  class="block w-full text-left px-3.5 py-2.5 rounded-[8px] border transition-all duration-150 cursor-pointer text-sm bg-surface-hover border-border hover:border-accent hover:bg-[rgba(124,138,255,0.08)]"
                  @click="chooseOption(opt)"
                >
                  {{ opt }}
                </button>
              </template>
            </div>
          </template>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-5 text-text-secondary">
          <span class="inline-block text-xl tracking-wider animate-[blink_1.4s_infinite_both]">●</span>
          <span class="inline-block text-xl tracking-wider animate-[blink_1.4s_infinite_both]" style="animation-delay: 0.2s">●</span>
          <span class="inline-block text-xl tracking-wider animate-[blink_1.4s_infinite_both]" style="animation-delay: 0.4s">●</span>
        </div>

        <div ref="convEnd" />
      </div>

      <div class="flex gap-2.5 items-center mt-0">
        <span v-if="digRecommended" class="text-xs text-warn flex-1">💡 AI 建议可以收尾了，可以继续深挖也可以直接进入下一步</span>
        <span v-else class="flex-1" />
      </div>
      <div class="flex gap-2.5 flex-wrap">
        <button
          class="px-5 py-2.5 rounded-[8px] text-sm font-semibold cursor-pointer border transition-all duration-150 bg-surface border-border hover:bg-surface-hover hover:border-accent disabled:opacity-50 disabled:cursor-not-allowed"
          @click="reset"
        >
          重新开始
        </button>
        <button
          class="px-5 py-2.5 rounded-[8px] text-sm font-semibold cursor-pointer border transition-all duration-150 bg-accent border-accent text-white hover:bg-[#6a78e8] disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="loading"
          @click="goToStep3"
        >
          {{ mode === 'idea' ? '挖够了，进入发散 →' : '挖够了，生成提示词 →' }}
        </button>
      </div>
    </template>

    <!-- ====== Step 3: Output ====== -->
    <template v-if="step === 3">
      <details class="mb-4">
        <summary class="cursor-pointer text-[13px] text-text-secondary">查看对话历史</summary>
        <div class="mt-2 flex flex-col gap-2">
          <div v-for="(m, idx) in messages" :key="idx" class="text-[13px]">
            <span v-if="m.role === 'user'" class="text-text-secondary">你：{{ m.content }}</span>
            <span v-else class="text-accent">AI：{{ m.questions?.[0] || m.content?.slice(0, 100) || '' }}</span>
          </div>
        </div>
      </details>

      <MarkdownRenderer :content="output" />

      <div class="flex gap-2.5 flex-wrap mt-4">
        <button
          class="px-5 py-2.5 rounded-[8px] text-sm font-semibold cursor-pointer border transition-all duration-150 bg-surface border-border hover:bg-surface-hover hover:border-accent disabled:opacity-50 disabled:cursor-not-allowed"
          @click="reset"
        >
          重新开始
        </button>
        <button
          class="px-5 py-2.5 rounded-[8px] text-sm font-semibold cursor-pointer border transition-all duration-150 bg-surface border-border hover:bg-surface-hover hover:border-accent disabled:opacity-50 disabled:cursor-not-allowed"
          @click="goBackToStep2"
        >
          继续追问
        </button>
        <button
          class="px-5 py-2.5 rounded-[8px] text-sm font-semibold cursor-pointer border transition-all duration-150 bg-surface border-border hover:bg-surface-hover hover:border-accent disabled:opacity-50 disabled:cursor-not-allowed"
          @click="copyOutput"
        >
          复制结果
        </button>
      </div>
    </template>

    <!-- Toast -->
    <div
      v-if="toastVisible"
      class="fixed top-5 left-1/2 -translate-x-1/2 px-5 py-2.5 rounded-[8px] text-[13px] font-semibold z-[100] pointer-events-none animate-[toastIn_0.3s_ease-out]"
      :class="toastError ? 'bg-danger text-white' : 'bg-accent text-white'"
    >
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import { useSettingsStore } from '../stores/settings.js'

const settings = useSettingsStore()

// ── State ──────────────────────────────────────────────
const mode = ref(null)           // 'idea' | 'prompt'
const step = ref(1)              // 1 | 2 | 3
const messages = ref([])         // [{role, content, questions?, options?, round?}]
const loading = ref(false)
const digRecommended = ref(false)
const round = ref(0)
const output = ref('')
const ideaInput = ref('')
const customInputs = ref({})
const convEnd = ref(null)

// Toast
const toastVisible = ref(false)
const toastMessage = ref('')
const toastError = ref(false)
let toastTimer = null

// ── Computed ───────────────────────────────────────────
const stepLabels = computed(() => {
  return mode.value === 'idea' ? ['起点', '反问', '发散'] : ['需求', '反问', '生成']
})



function stepClass(i) {
  if (step.value > i) return 'border-success text-success bg-[rgba(16,185,129,0.1)]'
  if (step.value === i) return 'border-accent text-accent bg-[rgba(124,138,255,0.15)]'
  return 'border-border text-text-secondary'
}

// ── Toast ──────────────────────────────────────────────
function showToast(msg, isError = false) {
  toastMessage.value = msg
  toastError.value = isError
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2500)
}

// ── API ────────────────────────────────────────────────
async function callStep2() {
  loading.value = true
  try {
    const data = await settings.apiPost('/brainstorm/step2', {
      mode: mode.value,
      messages: messages.value
    })
    if (data.error) {
      showToast(data.error, true)
      loading.value = false
      return
    }
    round.value++
    messages.value.push({
      role: 'assistant',
      content: data.raw,
      questions: [data.question],
      options: data.options,
      round: round.value
    })
    digRecommended.value = data.dig_recommended
    loading.value = false
    await scrollToBottom()
  } catch (e) {
    showToast('请求失败: ' + e.message, true)
    loading.value = false
  }
}

async function callStep3() {
  loading.value = true
  try {
    const data = await settings.apiPost('/brainstorm/step3', {
      mode: mode.value,
      messages: messages.value
    })
    if (data.error) {
      showToast(data.error, true)
      loading.value = false
      return
    }
    step.value = 3
    output.value = data.output
    loading.value = false
  } catch (e) {
    showToast('请求失败: ' + e.message, true)
    loading.value = false
  }
}

// ── Handlers ───────────────────────────────────────────
function selectMode(m) {
  mode.value = m
}

function startBrainstorm() {
  const content = ideaInput.value.trim()
  if (!content) {
    showToast('请输入内容', true)
    return
  }
  messages.value = [{ role: 'user', content }]
  step.value = 2
  round.value = 0
  digRecommended.value = false
  ideaInput.value = ''
  callStep2()
}

function chooseOption(opt) {
  if (loading.value) return
  messages.value.push({ role: 'user', content: opt })
  callStep2()
}

function chooseCustom(idx) {
  if (loading.value) return
  const val = (customInputs.value[idx] || '').trim()
  if (!val) {
    showToast('请输入你的想法', true)
    return
  }
  messages.value.push({ role: 'user', content: val })
  customInputs.value[idx] = ''
  callStep2()
}

function goToStep3() {
  if (loading.value) return
  callStep3()
}

function reset() {
  const currentMode = mode.value
  mode.value = currentMode
  step.value = 1
  messages.value = []
  loading.value = false
  digRecommended.value = false
  round.value = 0
  output.value = ''
  ideaInput.value = ''
  customInputs.value = {}
}

function goBackToStep2() {
  step.value = 2
  digRecommended.value = false
}

function copyOutput() {
  navigator.clipboard.writeText(output.value || '').then(() => showToast('已复制到剪贴板'))
}

async function scrollToBottom() {
  await nextTick()
  if (convEnd.value) {
    convEnd.value.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes blink {
  0%, 80%, 100% { opacity: 0.2; }
  40% { opacity: 1; }
}

@keyframes toastIn {
  from { opacity: 0; transform: translateX(-50%) translateY(-10px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}
</style>
