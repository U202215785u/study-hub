<template>
  <div class="min-h-screen bg-bg text-text">
    <!-- Header -->
    <header class="border-b border-border bg-surface">
      <div class="mx-auto max-w-5xl px-5 py-4 flex items-center gap-4">
        <router-link
          to="/wiki"
          class="text-[13px] text-text-secondary hover:text-accent transition-colors shrink-0"
        >
          ← 返回 Wiki 知识库
        </router-link>
        <div class="h-4 w-px bg-border shrink-0"></div>
        <h1 class="text-base font-semibold truncate">{{ page?.title || 'Wiki 页面' }}</h1>
        <span class="ml-auto"></span>
        <button
          v-if="page"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent shrink-0"
          @click="openEditModal"
        >
          ✏️ 编辑
        </button>
        <button
          v-if="page"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent shrink-0"
          @click="showMindmap = true"
        >
          🧠 思维导图
        </button>
        <button
          v-if="page"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent shrink-0"
          @click="openSlides"
        >
          📽️ 幻灯片
        </button>
        <button
          v-if="page"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent shrink-0"
          @click="showShareCard = true"
        >
          📤 分享
        </button>
        <button
          v-if="page"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-danger text-danger hover:bg-danger hover:text-white shrink-0"
          @click="deletePage"
        >
          删除此页
        </button>
      </div>
    </header>

    <!-- Content -->
    <main class="mx-auto max-w-5xl px-5 py-8">
      <div v-if="loading" class="text-center py-16 text-text-secondary">
        <p>加载中…</p>
      </div>

      <div v-else-if="error" class="text-center py-16 text-danger">
        <p>{{ error }}</p>
        <router-link to="/wiki" class="text-accent hover:underline text-sm mt-2 inline-block">
          返回 Wiki 知识库
        </router-link>
      </div>

      <div v-else-if="!page" class="text-center py-16 text-text-secondary">
        <p>页面不存在</p>
        <router-link to="/wiki" class="text-accent hover:underline text-sm mt-2 inline-block">
          返回 Wiki 知识库
        </router-link>
      </div>

      <div v-else class="max-w-[860px]">
        <!-- Title + Cover Image -->
        <h1 v-if="page.title" class="text-2xl font-bold mb-4">{{ page.title }}</h1>
        <div v-if="page.cover_image" class="mb-6 rounded-[12px] overflow-hidden border border-border">
          <img :src="resolveImageUrl(page.cover_image)" alt="封面" class="w-full h-[200px] object-cover" />
        </div>

        <!-- Meta bar -->
        <div class="flex gap-4 flex-wrap text-[13px] text-text-secondary mb-5 pb-4 border-b border-border">
          <span v-if="page.category">📂 {{ page.category }}</span>
          <span>📝 v{{ page.version }}</span>
          <span>📊 {{ page.char_count }} 字</span>
          <span>📅 {{ (page.updated_at || page.created_at || '').slice(0, 10) }}</span>
          <div v-if="pageTags.length" class="flex gap-1 flex-wrap">
            <span
              v-for="t in pageTags"
              :key="t"
              class="px-2.5 py-0.5 rounded-[12px] text-[11px] bg-accent-glow text-accent"
            >
              {{ t }}
            </span>
          </div>
          <span
            v-if="pageContradictions.length"
            class="inline-flex items-center gap-1 px-3 py-1 rounded-[12px] text-xs bg-warn/10 text-warn border border-warn/30"
          >
            ⚠️ {{ pageContradictions.length }} 处矛盾
          </span>
        </div>

        <!-- Markdown content -->
        <div>
          <MarkdownRenderer :content="page.content" />
        </div>

        <!-- Links section -->
        <div class="mt-8 pt-4 border-t border-border">
          <div v-if="page.out_links && page.out_links.length">
            <h4 class="text-sm text-text-secondary mb-2">🔗 此页面引用了</h4>
            <p class="flex flex-wrap gap-2">
              <a
                v-for="l in page.out_links"
                :key="l.target_page_slug"
                :href="`/wiki/${l.target_page_slug}`"
                target="_blank"
                rel="noopener noreferrer"
                class="wikilink border-b border-dashed border-accent text-accent hover:text-[#a5b0ff]"
              >
                [[{{ l.target_page_slug }}]]
              </a>
            </p>
          </div>
          <div v-if="page.in_links && page.in_links.length" class="mt-4">
            <h4 class="text-sm text-text-secondary mb-2">📎 被以下页面引用</h4>
            <p class="flex flex-wrap gap-2">
              <a
                v-for="l in page.in_links"
                :key="l.slug"
                :href="`/wiki/${l.slug}`"
                target="_blank"
                rel="noopener noreferrer"
                class="wikilink border-b border-dashed border-accent text-accent hover:text-[#a5b0ff]"
              >
                {{ l.title }}
              </a>
            </p>
          </div>
          <div v-if="pageSources.length" class="mt-4">
            <h4 class="text-sm text-text-secondary mb-2">📖 源文档 ID</h4>
            <p class="text-xs text-text-secondary">{{ pageSources.join(', ') }}</p>
          </div>
        </div>
      </div>
    </main>

    <!-- Edit Modal -->
    <div
      v-if="editModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="closeEditModal"
    >
      <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[800px] flex flex-col gap-4 max-h-[90vh] overflow-y-auto">
        <h3 class="text-base font-semibold">编辑: {{ page?.title }}</h3>
        <div class="flex gap-2.5 flex-wrap">
          <input v-model="editForm.title" type="text" placeholder="页面标题" class="flex-1 min-w-[120px] px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent" />
          <input v-model="editForm.category" type="text" placeholder="分类（可选）" class="flex-1 min-w-[120px] px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent" />
          <input v-model="editForm.tags" type="text" placeholder="标签（逗号分隔，可选）" class="flex-1 min-w-[120px] px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-sm text-text outline-none focus:border-accent" />
        </div>

        <!-- Cover Image Selector -->
        <div class="bg-bg border border-border rounded-[8px] p-3">
          <div class="text-[13px] text-text-secondary mb-2">🖼️ 封面图</div>
          <div class="flex gap-2 flex-wrap mb-2">
            <button
              v-for="cover in builtInCovers"
              :key="cover.url"
              class="relative w-[80px] h-[50px] rounded-[6px] overflow-hidden border-2 transition-all"
              :class="editForm.cover_image === cover.url ? 'border-accent' : 'border-transparent hover:border-border'"
              @click="editForm.cover_image = cover.url"
              :title="cover.name"
            >
              <img :src="resolveImageUrl(cover.url)" class="w-full h-full object-cover" />
            </button>
            <button
              class="w-[80px] h-[50px] rounded-[6px] border-2 border-dashed border-border flex items-center justify-center text-text-secondary hover:border-accent transition-all"
              :class="editForm.cover_image && !builtInCovers.some(c => c.url === editForm.cover_image) ? 'border-accent' : ''"
              @click="editForm.cover_image = ''"
              title="自定义 URL"
            >
              🔗
            </button>
            <button
              class="w-[80px] h-[50px] rounded-[6px] border-2 border-dashed border-accent/50 flex items-center justify-center text-accent hover:bg-accent/10 transition-all"
              :class="generatingCover ? 'opacity-50 cursor-not-allowed' : ''"
              :disabled="generatingCover"
              @click="openAIGenerateModal"
              title="AI 生成封面"
            >
              {{ generatingCover ? '⏳' : '✨' }}
            </button>
          </div>
          <input
            v-if="!editForm.cover_image || !builtInCovers.some(c => c.url === editForm.cover_image)"
            v-model="editForm.cover_image"
            type="text"
            placeholder="输入图片 URL，或从上方选择内置封面…"
            class="w-full px-3 py-2 bg-surface border border-border rounded-[6px] text-sm text-text outline-none focus:border-accent"
          />
        </div>

        <textarea
          v-model="editForm.content"
          placeholder="Markdown 内容…"
          class="w-full min-h-[400px] px-3.5 py-3.5 bg-bg border border-border rounded-[8px] text-sm text-text font-mono leading-relaxed outline-none resize-y focus:border-accent"
        ></textarea>
        <div class="flex gap-2.5 justify-end">
          <button class="px-3.5 py-[7px] rounded-[8px] border text-[13px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent" @click="closeEditModal">
            取消
          </button>
          <button class="px-3.5 py-[7px] rounded-[8px] border text-[13px] transition-all bg-accent border-accent text-white hover:opacity-90" @click="saveEdit">
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- AI Generate Cover Modal -->
    <div v-if="aiGenerateModalVisible" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[110]" @click.self="aiGenerateModalVisible = false">
      <div class="bg-surface border border-border rounded-[12px] p-5 w-[90%] max-w-[500px] flex flex-col gap-4">
        <h3 class="text-base font-semibold">✨ AI 生成封面</h3>
        <div class="text-[13px] text-text-secondary">
          为《{{ page?.title }}》生成封面图
        </div>
        <textarea
          v-model="aiGeneratePrompt"
          placeholder="输入提示词（可选），留空则自动根据文章内容生成..."
          class="w-full min-h-[100px] px-3 py-2 bg-bg border border-border rounded-[8px] text-sm text-text outline-none resize-y focus:border-accent"
        ></textarea>
        <div class="flex gap-2.5 justify-end">
          <button class="px-3.5 py-[7px] rounded-[8px] border text-[13px] bg-surface border-border hover:bg-surface-hover" @click="aiGenerateModalVisible = false">取消</button>
          <button
            class="px-3.5 py-[7px] rounded-[8px] border text-[13px] bg-accent border-accent text-white hover:opacity-90 disabled:opacity-40"
            :disabled="generatingCover"
            @click="generateAICover"
          >
            {{ generatingCover ? '生成中…' : '生成封面' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Mindmap Modal -->
    <div v-if="showMindmap && page" class="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center" @click.self="showMindmap = false">
      <div class="bg-surface rounded-[12px] p-4 w-[95%] max-w-[900px] h-[85vh] border border-border flex flex-col">
        <div class="flex justify-between items-center mb-3">
          <h3 class="text-base font-semibold">🧠 {{ page.title }} — 思维导图</h3>
          <button @click="showMindmap = false" class="text-text-secondary hover:text-text text-xl">×</button>
        </div>
        <div ref="mindmapRef" class="flex-1 rounded-[8px] border border-border bg-bg overflow-hidden"></div>
      </div>
    </div>

    <!-- Share Card -->
    <WikiShareCard :visible="showShareCard" :page="page" @close="showShareCard = false" />

    <!-- Toast -->
    <Toast ref="toastRef" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSettingsStore } from '../stores/settings.js'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import Toast from '../components/Toast.vue'
import WikiShareCard from '../components/WikiShareCard.vue'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'
import { Marp } from '@marp-team/marp-core'

const route = useRoute()
const router = useRouter()
const settings = useSettingsStore()

// ====== State ======
const page = ref(null)
const loading = ref(true)
const error = ref('')

const editModalVisible = ref(false)
const editForm = ref({ title: '', category: '', tags: '', content: '', cover_image: '' })

// ====== AI Generate Cover ======
const aiGenerateModalVisible = ref(false)
const aiGeneratePrompt = ref('')
const generatingCover = ref(false)

const builtInCovers = [
  { name: '抽象蓝', url: '/covers/abstract-blue.jpg' },
  { name: '紫渐变', url: '/covers/gradient-purple.jpg' },
  { name: '暖渐变', url: '/covers/warm-gradient.jpg' },
  { name: '几何', url: '/covers/geometric.jpg' },
  { name: '霓虹', url: '/covers/neon-glow.jpg' },
  { name: '山夜', url: '/covers/mountain-night.jpg' },
]

const toastRef = ref(null)
const showShareCard = ref(false)
const showMindmap = ref(false)
const mindmapRef = ref(null)
let mmInstance = null

// ====== Computed ======
const pageTags = computed(() => safeJsonParse(page.value?.tags, []))
const pageSources = computed(() => safeJsonParse(page.value?.source_doc_ids, []))
const pageContradictions = computed(() => safeJsonParse(page.value?.contradictions, []))

// ====== Lifecycle ======
onMounted(() => {
  loadPage()
})

// ====== Data Loading ======
async function loadPage() {
  const slug = route.params.slug
  if (!slug) {
    error.value = '缺少页面标识'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''

  try {
    const data = await settings.apiGet(`/wiki/pages/${encodeURIComponent(slug)}`)
    if (data.error) {
      error.value = data.error
      page.value = null
    } else {
      page.value = data
    }
  } catch (e) {
    error.value = '加载页面失败'
    page.value = null
  } finally {
    loading.value = false
  }
}

// ====== Page Actions ======
async function deletePage() {
  if (!page.value) return
  if (!confirm(`确定删除 Wiki 页面「${page.value.title}」吗？此操作不可撤销。`)) return
  try {
    const r = await settings.apiDelete(`/wiki/pages/${page.value.id}`)
    if (r.error) { toast(r.error, true); return }
    toast('已删除')
    router.push('/wiki')
  } catch (e) {
    toast('删除失败', true)
  }
}

// ====== Edit Modal ======
function openEditModal() {
  if (!page.value) return
  editForm.value = {
    title: page.value.title || '',
    category: page.value.category || '',
    tags: safeJsonParse(page.value.tags, []).join(', '),
    content: page.value.content || '',
    cover_image: page.value.cover_image || ''
  }
  editModalVisible.value = true
}

function closeEditModal() {
  editModalVisible.value = false
}

async function saveEdit() {
  if (!page.value) return
  const title = editForm.value.title.trim()
  const content = editForm.value.content.trim()
  if (!title || !content) { toast('标题和内容不能为空', true); return }

  const category = editForm.value.category.trim()
  const tagsStr = editForm.value.tags.trim()
  const tags = tagsStr ? tagsStr.split(/[,，]\s*/).map(t => t.trim()).filter(Boolean) : []

  try {
    const r = await settings.apiPut(`/wiki/pages/${page.value.id}`, { title, content, category, tags, cover_image: editForm.value.cover_image.trim() })
    if (r.error) { toast(r.error, true); return }
    toast('保存成功')
    closeEditModal()
    if (r.slug && r.slug !== route.params.slug) {
      router.replace(`/wiki/${r.slug}`)
    } else {
      await loadPage()
    }
  } catch (e) {
    toast('保存失败', true)
  }
}

function openAIGenerateModal() {
  aiGeneratePrompt.value = ''
  aiGenerateModalVisible.value = true
}

async function generateAICover() {
  if (!page.value) return
  generatingCover.value = true
  try {
    const r = await settings.apiPost('/images/generate-cover', {
      page_id: page.value.id,
      title: page.value.title,
      content: page.value.content,
      prompt: aiGeneratePrompt.value.trim()
    })
    if (r.error) {
      toast(r.error, true)
    } else {
      editForm.value.cover_image = r.url
      toast('封面生成成功')
      aiGenerateModalVisible.value = false
    }
  } catch (e) {
    toast('生成失败', true)
  } finally {
    generatingCover.value = false
  }
}

// ====== Utils ======
function safeJsonParse(s, def) {
  try { return JSON.parse(s) } catch { return def }
}

function resolveImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  if (url.startsWith('/images/')) return `${window.location.origin}${url}`
  return url
}

function toast(msg, error = false) {
  toastRef.value?.show(msg, error)
}

// ========== 思维导图 ==========
watch(showMindmap, async (visible) => {
  if (visible && page.value?.content) {
    await nextTick()
    renderMindmap()
  }
})

function renderMindmap() {
  if (!mindmapRef.value || !page.value?.content) return
  const transformer = new Transformer()
  const { root } = transformer.transform(page.value.content)
  mindmapRef.value.innerHTML = ''
  mmInstance = Markmap.create(mindmapRef.value, null, root)
}

// ========== 幻灯片 ==========
function openSlides() {
  if (!page.value?.content) return
  const marp = new Marp()
  const { html, css } = marp.render(page.value.content)
  const slideWindow = window.open('', '_blank', 'width=1200,height=800')
  if (!slideWindow) {
    toast('弹窗被拦截，请允许弹窗', true)
    return
  }
  slideWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${page.value.title} — 幻灯片</title>
      <style>${css}</style>
      <style>
        body { margin: 0; background: #222; }
        .marpit { display: flex; flex-direction: column; align-items: center; padding: 20px; gap: 20px; }
        section { box-shadow: 0 4px 20px rgba(0,0,0,0.5); border-radius: 8px; }
      </style>
    </head>
    <body>
      <div class="marpit">${html}</div>
      <script>
        document.addEventListener('keydown', (e) => {
          if (e.key === 'Escape') window.close();
        });
      <\/script>
    </body>
    </html>
  `)
  slideWindow.document.close()
}
</script>
