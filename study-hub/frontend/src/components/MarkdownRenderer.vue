<template>
  <div class="markdown-content-outer" :data-theme="currentTheme">
    <div class="markdown-reading-toolbar" role="toolbar" aria-label="阅读设置">
      <div class="markdown-font-control" role="group" aria-label="字号">
        <button
          v-for="size in fontSizes"
          :key="size.key"
          type="button"
          class="markdown-font-button"
          :class="{ 'is-active': currentFontSize === size.key }"
          :aria-pressed="currentFontSize === size.key"
          :data-testid="`markdown-font-${size.key}`"
          @click.stop="setFontSize(size.key)"
        >
          {{ size.label }}
        </button>
      </div>
      <button
        type="button"
        class="kami-theme-toggle"
        data-testid="markdown-theme-toggle"
        @click.stop="cycleTheme"
        :title="`切换背景，当前为${currentLabel}`"
      >
        <span aria-hidden="true">{{ currentIcon }}</span>
        <span>{{ currentLabel }}</span>
      </button>
    </div>
    <div
      ref="contentRef"
      class="markdown-content"
      :data-theme="currentTheme"
      :data-font-size="currentFontSize"
      v-html="rendered"
    ></div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, onUpdated, nextTick } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  content: { type: String, default: '' }
})

const emit = defineEmits(['link-click'])

const WIKILINK_PLACEHOLDER = '\x00WL\x00'
const THEME_PREFERENCE_KEY = 'markdown-theme-preference'

const themes = [
  { key: 'parchment', label: '米白', icon: '☀️' },
  { key: 'kraft', label: '牛皮纸', icon: '📜' },
  { key: 'dark', label: '暗黑', icon: '🌙' }
]

const fontSizes = [
  { key: 'small', label: '小' },
  { key: 'standard', label: '标准' },
  { key: 'large', label: '大' }
]

function getDefaultTheme() {
  const saved = localStorage.getItem(THEME_PREFERENCE_KEY)
  if (saved && themes.some(t => t.key === saved)) return saved
  return 'parchment'
}

const currentTheme = ref(getDefaultTheme())

function getDefaultFontSize() {
  const saved = localStorage.getItem('markdown-font-size')
  return fontSizes.some(size => size.key === saved) ? saved : 'standard'
}

const currentFontSize = ref(getDefaultFontSize())

const currentThemeObj = computed(() => themes.find(t => t.key === currentTheme.value) || themes[0])
const currentLabel = computed(() => currentThemeObj.value.label)
const currentIcon = computed(() => currentThemeObj.value.icon)

function cycleTheme() {
  const idx = themes.findIndex(t => t.key === currentTheme.value)
  const next = themes[(idx + 1) % themes.length]
  currentTheme.value = next.key
  localStorage.setItem(THEME_PREFERENCE_KEY, next.key)
  localStorage.setItem('markdown-theme', next.key)
  window.dispatchEvent(new CustomEvent('markdown-theme-change', { detail: next.key }))
}

function setFontSize(size) {
  if (!fontSizes.some(option => option.key === size)) return
  currentFontSize.value = size
  localStorage.setItem('markdown-font-size', size)
  window.dispatchEvent(new CustomEvent('markdown-font-size-change', { detail: size }))
}

onMounted(() => {
  const handler = (e) => {
    if (e.detail && themes.some(t => t.key === e.detail)) {
      currentTheme.value = e.detail
    }
  }
  const storageHandler = (e) => {
    if (e.key === THEME_PREFERENCE_KEY && e.newValue && themes.some(t => t.key === e.newValue)) {
      currentTheme.value = e.newValue
    }
    if (e.key === 'markdown-font-size' && fontSizes.some(size => size.key === e.newValue)) {
      currentFontSize.value = e.newValue
    }
  }
  const fontSizeHandler = (e) => {
    if (fontSizes.some(size => size.key === e.detail)) {
      currentFontSize.value = e.detail
    }
  }
  window.addEventListener('markdown-theme-change', handler)
  window.addEventListener('markdown-font-size-change', fontSizeHandler)
  window.addEventListener('storage', storageHandler)

  onUnmounted(() => {
    window.removeEventListener('markdown-theme-change', handler)
    window.removeEventListener('markdown-font-size-change', fontSizeHandler)
    window.removeEventListener('storage', storageHandler)
  })
})

const rendered = computed(() => {
  if (!props.content) return ''
  try {
    const registry = []
    let processed = props.content.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (m, slug, text) => {
      const idx = registry.length
      registry.push({ slug: slug.trim(), text: (text || slug).trim() })
      return WIKILINK_PLACEHOLDER + idx + WIKILINK_PLACEHOLDER
    })

    marked.setOptions({ breaks: true, gfm: true })
    processed = marked.parse(processed)

    // 外部链接在新标签页打开
    processed = processed.replace(/<a href="(https?:\/\/[^\"]*)"/g, '<a href="$1" target="_blank" rel="noopener noreferrer"')

    processed = processed.replace(new RegExp(WIKILINK_PLACEHOLDER + '(\\d+)' + WIKILINK_PLACEHOLDER, 'g'), (m, idx) => {
      const wl = registry[parseInt(idx)]
      if (wl) {
        return `<a href="javascript:void(0)" class="wikilink" data-wikilink="${escHtml(encodeURIComponent(wl.slug))}">${escHtml(wl.text)}</a>`
      }
      return m
    })

    return processed
  } catch (e) {
    return escHtml(props.content).replace(/\n/g, '<br>')
  }
})

const contentRef = ref(null)

// 在内容渲染后，直接给每个 wikilink 绑定点击事件（避免事件委托在复杂 DOM 中失效）
function bindWikilinkEvents() {
  if (!contentRef.value) return
  contentRef.value.querySelectorAll('a[data-wikilink]').forEach(a => {
    a.onclick = (e) => {
      e.preventDefault()
      e.stopPropagation()
      const slug = decodeURIComponent(a.getAttribute('data-wikilink'))
      window.dispatchEvent(new CustomEvent('markdown-wikilink-click', { detail: slug }))
      emit('link-click', slug)
    }
  })
}

onUpdated(() => {
  bindWikilinkEvents()
})

onMounted(() => {
  nextTick(() => bindWikilinkEvents())
})

function escHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
</script>
