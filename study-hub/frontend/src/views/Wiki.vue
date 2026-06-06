<template>
  <div class="flex h-screen overflow-hidden bg-bg">
    <!-- 左侧边栏 -->
    <aside class="w-[260px] min-w-[260px] bg-surface border-r border-border flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-3 pb-2">
        <h2 class="text-base font-bold">🧠 Wiki 知识库</h2>
        <router-link to="/kb" class="text-[13px] text-text-secondary hover:text-accent transition-colors" title="返回文档管理">
          ← 文档
        </router-link>
      </div>

      <!-- Actions -->
      <div class="flex gap-1.5 px-3 mb-2">
        <button
          class="flex-1 text-center px-3 py-[6px] rounded-[8px] border text-[12px] whitespace-nowrap transition-all bg-accent border-accent text-white hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          :disabled="compiling"
          @click="startCompile"
        >
          {{ compiling ? '编译中…' : '⚡ 编译' }}
        </button>
        <button
          class="flex-1 text-center px-3 py-[6px] rounded-[8px] border text-[12px] whitespace-nowrap transition-all bg-surface border-warn text-warn hover:bg-warn hover:text-black disabled:opacity-40 disabled:cursor-not-allowed"
          :disabled="regenerating"
          @click="regenerateWiki"
        >
          {{ regenerating ? '重建中…' : '🔄 重建' }}
        </button>
      </div>

      <!-- Search -->
      <div class="px-3 mb-2">
        <input
          v-model="searchQuery"
          type="text"
          class="w-full px-3 py-2 bg-bg border border-border rounded-[8px] text-[13px] text-text outline-none focus:border-accent"
          placeholder="搜索 Wiki 页面…"
        />
      </div>

      <!-- Category Tree -->
      <div class="px-3 mb-1 text-[11px] text-text-secondary uppercase tracking-wider">索引</div>
      <div class="px-3 pb-2 max-h-[35%] overflow-y-auto">
        <!-- 全部 -->
        <div
          class="px-2 py-1 rounded-[6px] cursor-pointer text-[12px] transition-colors mb-0.5"
          :class="currentCat === '' ? 'bg-accent-glow text-accent' : 'text-text-secondary hover:bg-surface-hover'"
          @click="filterByCat('')"
        >
          📂 全部
        </div>

        <!-- 树形分类 -->
        <div v-for="node in categoryTree" :key="node.name" class="mb-0.5">
          <div
            class="px-2 py-1 rounded-[6px] cursor-pointer text-[12px] transition-colors flex items-center gap-1"
            :class="currentCat === node.name ? 'bg-accent-glow text-accent' : 'text-text-secondary hover:bg-surface-hover'"
            @click="filterByCat(node.name)"
          >
            <span class="text-[9px]">{{ node.children.length > 0 ? (expandedCats.has(node.name) ? '▼' : '▶') : '·' }}</span>
            <span class="truncate">{{ node.name }}</span>
            <span class="text-[10px] opacity-60 ml-auto">{{ node.count }}</span>
          </div>
          <div v-if="node.children.length > 0 && expandedCats.has(node.name)" class="ml-3 border-l border-border pl-2 mt-0.5">
            <div
              v-for="child in node.children"
              :key="child.name"
              class="px-2 py-0.5 rounded-[6px] cursor-pointer text-[11px] transition-colors mb-0.5"
              :class="currentCat === child.name ? 'bg-accent-glow text-accent' : 'text-text-secondary hover:bg-surface-hover'"
              @click.stop="filterByCat(child.name)"
            >
              <span class="truncate">{{ child.displayName || child.name }}</span>
              <span class="text-[10px] opacity-60 ml-1">{{ child.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Article List -->
      <div class="px-3 mb-1 text-[11px] text-text-secondary uppercase tracking-wider border-t border-border pt-2">
        {{ currentCat ? currentCat : '全部文章' }}
      </div>
      <div class="flex-1 overflow-y-auto px-3 pb-3">
        <div
          v-for="p in filteredPages"
          :key="p.id"
          class="px-2 py-1.5 rounded-[6px] cursor-pointer transition-colors text-[12px] mb-0.5"
          :class="currentPage && currentPage.id === p.id ? 'bg-accent-glow text-accent' : 'text-text-secondary hover:bg-surface-hover'"
          @click="openPage(p.id)"
        >
          <div class="font-medium truncate">{{ p.title }}</div>
          <div class="text-[10px] opacity-60 flex gap-2 mt-0.5">
            <span>v{{ p.version }}</span>
            <span>{{ p.char_count }}字</span>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div class="px-3 py-2 border-t border-border text-[11px] text-text-secondary flex gap-3">
        <span>页面 <b class="text-accent">{{ allPages.length }}</b></span>
        <span>链接 <b class="text-accent">{{ graphEdges.length }}</b></span>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden relative">
      <!-- Toolbar -->
      <div class="flex items-center gap-3 px-6 py-3 bg-surface border-b border-border flex-wrap">
        <h3 class="text-[15px] font-semibold mr-auto">{{ viewTitle }}</h3>
        <button
          class="px-3.5 py-1.5 bg-transparent border-none text-[13px] cursor-pointer border-b-2 transition-all"
          :class="currentTab === 'page' ? 'text-accent border-b-accent' : 'text-text-secondary hover:text-text border-b-transparent'"
          @click="switchTab('page')"
        >
          📄 页面
        </button>
        <button
          class="px-3.5 py-1.5 bg-transparent border-none text-[13px] cursor-pointer border-b-2 transition-all"
          :class="currentTab === 'graph' ? 'text-accent border-b-accent' : 'text-text-secondary hover:text-text border-b-transparent'"
          @click="switchTab('graph')"
        >
          🕸️ 知识图谱
        </button>
        <button
          class="px-3.5 py-1.5 bg-transparent border-none text-[13px] cursor-pointer border-b-2 transition-all"
          :class="currentTab === 'compile' ? 'text-accent border-b-accent' : 'text-text-secondary hover:text-text border-b-transparent'"
          @click="switchTab('compile')"
        >
          📋 编译日志
        </button>
        <span class="ml-auto"></span>
        <button
          v-if="currentTab === 'page' && currentPage"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent"
          @click="openEditModal"
        >
          ✏️ 编辑
        </button>
        <button
          v-if="currentTab === 'page' && currentPage"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent"
          @click="showMindmap = true"
        >
          🧠 思维导图
        </button>
        <button
          v-if="currentTab === 'page' && currentPage"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent"
          @click="openSlides"
        >
          📽️ 幻灯片
        </button>
        <button
          v-if="currentTab === 'page' && currentPage"
          class="px-2.5 py-1 rounded-[8px] border text-[12px] transition-all bg-surface border-border hover:bg-surface-hover hover:border-accent"
          @click="openCurrentPageInNewTab"
        >
          ↗ 新标签页打开
        </button>
      </div>

      <!-- 页面 Tab -->
      <div v-show="currentTab === 'page'" class="flex-1 overflow-hidden flex">
        <!-- 主阅读区 -->
        <div
          class="flex-1 overflow-y-auto transition-all duration-300"
          :class="previewPage ? 'px-6 py-6' : 'px-12 py-8'"
        >
          <!-- Empty -->
          <div v-if="!currentPage" class="text-center py-16 text-text-secondary">
            <div class="text-5xl mb-3">🧠</div>
            <p>LLM Wiki — AI 自动维护的结构化知识库</p>
            <p class="text-[13px] mt-2">点击左侧索引中的页面阅读内容</p>
          </div>

          <!-- Content -->
          <div v-else :class="previewPage ? 'max-w-full' : 'max-w-[800px] mx-auto'">
            <!-- Meta bar -->
            <div class="flex gap-4 flex-wrap text-[13px] text-text-secondary mb-5 pb-4 border-b border-border">
              <span v-if="currentPage.category">📂 {{ currentPage.category }}</span>
              <span>📝 v{{ currentPage.version }}</span>
              <span>📊 {{ currentPage.char_count }} 字</span>
              <span>📅 {{ (currentPage.updated_at || currentPage.created_at || '').slice(0, 10) }}</span>
              <div v-if="pageTags.length" class="flex gap-1 flex-wrap">
                <span
                  v-for="t in pageTags"
                  :key="t"
                  class="px-2.5 py-0.5 rounded-[12px] text-[11px] bg-accent-glow text-accent"
                >
                  {{ t }}
                </span>
              </div>
            </div>

            <!-- Markdown content (with cover image prepended) -->
            <div class="leading-[1.8] text-[15px]">
              <MarkdownRenderer :content="pageContentWithCover" @link-click="onLinkClick" />
            </div>

            <!-- Links section -->
            <div class="mt-8 pt-4 border-t border-border">
              <div v-if="currentPage.out_links && currentPage.out_links.length">
                <h4 class="text-sm text-text-secondary mb-2">🔗 此页面引用了</h4>
                <p class="flex flex-wrap gap-2">
                  <span
                    v-for="l in currentPage.out_links"
                    :key="l.target_page_slug"
                    class="wikilink cursor-pointer border-b border-dashed border-accent text-accent hover:text-[#a5b0ff]"
                    @click="openPageBySlug(l.target_page_slug)"
                  >
                    [[{{ l.target_page_slug }}]]
                  </span>
                </p>
              </div>
              <div v-if="currentPage.in_links && currentPage.in_links.length" class="mt-4">
                <h4 class="text-sm text-text-secondary mb-2">📎 被以下页面引用</h4>
                <p class="flex flex-wrap gap-2">
                  <span
                    v-for="l in currentPage.in_links"
                    :key="l.slug"
                    class="wikilink cursor-pointer border-b border-dashed border-accent text-accent hover:text-[#a5b0ff]"
                    @click="openPageBySlug(l.slug)"
                  >
                    {{ l.title }}
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧预览面板 -->
        <div
          v-if="previewPage"
          class="w-[420px] min-w-[420px] bg-surface border-l border-border flex flex-col overflow-hidden animate-slide-in"
        >
          <!-- Preview Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-border">
            <h4 class="text-[13px] font-semibold truncate">{{ previewPage.title }}</h4>
            <div class="flex gap-2">
              <button
                class="px-2 py-1 rounded-[6px] border text-[11px] transition-all bg-bg border-border hover:border-accent"
                @click="promotePreview"
              >
                切换为主文章
              </button>
              <button
                class="px-2 py-1 rounded-[6px] border text-[11px] transition-all bg-bg border-border hover:border-danger text-danger"
                @click="closePreview"
              >
                ✕
              </button>
            </div>
          </div>
          <!-- Preview Content -->
          <div class="flex-1 overflow-y-auto px-4 py-4">
            <div class="flex gap-3 flex-wrap text-[12px] text-text-secondary mb-3 pb-3 border-b border-border">
              <span v-if="previewPage.category">📂 {{ previewPage.category }}</span>
              <span>📝 v{{ previewPage.version }}</span>
              <span>📊 {{ previewPage.char_count }} 字</span>
            </div>
            <div class="leading-[1.7] text-[14px]">
              <MarkdownRenderer :content="previewPage.content" @link-click="onPreviewLinkClick" />
            </div>
          </div>
        </div>
      </div>

      <!-- 知识图谱 Tab -->
      <div v-show="currentTab === 'graph'" class="flex-1 overflow-hidden relative">
        <div ref="graphChartRef" class="w-full h-full"></div>
        <div class="absolute bottom-4 left-4 bg-surface border border-border rounded-[8px] px-4 py-3 text-xs text-text-secondary">
          <span class="text-accent mr-1">●</span> 节点 = Wiki 页面 &nbsp;
          <span class="text-text-secondary mr-1">—</span> 连线 = 交叉引用 &nbsp;
          拖拽移动 · 点击节点打开页面
        </div>
      </div>

      <!-- 编译日志 Tab -->
      <div v-show="currentTab === 'compile'" class="flex-1 overflow-y-auto px-6 py-4">
        <div class="max-h-full overflow-y-auto text-[13px] font-mono leading-relaxed space-y-1">
          <p v-if="compileLogs.length === 0" class="text-text-secondary">准备就绪，点击左侧「编译 Wiki」开始。</p>
          <p
            v-for="(log, i) in compileLogs"
            :key="i"
            :class="{
              'text-success': log.type === 'ok',
              'text-danger': log.type === 'err',
              'text-text-secondary': log.type === 'info'
            }"
          >
            {{ log.text }}
          </p>
        </div>
      </div>
    </main>

    <!-- Mindmap Modal -->
    <div v-if="showMindmap && currentPage" class="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center" @click.self="showMindmap = false">
      <div class="bg-surface rounded-[12px] p-4 w-[95%] max-w-[900px] h-[85vh] border border-border flex flex-col">
        <div class="flex justify-between items-center mb-3">
          <h3 class="text-base font-semibold">🧠 {{ currentPage.title }} — 思维导图</h3>
          <button @click="showMindmap = false" class="text-text-secondary hover:text-text text-xl">×</button>
        </div>
        <div ref="mindmapRef" class="flex-1 rounded-[8px] border border-border bg-bg overflow-hidden"></div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div
      v-if="editModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="closeEditModal"
    >
      <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[800px] flex flex-col gap-4 max-h-[90vh] overflow-y-auto">
        <h3 class="text-base font-semibold">编辑: {{ currentPage?.title }}</h3>
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
          <div v-if="editForm.cover_image && editForm.cover_image.startsWith('/images/')" class="mt-2">
            <img :src="resolveImageUrl(editForm.cover_image)" class="h-[80px] rounded-[6px] object-cover border border-border" />
          </div>
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
          为《{{ currentPage?.title }}》生成封面图
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

    <!-- Toast -->
    <Toast ref="toastRef" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useSettingsStore } from '../stores/settings.js'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import Toast from '../components/Toast.vue'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'
import { Marp } from '@marp-team/marp-core'

const settings = useSettingsStore()

// ====== State ======
const allPages = ref([])
const allCategories = ref([])
const currentPage = ref(null)
const previewPage = ref(null)
const currentTab = ref('page')
const searchQuery = ref('')
const searchResults = ref(null)
const isSearching = ref(false)
const currentCat = ref('')
const searchTimer = ref(null)
const expandedCats = ref(new Set())

const graphNodes = ref([])
const graphEdges = ref([])
const graphChartRef = ref(null)
let chartInstance = null

const compiling = ref(false)
const regenerating = ref(false)
const compileLogs = ref([])

const toastRef = ref(null)
const showMindmap = ref(false)
const mindmapRef = ref(null)
let mmInstance = null

// ====== Edit Modal ======
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

// ====== Computed ======
const viewTitle = computed(() => {
  if (previewPage.value && currentPage.value) {
    return `${currentPage.value.title} → ${previewPage.value.title}`
  }
  return currentPage.value ? currentPage.value.title : 'Wiki 阅读'
})

// 将标题 + 封面图插入到 Markdown 内容最前面
const pageContentWithCover = computed(() => {
  if (!currentPage.value) return ''
  const title = currentPage.value.title
    ? `# ${currentPage.value.title}\n\n`
    : ''
  const cover = currentPage.value.cover_image
    ? `![封面](${resolveImageUrl(currentPage.value.cover_image)})\n\n`
    : ''
  return title + cover + (currentPage.value.content || '')
})

function resolveImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  // /images/xxx → 后端服务 (8741)
  if (url.startsWith('/images/')) return `http://localhost:8741${url}`
  // /covers/xxx → 前端静态资源，保持原样
  return url
}



// 构建分类树（从扁平分类提取层级关系）
const categoryTree = computed(() => {
  const tree = []
  const map = new Map()

  allCategories.value.forEach(c => {
    const name = c.category
    const count = c.count

    // 尝试提取层级："AI工具/项目" → parent="AI工具", child="项目"
    // 或者 "AI-工具" → parent="AI", child="工具"
    const separators = ['/', '·', '—', '-', '：', ':']
    let parent = null
    let child = null

    for (const sep of separators) {
      if (name.includes(sep)) {
        const parts = name.split(sep)
        if (parts.length === 2) {
          parent = parts[0].trim()
          child = parts[1].trim()
          break
        }
      }
    }

    if (parent && child) {
      // 有层级关系
      if (!map.has(parent)) {
        const node = { name: parent, count: 0, children: [] }
        map.set(parent, node)
        tree.push(node)
      }
      map.get(parent).children.push({ name, count, displayName: child })
      map.get(parent).count += count
    } else {
      // 无层级关系，作为独立节点
      const node = { name, count, children: [] }
      map.set(name, node)
      tree.push(node)
    }
  })

  // 按页面数量排序
  tree.sort((a, b) => b.count - a.count)
  tree.forEach(node => {
    node.children.sort((a, b) => b.count - a.count)
  })

  return tree
})

const filteredPages = computed(() => {
  let pages = allPages.value
  if (currentCat.value) pages = pages.filter(p => p.category === currentCat.value)
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    pages = pages.filter(p =>
      p.title.toLowerCase().includes(q) ||
      (p.summary || '').toLowerCase().includes(q) ||
      (p.tags || '').toLowerCase().includes(q)
    )
  }
  return pages
})

const filteredSearchResults = computed(() => {
  if (!searchResults.value) return []
  let results = searchResults.value
  if (currentCat.value) results = results.filter(r => r.category === currentCat.value)
  return results
})

const pageTags = computed(() => safeJsonParse(currentPage.value?.tags, []))
const pageSources = computed(() => safeJsonParse(currentPage.value?.source_doc_ids, []))
const pageContradictions = computed(() => safeJsonParse(currentPage.value?.contradictions, []))

// ====== Lifecycle ======
onMounted(async () => {
  await loadPages()
  await loadCategories()
  await loadGraph()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

// ====== Data Loading ======
async function loadPages() {
  try {
    const data = await settings.apiGet('/wiki/pages')
    allPages.value = Array.isArray(data) ? data : []
  } catch (e) {
    toast('加载页面失败', true)
  }
}

async function loadCategories() {
  try {
    const data = await settings.apiGet('/wiki/categories')
    allCategories.value = Array.isArray(data) ? data : []
  } catch (e) {
    toast('加载分类失败', true)
  }
}

async function loadGraph() {
  try {
    const data = await settings.apiGet('/wiki/graph')
    graphNodes.value = data.nodes || []
    graphEdges.value = data.edges || []
  } catch (e) {
    toast('加载图谱失败', true)
  }
}

// ====== Search ======
watch(searchQuery, (val) => {
  clearTimeout(searchTimer.value)
  if (!val.trim()) {
    searchResults.value = null
    isSearching.value = false
    return
  }
  isSearching.value = true
  searchTimer.value = setTimeout(() => doSearch(val.trim()), 300)
})

async function doSearch(query) {
  try {
    const res = await settings.apiPost('/wiki/search', { query })
    searchResults.value = res.results || []
  } catch (e) {
    searchResults.value = []
  }
  isSearching.value = false
}

function filterByCat(cat) {
  if (currentCat.value === cat) {
    // 点击已选中的分类，展开/折叠
    if (expandedCats.value.has(cat)) {
      expandedCats.value.delete(cat)
    } else {
      expandedCats.value.add(cat)
    }
    return
  }
  currentCat.value = cat
}

// ====== Page Actions ======
async function openPage(id) {
  const p = allPages.value.find(x => x.id === id)
  if (!p) return
  if (p.content) {
    currentPage.value = p
    previewPage.value = null
    currentTab.value = 'page'
  } else {
    await openPageBySlug(p.slug || p.id)
  }
}

async function openPageBySlug(slug) {
  try {
    const data = await settings.apiGet(`/wiki/pages/${encodeURIComponent(slug)}`)
    if (data.error) {
      toast(data.error, true)
      return
    }
    currentPage.value = data
    previewPage.value = null
    currentTab.value = 'page'
  } catch (e) {
    toast('加载页面失败', true)
  }
}

// 点击文章内链接 → 右侧预览
async function onLinkClick(slug) {
  if (!slug) return
  try {
    const data = await settings.apiGet(`/wiki/pages/${encodeURIComponent(slug)}`)
    if (data.error) {
      toast(data.error, true)
      return
    }
    previewPage.value = data
  } catch (e) {
    toast('加载预览失败', true)
  }
}

// 预览面板内再点击链接 → 替换预览内容
async function onPreviewLinkClick(slug) {
  if (!slug) return
  try {
    const data = await settings.apiGet(`/wiki/pages/${encodeURIComponent(slug)}`)
    if (data.error) {
      toast(data.error, true)
      return
    }
    previewPage.value = data
  } catch (e) {
    toast('加载预览失败', true)
  }
}

// 将预览提升为主文章
function promotePreview() {
  if (!previewPage.value) return
  currentPage.value = previewPage.value
  previewPage.value = null
}

function closePreview() {
  previewPage.value = null
}

function openCurrentPageInNewTab() {
  if (!currentPage.value) return
  const slug = currentPage.value.slug || currentPage.value.id
  window.open(`/wiki/${encodeURIComponent(slug)}`, '_blank')
}

// ====== Edit Modal ======
function openEditModal() {
  if (!currentPage.value) return
  editForm.value = {
    title: currentPage.value.title || '',
    category: currentPage.value.category || '',
    tags: safeJsonParse(currentPage.value.tags, []).join(', '),
    content: currentPage.value.content || '',
    cover_image: currentPage.value.cover_image || ''
  }
  editModalVisible.value = true
}

function closeEditModal() {
  editModalVisible.value = false
}

async function saveEdit() {
  if (!currentPage.value) return
  const title = editForm.value.title.trim()
  const content = editForm.value.content.trim()
  if (!title || !content) { toast('标题和内容不能为空', true); return }

  const category = editForm.value.category.trim()
  const tagsStr = editForm.value.tags.trim()
  const tags = tagsStr ? tagsStr.split(/[,，]\s*/).map(t => t.trim()).filter(Boolean) : []

  try {
    const r = await settings.apiPut(`/wiki/pages/${currentPage.value.id}`, { title, content, category, tags, cover_image: editForm.value.cover_image.trim() })
    if (r.error) { toast(r.error, true); return }
    toast('保存成功')
    closeEditModal()
    // 用后端返回的新 slug 刷新页面数据
    const newSlug = r.slug || currentPage.value.slug || currentPage.value.id
    await openPageBySlug(newSlug)
    // 刷新列表（更新标题、分类等）
    await loadPages()
  } catch (e) {
    toast('保存失败', true)
  }
}

function openAIGenerateModal() {
  aiGeneratePrompt.value = ''
  aiGenerateModalVisible.value = true
}

async function generateAICover() {
  if (!currentPage.value) return
  generatingCover.value = true
  try {
    const r = await settings.apiPost('/images/generate-cover', {
      page_id: currentPage.value.id,
      title: currentPage.value.title,
      content: currentPage.value.content,
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

// ====== Compile / Regenerate ======
async function startCompile() {
  compiling.value = true
  switchTab('compile')
  compileLogs.value = [{ type: 'info', text: '⚙️ 正在编译文档为 Wiki 页面，请稍候…' }]

  try {
    const r = await settings.apiPost('/wiki/compile', {})
    if (r.status === 'no_docs') {
      compileLogs.value.push({ type: 'info', text: r.message })
    } else if (r.results) {
      for (const item of r.results) {
        if (item.error) {
          compileLogs.value.push({ type: 'err', text: `❌ [${item.doc_title}] 编译失败: ${item.error}` })
        } else {
          compileLogs.value.push({ type: 'ok', text: `✅ ${item.doc_title} → 新建 ${item.new_pages} 页, 更新 ${item.updated_pages} 页${item.contradictions > 0 ? `, ⚠️ ${item.contradictions} 处矛盾` : ''}` })
        }
      }
    }
    compileLogs.value.push({ type: 'info', text: '━━━ 编译完成 ━━━' })
  } catch (e) {
    compileLogs.value.push({ type: 'err', text: `编译失败: ${e.message}` })
  }

  compiling.value = false
  await loadPages()
  await loadGraph()
  await loadCategories()
}

async function regenerateWiki() {
  if (!confirm('确定清空所有 Wiki 页面并从零重建吗？此操作不可撤销。')) return
  regenerating.value = true
  switchTab('compile')
  compileLogs.value = [{ type: 'info', text: '🗑️ 已清空 Wiki，重新编译所有文档…' }]

  try {
    const r = await settings.apiPost('/wiki/regenerate', {})
    if (r.results) {
      for (const item of r.results) {
        if (item.error) {
          compileLogs.value.push({ type: 'err', text: `❌ [${item.doc_title}] ${item.error}` })
        } else {
          compileLogs.value.push({ type: 'ok', text: `✅ ${item.doc_title} → +${item.new_pages} 页` })
        }
      }
    }
    compileLogs.value.push({ type: 'info', text: '━━━ 重建完成 ━━━' })
  } catch (e) {
    compileLogs.value.push({ type: 'err', text: `重建失败: ${e.message}` })
  }

  regenerating.value = false
  await loadPages()
  await loadGraph()
  await loadCategories()
}

// ====== Tab Switching ======
function switchTab(tab) {
  currentTab.value = tab
  if (tab === 'graph') {
    nextTick(() => {
      renderGraph()
    })
  }
}

// ====== ECharts Graph ======
function renderGraph() {
  if (!graphChartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  chartInstance = echarts.init(graphChartRef.value)

  const nodes = graphNodes.value
  const edges = graphEdges.value
  const categories = [...new Set(nodes.map(n => n.category).filter(Boolean))]

  const option = {
    tooltip: { formatter: '{b}' },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      data: nodes.map(n => ({
        id: n.id,
        name: n.label,
        symbolSize: 5 + (n.deg || 0) * 3,
        category: categories.indexOf(n.category)
      })),
      links: edges.map(e => ({
        source: e.source,
        target: e.target,
        lineStyle: { type: e.type === 'contradiction' ? 'dashed' : 'solid' }
      })),
      force: {
        repulsion: 300,
        edgeLength: [100, 300],
        gravity: 0.1
      },
      categories: categories.map(c => ({ name: c })),
      label: {
        show: true,
        position: 'bottom',
        fontSize: 10,
        color: '#e0e0e8',
        formatter: (p) => p.name.length > 10 ? p.name.slice(0, 10) + '…' : p.name
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 2, color: '#7c8aff' }
      },
      lineStyle: {
        color: '#2a2a3a',
        width: 1,
        curveness: 0.1
      }
    }]
  }

  chartInstance.setOption(option)

  chartInstance.on('click', (params) => {
    if (params.dataType === 'node' && params.data.id) {
      openPageBySlug(params.data.id)
    }
  })

  const handleResize = () => chartInstance && chartInstance.resize()
  window.addEventListener('resize', handleResize)

  const originalDispose = chartInstance.dispose.bind(chartInstance)
  chartInstance.dispose = function () {
    window.removeEventListener('resize', handleResize)
    originalDispose()
  }
}

// ====== Utils ======
function safeJsonParse(s, def) {
  try { return JSON.parse(s) } catch { return def }
}

function toast(msg, error = false) {
  toastRef.value?.show(msg, error)
}

// ========== 思维导图 ==========
watch(showMindmap, async (visible) => {
  if (visible && currentPage.value?.content) {
    await nextTick()
    renderMindmap()
  }
})

function renderMindmap() {
  if (!mindmapRef.value || !currentPage.value?.content) return
  const transformer = new Transformer()
  const { root } = transformer.transform(currentPage.value.content)
  mindmapRef.value.innerHTML = ''
  mmInstance = Markmap.create(mindmapRef.value, null, root)
}

// ========== 幻灯片 ==========
function openSlides() {
  if (!currentPage.value?.content) return
  const marp = new Marp()
  const { html, css } = marp.render(currentPage.value.content)
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
      <title>${currentPage.value.title} — 幻灯片</title>
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

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes slide-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.animate-slide-in {
  animation: slide-in 0.2s ease-out;
}
</style>
