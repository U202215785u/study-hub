<template>
  <div class="flex h-screen overflow-hidden">
    <!-- 左侧边栏 -->
    <aside class="w-[260px] min-w-[260px] bg-surface border-r border-border flex flex-col p-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base font-bold">知识库管理</h2>
        <div class="flex items-center gap-2">
          <button
            class="px-2.5 py-[3px] text-[11px] rounded-[12px] border border-border bg-transparent text-text-secondary cursor-pointer transition-all whitespace-nowrap hover:border-accent hover:text-accent"
            :class="{ 'bg-accent border-accent text-white': sidebarEditing }"
            @click="toggleEditMode"
          >
            {{ sidebarEditing ? '完成' : '编辑' }}
          </button>
          <router-link to="/" class="text-[13px] text-text-secondary hover:text-accent transition-colors no-underline">
            ← 仪表盘
          </router-link>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto flex flex-col gap-1">
        <div
          class="flex items-center gap-2 px-3 py-2.5 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentCatId === null ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="selectCategory(null)"
        >
          <span class="text-lg">📚</span>
          <span class="flex-1">全部文档</span>
          <span class="text-text-secondary text-xs">{{ allDocCount }}</span>
        </div>

        <div
          v-for="cat in categories"
          :key="cat.id"
          class="flex items-center gap-2 px-3 py-2.5 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentCatId === cat.id ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="selectCategory(cat.id)"
        >
          <span class="text-lg">{{ cat.icon || '📁' }}</span>
          <span class="flex-1">{{ cat.name }}</span>
          <span class="text-text-secondary text-xs">{{ cat.doc_count || 0 }}</span>
          <div v-if="sidebarEditing" class="flex gap-1">
            <button
              class="w-6 h-6 rounded-full border-none flex items-center justify-center text-xs bg-white/[0.06] text-text-secondary hover:bg-accent hover:text-white cursor-pointer"
              title="编辑"
              @click.stop="openCatModal(cat.id)"
            >
              ✎
            </button>
            <button
              class="w-6 h-6 rounded-full border-none flex items-center justify-center text-xs bg-white/[0.06] text-text-secondary hover:bg-danger hover:text-white cursor-pointer"
              title="删除"
              @click.stop="deleteCat(cat.id)"
            >
              ×
            </button>
          </div>
        </div>

        <div
          class="flex items-center gap-2 px-3 py-2.5 rounded-[8px] cursor-pointer transition-colors text-sm"
          :class="currentCatId === 0 ? 'bg-accent-glow border border-accent' : 'hover:bg-surface-hover'"
          @click="selectCategory(0)"
        >
          <span class="text-lg">📭</span>
          <span class="flex-1">未分类</span>
        </div>
      </div>

      <div
        class="flex items-center gap-1.5 px-3 py-2.5 rounded-[8px] cursor-pointer text-[13px] text-text-secondary border border-dashed border-border mt-2 transition-colors hover:bg-surface-hover hover:text-accent hover:border-accent"
        @click="openCatModal()"
      >
        + 新建分类
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- 标题栏 -->
      <div class="flex items-center gap-3 px-6 py-4 bg-surface border-b border-border flex-wrap">
        <h3 class="text-[15px] font-semibold mr-auto">{{ currentTitle }}</h3>
        <span class="text-text-secondary text-[13px]">{{ filteredDocs.length }} 篇文档</span>
        <select
          v-model="docSort"
          @change="loadDocuments"
          class="px-2.5 py-1.5 bg-bg border border-border rounded-[8px] text-text text-[12px] outline-none cursor-pointer focus:border-accent"
        >
          <option value="created_at:desc">最新优先</option>
          <option value="created_at:asc">最早优先</option>
          <option value="title:asc">标题 A-Z</option>
          <option value="title:desc">标题 Z-A</option>
        </select>
        <input
          v-model="searchTerm"
          type="text"
          placeholder="搜索文档标题…"
          class="px-3.5 py-2 bg-bg border border-border rounded-[8px] text-text text-[13px] outline-none w-[200px] focus:border-accent"
        >
        <button
          class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors whitespace-nowrap hover:bg-surface-hover hover:border-accent"
          @click="fileInput?.click()"
        >
          上传文档
        </button>
        <input
          ref="fileInput"
          type="file"
          accept=".txt,.md,.pdf"
          multiple
          class="hidden"
          @change="handleUpload"
        >
        <button
          class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors whitespace-nowrap hover:bg-surface-hover hover:border-accent"
          @click="openPasteModal"
        >
          粘贴文本
        </button>
        <button
          v-if="selectedDocs.size > 0"
          class="px-3.5 py-[7px] rounded-[8px] border border-danger text-danger text-[13px] cursor-pointer transition-colors whitespace-nowrap hover:bg-danger hover:text-white"
          @click="batchDelete"
        >
          批量删除
        </button>
      </div>

      <!-- 文档表格 -->
      <div class="flex-1 overflow-y-auto px-6 py-4">
        <!-- 批量操作栏 -->
        <div
          v-if="selectedDocs.size > 0"
          class="flex items-center gap-2.5 px-4 py-2.5 bg-accent-glow border border-accent rounded-[8px] mb-3"
        >
          <span class="text-[13px] mr-2">已选 {{ selectedDocs.size }} 项</span>
          <select
            v-model="batchMoveTarget"
            class="px-2.5 py-1 text-[12px] rounded-[8px] border border-border bg-surface text-text outline-none focus:border-accent"
          >
            <option value="">移动到…</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">
              {{ c.icon }} {{ c.name }}
            </option>
          </select>
          <button
            class="px-2.5 py-1 text-[12px] rounded-[8px] border border-border bg-surface text-text cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent disabled:opacity-40 disabled:cursor-not-allowed"
            :disabled="!batchMoveTarget"
            @click="batchMove"
          >
            移动
          </button>
          <button
            class="px-2.5 py-1 text-[12px] rounded-[8px] border border-border bg-surface text-text cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="clearSelection"
          >
            取消选择
          </button>
        </div>

        <table class="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th class="w-9 text-left px-3 py-2.5 border-b border-border text-text-secondary font-semibold text-xs uppercase sticky top-0 bg-bg">
                <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll">
              </th>
              <th class="text-left px-3 py-2.5 border-b border-border text-text-secondary font-semibold text-xs uppercase sticky top-0 bg-bg">文档标题</th>
              <th class="w-[100px] text-left px-3 py-2.5 border-b border-border text-text-secondary font-semibold text-xs uppercase sticky top-0 bg-bg">分类</th>
              <th class="w-[180px] text-left px-3 py-2.5 border-b border-border text-text-secondary font-semibold text-xs uppercase sticky top-0 bg-bg">标签</th>
              <th class="w-[100px] text-left px-3 py-2.5 border-b border-border text-text-secondary font-semibold text-xs uppercase sticky top-0 bg-bg">信息</th>
              <th class="w-[120px] text-left px-3 py-2.5 border-b border-border text-text-secondary font-semibold text-xs uppercase sticky top-0 bg-bg">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="doc in filteredDocs"
              :key="doc.id"
              class="hover:bg-surface-hover transition-colors"
            >
              <td class="px-3 py-2.5 border-b border-border">
                <input
                  type="checkbox"
                  :checked="selectedDocs.has(doc.id)"
                  @change="toggleDoc(doc.id)"
                >
              </td>
              <td class="px-3 py-2.5 border-b border-border">
                <span
                  class="text-text font-medium cursor-pointer hover:text-accent transition-colors"
                  @click="viewDoc(doc.id)"
                >
                  {{ doc.title }}
                </span>
              </td>
              <td class="px-3 py-2.5 border-b border-border">
                <span
                  v-if="doc.category_name"
                  class="inline-flex items-center gap-1 px-2 py-[3px] rounded-[12px] text-[11px] bg-surface border border-border"
                >
                  {{ doc.category_icon || '📁' }} {{ doc.category_name }}
                </span>
                <span v-else class="text-text-secondary text-xs">未分类</span>
              </td>
              <td class="px-3 py-2.5 border-b border-border">
                <template v-if="docTags(doc.tags).length">
                  <span
                    v-for="tag in docTags(doc.tags)"
                    :key="tag"
                    class="inline-block px-2 py-0.5 rounded-[10px] text-[11px] bg-accent-glow text-accent mx-0.5"
                  >
                    {{ tag }}
                  </span>
                </template>
                <span v-else class="text-text-secondary text-xs">-</span>
              </td>
              <td class="px-3 py-2.5 border-b border-border text-text-secondary text-xs">
                {{ doc.char_count || 0 }}字<br>{{ formatDate(doc.created_at) }}
              </td>
              <td class="px-3 py-2.5 border-b border-border">
                <div class="flex gap-1">
                  <!-- ASR 失败：重新识别按钮 -->
                  <button
                    v-if="doc.asr_failed"
                    class="px-2 py-1 text-[11px] rounded-[6px] border border-danger bg-danger/10 text-danger cursor-pointer transition-colors hover:bg-danger hover:text-white whitespace-nowrap"
                    title="重新识别（ASR 失败）"
                    @click="reparseDoc(doc.id)"
                  >
                    🔄 重识
                  </button>
                  <button
                    class="px-2.5 py-1 text-[12px] rounded-[8px] border border-border bg-surface text-text cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
                    title="移动"
                    @click="moveDocPrompt(doc.id)"
                  >
                    移
                  </button>
                  <button
                    class="px-2.5 py-1 text-[12px] rounded-[8px] border border-border bg-surface text-text cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
                    title="标签"
                    @click="editTags(doc.id)"
                  >
                    标
                  </button>
                  <button
                    class="px-2.5 py-1 text-[12px] rounded-[8px] border border-border bg-surface text-danger cursor-pointer transition-colors hover:bg-danger hover:text-white"
                    title="删除"
                    @click="deleteDoc(doc.id)"
                  >
                    删
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 空状态 -->
        <div v-if="!filteredDocs.length" class="text-center py-[60px] text-text-secondary">
          <div class="text-5xl mb-3">📄</div>
          <p>暂无文档。上传文档或粘贴文本开始构建知识库。</p>
        </div>
      </div>
    </main>

    <!-- 分类弹窗 -->
    <div
      v-if="catModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="catModalVisible = false"
    >
      <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[480px] flex flex-col gap-4">
        <h3 class="text-base font-semibold">{{ editingCatId ? '编辑分类' : '新建分类' }}</h3>
        <input
          v-model="catForm.name"
          type="text"
          placeholder="分类名称"
          class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
        >
        <div>
          <span class="text-xs text-text-secondary">图标</span>
          <input
            v-model="catForm.icon"
            type="text"
            maxlength="2"
            class="ml-2 px-3 py-2 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent w-[60px]"
          >
        </div>
        <div>
          <span class="text-xs text-text-secondary">颜色</span>
          <div class="flex gap-1.5 flex-wrap mt-1">
            <div
              v-for="c in COLORS"
              :key="c"
              class="w-6 h-6 rounded-full cursor-pointer border-2 transition-all"
              :class="catForm.color === c ? 'border-white shadow-[0_0_8px_rgba(255,255,255,0.3)]' : 'border-transparent'"
              :style="{ background: c }"
              @click="catForm.color = c"
            />
          </div>
        </div>
        <div>
          <span class="text-xs text-text-secondary">关联标签</span>
          <div class="mt-1.5">
            <div v-if="allTags.length === 0" class="text-text-secondary text-xs py-1">
              暂无标签，上传文档后将自动识别
            </div>
            <div v-else class="flex flex-wrap gap-1.5">
              <span
                v-for="tag in allTags"
                :key="tag"
                class="inline-block px-2 py-0.5 rounded-[10px] text-[11px] cursor-pointer transition-colors border"
                :class="(catForm.tag_rules || []).includes(tag) ? 'bg-accent-glow text-accent border-accent' : 'bg-surface text-text-secondary border-border hover:border-accent hover:text-accent'"
                @click="toggleCatTag(tag)"
              >
                {{ tag }}
              </span>
            </div>
          </div>
        </div>
        <div class="flex gap-2.5 justify-end">
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="catModalVisible = false"
          >
            取消
          </button>
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-accent bg-accent text-white text-[13px] cursor-pointer transition-opacity hover:opacity-90"
            @click="saveCategory"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- 文档内容弹窗 -->
    <div
      v-if="docModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="docModalVisible = false"
    >
      <div class="bg-surface border border-border rounded-[12px] p-5 w-[92%] md:w-[88%] max-w-[1200px] flex flex-col gap-4 max-h-[90vh]">
        <h3 class="text-base font-semibold shrink-0">{{ currentDoc?.title }}</h3>
        <div class="overflow-y-auto bg-bg p-5 rounded-[8px] flex-1 min-h-0">
          <MarkdownRenderer v-if="currentDoc" :content="currentDoc.content || ''" />
        </div>
        <div class="flex gap-2.5 justify-end shrink-0">
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="copyAndOpenClaude"
          >
            复制全文 & 打开 Claude
          </button>
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="docModalVisible = false"
          >
            关闭
          </button>
        </div>
      </div>
    </div>

    <!-- 移动分组弹窗 -->
    <div
      v-if="moveModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="moveModalVisible = false"
    >
      <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[480px] flex flex-col gap-4">
        <h3 class="text-base font-semibold">移动分组</h3>

        <!-- 快捷标签建分组 -->
        <div v-if="moveCurrentDocTags.length > 0">
          <span class="text-xs text-text-secondary">基于标签快捷建分组</span>
          <div class="flex flex-wrap gap-1.5 mt-1.5">
            <button
              v-for="tag in moveCurrentDocTags"
              :key="tag"
              class="px-2 py-0.5 rounded-[10px] text-[11px] border border-dashed border-accent text-accent cursor-pointer transition-colors hover:bg-accent-glow"
              @click="quickCreateCatFromTag(tag)"
            >
              + {{ tag }}
            </button>
          </div>
        </div>

        <!-- 选择已有分组 -->
        <div>
          <span class="text-xs text-text-secondary">选择分组</span>
          <select
            v-model="moveTargetCategory"
            class="mt-1.5 w-full px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
          >
            <option value="">未分类</option>
            <option
              v-for="c in categories"
              :key="c.id"
              :value="c.id"
              :disabled="c.id === moveCurrentDoc?.category_id"
            >
              {{ c.icon }} {{ c.name }} {{ c.id === moveCurrentDoc?.category_id ? '(当前)' : '' }}
            </option>
          </select>
        </div>

        <!-- 新建分组 -->
        <div class="border-t border-border pt-3">
          <span class="text-xs text-text-secondary">或新建分组</span>
          <div class="flex gap-2 mt-1.5">
            <input
              v-model="moveNewCatName"
              type="text"
              placeholder="分组名称"
              class="flex-1 px-3 py-2 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
            >
            <button
              class="px-3 py-[6px] rounded-[8px] border border-accent bg-accent text-white text-[13px] cursor-pointer transition-opacity hover:opacity-90 whitespace-nowrap"
              :disabled="!moveNewCatName.trim()"
              @click="createAndMove"
            >
              创建并移动
            </button>
          </div>
        </div>

        <div class="flex gap-2.5 justify-end">
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="moveModalVisible = false"
          >
            取消
          </button>
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-accent bg-accent text-white text-[13px] cursor-pointer transition-opacity hover:opacity-90"
            :disabled="!moveTargetCategory && !moveNewCatName.trim()"
            @click="confirmMove"
          >
            移动
          </button>
        </div>
      </div>
    </div>

    <!-- 标签编辑弹窗 -->
    <div
      v-if="tagModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="tagModalVisible = false"
    >
      <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[480px] flex flex-col gap-4">
        <h3 class="text-base font-semibold">编辑标签</h3>
        <button
          class="px-3 py-[6px] rounded-[8px] border border-dashed border-accent text-accent text-[13px] cursor-pointer transition-colors hover:bg-accent-glow self-start flex items-center gap-1"
          :disabled="autoTagLoading"
          @click="autoTag"
        >
          <span v-if="autoTagLoading" class="inline-block w-3.5 h-3.5 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
          {{ autoTagLoading ? '识别中…' : '🪄 AI 识别标签' }}
        </button>
        <div class="flex flex-wrap gap-1.5 items-center min-h-[28px]">
          <span
            v-for="(t, i) in editingTags"
            :key="i"
            class="inline-block px-2 py-0.5 rounded-[10px] text-[11px] bg-accent-glow text-accent"
          >
            {{ t }}
            <span class="cursor-pointer opacity-50 text-[10px] hover:opacity-100 hover:text-danger ml-0.5" @click="removeTag(i)">×</span>
          </span>
          <span v-if="!editingTags.length" class="text-text-secondary text-xs">暂无标签</span>
        </div>
        <input
          v-model="newTagInput"
          type="text"
          placeholder="输入新标签，回车添加"
          class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
          @keydown.enter.prevent="addNewTag"
        >
        <div class="flex gap-2.5 justify-end">
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="tagModalVisible = false"
          >
            取消
          </button>
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-accent bg-accent text-white text-[13px] cursor-pointer transition-opacity hover:opacity-90"
            @click="saveTags"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- 粘贴文本弹窗 -->
    <div
      v-if="pasteModalVisible"
      class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]"
      @click.self="pasteModalVisible = false"
    >
      <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[600px] flex flex-col gap-4">
        <h3 class="text-base font-semibold">粘贴文本到知识库</h3>
        <input
          v-model="pasteForm.title"
          type="text"
          placeholder="文档标题"
          class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
        >
        <textarea
          v-model="pasteForm.content"
          placeholder="粘贴文本内容…"
          class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent resize-y min-h-[200px] font-[inherit]"
        />
        <select
          v-model="pasteForm.category_id"
          class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent"
        >
          <option value="">无分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">
            {{ c.icon }} {{ c.name }}
          </option>
        </select>
        <div class="flex gap-2.5 justify-end">
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer transition-colors hover:bg-surface-hover hover:border-accent"
            @click="pasteModalVisible = false"
          >
            取消
          </button>
          <button
            class="px-3.5 py-[7px] rounded-[8px] border border-accent bg-accent text-white text-[13px] cursor-pointer transition-opacity hover:opacity-90"
            @click="savePaste"
          >
            存入知识库
          </button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div
      v-if="toastVisible"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 px-5 py-2.5 rounded-[8px] text-sm border z-[200] transition-opacity duration-300"
      :class="toastIsError ? 'border-danger text-danger' : 'border-border text-text bg-surface'"
    >
      {{ toastMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '../stores/settings.js'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const settings = useSettingsStore()

// ===== 常量 =====
const COLORS = ['#7c8aff', '#4ade80', '#f59e0b', '#ef4444', '#ec4899', '#8b5cf6', '#06b6d4', '#f97316']

// ===== 状态 =====
const categories = ref([])
const documents = ref([])
const currentCatId = ref(null)
const selectedDocs = ref(new Set())
const sidebarEditing = ref(false)
const searchTerm = ref('')
const batchMoveTarget = ref('')
const fileInput = ref(null)
const docSort = ref('created_at:desc')

// 弹窗状态
const catModalVisible = ref(false)
const editingCatId = ref(null)
const catForm = ref({ name: '', icon: '📁', color: '#7c8aff', tag_rules: [] })

const docModalVisible = ref(false)
const currentDoc = ref(null)

const tagModalVisible = ref(false)
const editingTagDocId = ref(null)
const editingTags = ref([])
const newTagInput = ref('')
const autoTagLoading = ref(false)

const moveModalVisible = ref(false)
const moveCurrentDoc = ref(null)
const moveTargetCategory = ref('')
const moveNewCatName = ref('')

const pasteModalVisible = ref(false)
const pasteForm = ref({ title: '', content: '', category_id: '' })

// Toast
const toastVisible = ref(false)
const toastMsg = ref('')
const toastIsError = ref(false)
let toastTimer = null

// ===== 计算属性 =====
const currentTitle = computed(() => {
  if (currentCatId.value === null) return '全部文档'
  if (currentCatId.value === 0) return '未分类'
  return categories.value.find(c => c.id === currentCatId.value)?.name || '全部文档'
})

const allDocCount = computed(() => {
  return documents.value.length
})

const allTags = computed(() => {
  const tagSet = new Set()
  documents.value.forEach(doc => {
    docTags(doc.tags).forEach(t => tagSet.add(t))
  })
  return Array.from(tagSet).sort()
})

const filteredDocs = computed(() => {
  let list = documents.value
  if (searchTerm.value) {
    const term = searchTerm.value.toLowerCase()
    list = list.filter(d => (d.title || '').toLowerCase().includes(term))
  }
  return list
})

const isAllSelected = computed(() => {
  if (!filteredDocs.value.length) return false
  return filteredDocs.value.every(d => selectedDocs.value.has(d.id))
})

// ===== 帮助函数 =====
function toast(msg, isError = false) {
  toastMsg.value = msg
  toastIsError.value = isError
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2500)
}

function docTags(tagsStr) {
  try {
    return JSON.parse(tagsStr || '[]')
  } catch {
    return []
  }
}

function formatDate(dateStr) {
  return (dateStr || '').slice(0, 10)
}

// ===== 数据加载 =====
async function loadCategories() {
  try {
    categories.value = await settings.apiGet('/categories')
  } catch {
    categories.value = []
  }
}

async function loadDocuments() {
  try {
    const params = new URLSearchParams()
    if (currentCatId.value !== null) params.append('category_id', String(currentCatId.value))
    const [sortBy, sortOrder] = docSort.value.split(':')
    params.append('sort_by', sortBy)
    params.append('sort_order', sortOrder)
    const path = '/documents?' + params.toString()
    documents.value = await settings.apiGet(path)
  } catch {
    documents.value = []
  }
}

// ===== 分类操作 =====
function toggleEditMode() {
  sidebarEditing.value = !sidebarEditing.value
}

function selectCategory(catId) {
  currentCatId.value = catId
  selectedDocs.value.clear()
  batchMoveTarget.value = ''
  loadDocuments()
}

function openCatModal(catId) {
  editingCatId.value = catId || null
  if (catId) {
    const cat = categories.value.find(c => c.id === catId)
    if (!cat) return
    const rules = cat.tag_rules
      ? (typeof cat.tag_rules === 'string' ? JSON.parse(cat.tag_rules) : cat.tag_rules)
      : []
    catForm.value = { name: cat.name, icon: cat.icon, color: cat.color, tag_rules: rules }
  } else {
    catForm.value = { name: '', icon: '📁', color: '#7c8aff', tag_rules: [] }
  }
  catModalVisible.value = true
}

function toggleCatTag(tag) {
  const rules = catForm.value.tag_rules || []
  const idx = rules.indexOf(tag)
  if (idx >= 0) {
    rules.splice(idx, 1)
  } else {
    rules.push(tag)
  }
  catForm.value.tag_rules = [...rules]
}

async function saveCategory() {
  const name = catForm.value.name.trim()
  if (!name) { toast('请输入分类名称', true); return }
  const icon = catForm.value.icon || '📁'
  const color = catForm.value.color
  const tag_rules = catForm.value.tag_rules || []

  try {
    let res
    if (editingCatId.value) {
      res = await settings.apiPut(`/categories/${editingCatId.value}`, { name, icon, color, tag_rules })
    } else {
      res = await settings.apiPost('/categories', { name, icon, color, tag_rules })
    }
    if (res.error) { toast(res.error, true); return }
    toast(editingCatId.value ? '分类已更新' : '分类已创建')
    catModalVisible.value = false
    editingCatId.value = null
    await loadCategories()
  } catch {
    toast('操作失败', true)
  }
}

async function deleteCat(catId) {
  const cat = categories.value.find(c => c.id === catId)
  if (!cat) return
  if (!confirm(`删除分类 "${cat.name}"？文档不会被删除，会变为未分类。`)) return
  try {
    await settings.apiDelete(`/categories/${catId}`)
    toast('分类已删除')
    if (currentCatId.value === catId) selectCategory(null)
    else await loadCategories()
  } catch {
    toast('删除失败', true)
  }
}

// ===== 选择逻辑 =====
function toggleDoc(id) {
  if (selectedDocs.value.has(id)) selectedDocs.value.delete(id)
  else selectedDocs.value.add(id)
}

function toggleSelectAll() {
  const checked = !isAllSelected.value
  if (checked) {
    filteredDocs.value.forEach(d => selectedDocs.value.add(d.id))
  } else {
    filteredDocs.value.forEach(d => selectedDocs.value.delete(d.id))
  }
}

function clearSelection() {
  selectedDocs.value.clear()
  batchMoveTarget.value = ''
}

// ===== 批量操作 =====
async function batchMove() {
  const catId = batchMoveTarget.value
  if (!catId) return
  try {
    await settings.apiPut('/documents/batch-move', {
      doc_ids: [...selectedDocs.value],
      category_id: parseInt(catId)
    })
    toast(`已移动 ${selectedDocs.value.size} 篇文档`)
    clearSelection()
    await loadCategories()
    await loadDocuments()
  } catch {
    toast('移动失败', true)
  }
}

async function batchDelete() {
  if (!confirm(`确认删除 ${selectedDocs.value.size} 篇文档？此操作不可恢复。`)) return
  try {
    const data = await settings.apiPost('/documents/batch-delete', { doc_ids: [...selectedDocs.value] })
    toast(`已删除 ${data.count || selectedDocs.value.size} 篇文档`)
    clearSelection()
    await loadCategories()
    await loadDocuments()
  } catch {
    toast('批量删除失败', true)
  }
}

const moveCurrentDocTags = computed(() => {
  if (!moveCurrentDoc.value) return []
  return docTags(moveCurrentDoc.value.tags)
})

function moveDocPrompt(docId) {
  const doc = documents.value.find(d => d.id === docId)
  if (!doc) return
  moveCurrentDoc.value = doc
  moveTargetCategory.value = doc.category_id || ''
  moveNewCatName.value = ''
  moveModalVisible.value = true
}

async function quickCreateCatFromTag(tag) {
  try {
    const res = await settings.apiPost('/categories', {
      name: tag,
      icon: '🏷️',
      color: '#7c8aff',
      tag_rules: [tag]
    })
    if (res.error) { toast(res.error, true); return }
    toast(`分组 "${tag}" 已创建`)
    await loadCategories()
    moveTargetCategory.value = String(res.id)
  } catch {
    toast('创建分组失败', true)
  }
}

async function createAndMove() {
  const name = moveNewCatName.value.trim()
  if (!name) return
  try {
    const res = await settings.apiPost('/categories', {
      name,
      icon: '📁',
      color: '#7c8aff'
    })
    if (res.error) { toast(res.error, true); return }
    toast(`分组 "${name}" 已创建`)
    await loadCategories()
    moveTargetCategory.value = String(res.id)
    moveNewCatName.value = ''
  } catch {
    toast('创建分组失败', true)
  }
}

async function confirmMove() {
  if (!moveCurrentDoc.value) return
  const docId = moveCurrentDoc.value.id
  const targetId = moveTargetCategory.value
  try {
    const body = { category_id: targetId === '' ? null : parseInt(targetId) }
    const data = await settings.apiPut(`/documents/${docId}/move`, body)
    if (data.error) { toast(data.error, true); return }
    toast(targetId === '' ? '已移除分类' : `已移动到 ${data.category_name}`)
    moveModalVisible.value = false
    moveCurrentDoc.value = null
    moveTargetCategory.value = ''
    moveNewCatName.value = ''
    await loadCategories()
    await loadDocuments()
  } catch {
    toast('移动失败', true)
  }
}

async function deleteDoc(docId) {
  const doc = documents.value.find(d => d.id === docId)
  if (!doc) return
  if (!confirm(`确认删除 "${doc.title}"？`)) return
  try {
    await settings.apiDelete(`/documents/${docId}`)
    toast('已删除')
    if (selectedDocs.value.has(docId)) selectedDocs.value.delete(docId)
    await loadCategories()
    await loadDocuments()
  } catch {
    toast('删除失败', true)
  }
}

// ===== 重新识别（ASR 失败文档）=====
async function reparseDoc(docId) {
  const doc = documents.value.find(d => d.id === docId)
  if (!doc) return
  if (!confirm(`重新识别 "${doc.title}"？\n将删除旧文档并重新提取语音文本。`)) return
  try {
    const data = await settings.apiPost(`/automation/reparse/${docId}`)
    if (data.error) {
      toast(data.error, true)
    } else {
      toast('已重新提交识别任务')
      await loadDocuments()
    }
  } catch {
    toast('重新识别失败', true)
  }
}

// ===== 文档查看 =====
async function viewDoc(id) {
  try {
    currentDoc.value = await settings.apiGet(`/documents/${id}`)
    docModalVisible.value = true
  } catch {
    toast('加载文档失败', true)
  }
}

async function copyAndOpenClaude() {
  if (!currentDoc.value) return
  try {
    await navigator.clipboard.writeText(currentDoc.value.content || '')
    window.open('https://claude.ai', '_blank')
    toast('内容已复制，请粘贴到 Claude')
  } catch {
    toast('复制失败', true)
  }
}

// ===== 标签编辑 =====
function editTags(docId) {
  editingTagDocId.value = docId
  const doc = documents.value.find(d => d.id === docId)
  if (!doc) return
  editingTags.value = docTags(doc.tags)
  newTagInput.value = ''
  tagModalVisible.value = true
}

function removeTag(idx) {
  editingTags.value.splice(idx, 1)
}

function addNewTag() {
  const val = newTagInput.value.trim()
  if (val && !editingTags.value.includes(val)) {
    editingTags.value.push(val)
    newTagInput.value = ''
  }
}

async function autoTag() {
  if (editingTagDocId.value === null || autoTagLoading.value) return
  autoTagLoading.value = true
  try {
    const data = await settings.apiPost(`/documents/${editingTagDocId.value}/auto-tags`)
    if (data.error) {
      toast(data.error, true)
    } else if (data.tags && data.tags.length) {
      // 只添加当前不存在的标签
      const existing = new Set(editingTags.value)
      const newTags = data.tags.filter(t => !existing.has(t))
      if (newTags.length) {
        editingTags.value.push(...newTags)
        toast(`识别到 ${newTags.length} 个新标签`)
      } else {
        toast('识别的标签都已存在')
      }
    } else {
      toast('未识别到标签')
    }
  } catch {
    toast('识别失败', true)
  } finally {
    autoTagLoading.value = false
  }
}

async function saveTags() {
  if (editingTagDocId.value === null) return
  try {
    await settings.apiPut(`/documents/${editingTagDocId.value}/tags`, { tags: editingTags.value })
    toast('标签已保存')
    tagModalVisible.value = false
    await loadDocuments()
  } catch {
    toast('保存失败', true)
  }
}

// ===== 上传 =====
async function handleUpload(event) {
  const files = event.target.files
  if (!files.length) return
  for (const file of files) {
    try {
      const form = new FormData()
      form.append('file', file)
      if (currentCatId.value !== null && currentCatId.value !== 0) {
        form.append('category_id', currentCatId.value)
      }
      const data = await settings.apiUpload('/upload', form)
      if (data.id) toast(`"${file.name}" 上传成功`)
      else toast(`上传失败: ${data.detail || data.error}`, true)
    } catch {
      toast(`上传 "${file.name}" 失败`, true)
    }
  }
  event.target.value = ''
  await loadCategories()
  await loadDocuments()
}

// ===== 粘贴文本 =====
function openPasteModal() {
  pasteForm.value = {
    title: '',
    content: '',
    category_id: currentCatId.value && currentCatId.value !== 0 ? currentCatId.value : ''
  }
  pasteModalVisible.value = true
}

async function savePaste() {
  const title = pasteForm.value.title.trim()
  const content = pasteForm.value.content.trim()
  if (!title || !content) { toast('请填写标题和内容', true); return }
  const catId = pasteForm.value.category_id
  try {
    const data = await settings.apiPost('/upload/text', {
      title,
      content,
      source: 'paste',
      category_id: catId ? parseInt(catId) : null
    })
    if (data.id) {
      toast('已存入知识库')
      pasteModalVisible.value = false
      await loadCategories()
      await loadDocuments()
    } else {
      toast('失败: ' + (data.error || '未知错误'), true)
    }
  } catch {
    toast('存入失败', true)
  }
}

// ===== 键盘 & 初始化 =====
function onKeydown(e) {
  if (e.key === 'Escape') {
    catModalVisible.value = false
    docModalVisible.value = false
    tagModalVisible.value = false
    moveModalVisible.value = false
    pasteModalVisible.value = false
  }
}

onMounted(() => {
  loadCategories()
  loadDocuments()
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>
