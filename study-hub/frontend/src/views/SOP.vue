<template>
  <div class="flex flex-col gap-5">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-[22px] font-bold tracking-tight">SOP 规范化</h1>
        <p class="text-xs text-text-secondary mt-1">搭流程 → 连环节 → 知识库自动匹配建议</p>
      </div>
      <div class="flex gap-2">
        <button @click="openBlockModal()" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer hover:bg-surface-hover hover:border-accent transition-colors">
          + 新建环节
        </button>
        <button @click="openChainModal()" class="px-4 py-2 rounded-[8px] bg-accent text-white text-[13px] cursor-pointer border-none hover:opacity-90 transition-opacity">
          + 新建链路
        </button>
      </div>
    </div>

    <!-- Main layout: chains sidebar + editor -->
    <div class="flex gap-5 flex-col lg:flex-row">
      <!-- ===== LEFT: Chains + Blocks ===== -->
      <div class="flex flex-col gap-4 lg:w-[320px] flex-shrink-0">
        <!-- Chains -->
        <div class="bg-surface border border-border rounded-[12px] overflow-hidden">
          <div class="px-4 py-3 border-b border-border flex items-center justify-between">
            <span class="text-[12px] font-semibold text-text-secondary uppercase tracking-[1.5px]">链路</span>
            <span class="text-[10px] text-text-secondary">{{ chains.length }}</span>
          </div>
          <div v-if="!chains.length" class="p-4 text-center text-text-secondary text-[12px]">
            <p class="text-lg mb-1">📋</p>
            <p>还没有链路</p>
            <p class="text-[10px] mt-0.5">点击右上角"新建链路"</p>
          </div>
          <div v-else class="flex flex-col">
            <div
              v-for="c in chains" :key="c.id"
              @click="selectChain(c)"
              class="px-4 py-3 cursor-pointer transition-colors border-l-[3px] flex items-center justify-between group"
              :class="selectedChain?.id === c.id
                ? 'border-l-accent bg-accent/5'
                : 'border-l-transparent hover:bg-surface-hover'"
            >
              <div class="flex-1 min-w-0">
                <div class="text-[13px] font-semibold truncate">{{ c.name }}</div>
                <div class="text-[10px] text-text-secondary mt-0.5">{{ c.block_count || 0 }} 个环节</div>
              </div>
              <button
                @click.stop="deleteChain(c)"
                class="text-[10px] text-text-secondary hover:text-danger bg-transparent border-none cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity px-1"
                title="删除链路"
              >🗑</button>
            </div>
          </div>
        </div>

        <!-- Block Library -->
        <div class="bg-surface border border-border rounded-[12px] overflow-hidden flex-1 flex flex-col min-h-[200px]">
          <div class="px-4 py-3 border-b border-border flex items-center justify-between gap-2">
            <span class="text-[12px] font-semibold text-text-secondary uppercase tracking-[1.5px]">环节库</span>
            <input
              v-model="searchText"
              type="text"
              placeholder="筛选…"
              class="w-[90px] px-2 py-1 bg-bg border border-border rounded-[6px] text-[11px] text-text outline-none focus:border-accent"
            />
          </div>
          <div class="p-3 flex flex-col gap-1.5 overflow-y-auto flex-1 max-h-[400px]">
            <div v-if="!filteredBlocks.length" class="text-center py-8 text-text-secondary text-[12px]">
              <p class="text-lg mb-1">🧩</p>
              <p>{{ searchText ? '没有匹配的环节' : '环节库为空' }}</p>
              <p class="text-[10px] mt-0.5">点击"新建环节"添加</p>
            </div>
            <div
              v-for="b in filteredBlocks" :key="b.id"
              class="group/item"
            >
              <SOPBlockCard
                :block="b"
                :draggable="!!selectedChain"
                :selected="editingBlock?.id === b.id"
                @select="openBlockModal(b)"
                @edit="openBlockModal(b)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- ===== RIGHT: Chain Editor ===== -->
      <div class="flex-1 min-w-0">
        <!-- No chain selected -->
        <div v-if="!selectedChain" class="bg-surface border border-dashed border-border rounded-[12px] p-12 text-center text-text-secondary">
          <p class="text-4xl mb-4">🔗</p>
          <p class="text-[15px] font-semibold mb-1">选择或新建一个链路</p>
          <p class="text-[12px]">从左侧选中链路开始编辑，拖拽环节库中的卡片到此处，或让 AI 分析 Wiki 自动匹配</p>
          <button @click="openChainModal()" class="mt-4 px-4 py-2 rounded-[8px] bg-accent text-white text-[13px] cursor-pointer border-none hover:opacity-90">新建第一个链路</button>
        </div>

        <!-- Chain editor -->
        <template v-else>
          <SOPChainEditor
            :key="selectedChain.id"
            :chain="selectedChain"
            :blocks="chainBlocks"
            @select-block="openBlockModal"
            @edit-block="openBlockModal"
            @remove-block="removeBlockFromChain"
            @move-up="(item) => moveBlock(item, -1)"
            @move-down="(item) => moveBlock(item, 1)"
            @edit-chain="openChainModal(selectedChain)"
            @add-branch="openBranchAdd"
            @reorder-blocks="onReorderBlocks"
            @drop-block="onDropBlock"
          />

          <!-- Add bar -->
          <div class="mt-3 bg-surface border border-border rounded-[12px] p-3">
            <div class="flex items-center gap-2">
              <span class="text-[12px] text-text-secondary flex-shrink-0">
                {{ branchParent ? `添加分支到「${branchParent.block.title}」` : '追加环节到末尾' }}
              </span>
              <select
                v-model="addBlockId"
                class="flex-1 px-3 py-1.5 bg-bg border border-border rounded-[8px] text-[12px] text-text outline-none focus:border-accent min-w-0"
              >
                <option :value="null">{{ blocksNotInChain.length ? '选择环节…' : '所有环节已在链路中' }}</option>
                <option v-for="b in blocksNotInChain" :key="b.id" :value="b.id">{{ b.title }}</option>
              </select>
              <button
                @click="addBlockToChain"
                :disabled="!addBlockId"
                class="px-3 py-1.5 bg-accent text-white rounded-[8px] text-[12px] cursor-pointer border-none disabled:opacity-40 transition-opacity flex-shrink-0"
              >添加</button>
              <button
                v-if="branchParent"
                @click="branchParent = null"
                class="text-[10px] text-text-secondary hover:text-danger bg-transparent border-none cursor-pointer flex-shrink-0"
              >✕ 取消分支</button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ===== Suggestion Queue ===== -->
    <SOPSuggestionQueue
      :suggestions="suggestions"
      :analyzing="analyzing"
      :unmatched-count="unmatchedCount"
      @confirm="confirmSuggestion"
      @reject="rejectSuggestion"
      @analyze="triggerAnalysis"
    />

    <!-- ==== Block Edit Modal ==== -->
    <div v-if="showBlockModal" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="closeBlockModal">
      <div class="bg-surface border border-border rounded-[16px] p-6 w-[560px] max-h-[85vh] overflow-y-auto shadow-2xl">
        <h3 class="text-[16px] font-bold mb-4">{{ editingBlock?.id ? '编辑环节' : '新建环节' }}</h3>
        <div class="flex flex-col gap-3">
          <div>
            <label class="text-[10px] text-text-secondary uppercase tracking-[1.5px] font-semibold">名称</label>
            <input v-model="blockForm.title" class="w-full mt-1 px-3 py-2.5 bg-bg border border-border rounded-[8px] text-[13px] text-text outline-none focus:border-accent transition-colors" placeholder="环节名称" />
          </div>
          <div>
            <label class="text-[10px] text-text-secondary uppercase tracking-[1.5px] font-semibold">简述</label>
            <input v-model="blockForm.description" class="w-full mt-1 px-3 py-2.5 bg-bg border border-border rounded-[8px] text-[13px] text-text outline-none focus:border-accent transition-colors" placeholder="一句话描述" />
          </div>
          <div>
            <label class="text-[10px] text-text-secondary uppercase tracking-[1.5px] font-semibold">详细内容 (Markdown)</label>
            <textarea v-model="blockForm.content" rows="8" class="w-full mt-1 px-3 py-2.5 bg-bg border border-border rounded-[8px] text-[13px] text-text outline-none focus:border-accent transition-colors resize-y font-mono text-[12px] leading-relaxed" placeholder="操作步骤、检查项、注意事项…&#10;&#10;用 Markdown 格式书写"></textarea>
          </div>
          <div>
            <label class="text-[10px] text-text-secondary uppercase tracking-[1.5px] font-semibold">标签（逗号分隔）</label>
            <input v-model="blockForm.tagsStr" class="w-full mt-1 px-3 py-2.5 bg-bg border border-border rounded-[8px] text-[13px] text-text outline-none focus:border-accent transition-colors" placeholder="写小说, 创作流程" />
          </div>
          <div v-if="editingBlock?.source_wiki_page_id" class="text-[11px] text-accent bg-accent/5 px-3 py-2 rounded-[8px]">
            📄 来源于 Wiki 页面 #{{ editingBlock.source_wiki_page_id }}
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-5 pt-4 border-t border-border">
          <button v-if="editingBlock?.id" @click="deleteBlock(editingBlock)" class="px-4 py-2 rounded-[8px] border border-danger/20 text-danger text-[13px] cursor-pointer hover:bg-danger/5 transition-colors mr-auto">删除</button>
          <button @click="closeBlockModal" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer hover:bg-surface-hover transition-colors">取消</button>
          <button @click="saveBlock" :disabled="!blockForm.title.trim()" class="px-5 py-2 rounded-[8px] bg-accent text-white text-[13px] cursor-pointer border-none hover:opacity-90 transition-opacity disabled:opacity-40">保存</button>
        </div>
      </div>
    </div>

    <!-- ==== Chain Edit Modal ==== -->
    <div v-if="showChainModal" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="closeChainModal">
      <div class="bg-surface border border-border rounded-[16px] p-6 w-[460px] shadow-2xl">
        <h3 class="text-[16px] font-bold mb-4">{{ editingChain?.id ? '编辑链路' : '新建链路' }}</h3>
        <div class="flex flex-col gap-3">
          <div>
            <label class="text-[10px] text-text-secondary uppercase tracking-[1.5px] font-semibold">名称</label>
            <input v-model="chainForm.name" class="w-full mt-1 px-3 py-2.5 bg-bg border border-border rounded-[8px] text-[13px] text-text outline-none focus:border-accent transition-colors" placeholder="例如：写小说流程" />
          </div>
          <div>
            <label class="text-[10px] text-text-secondary uppercase tracking-[1.5px] font-semibold">描述</label>
            <textarea v-model="chainForm.description" rows="3" class="w-full mt-1 px-3 py-2.5 bg-bg border border-border rounded-[8px] text-[13px] text-text outline-none focus:border-accent transition-colors resize-y" placeholder="这个链路涵盖从哪到哪的完整流程"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-5 pt-4 border-t border-border">
          <button @click="closeChainModal" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer hover:bg-surface-hover transition-colors">取消</button>
          <button @click="saveChain" :disabled="!chainForm.name.trim()" class="px-5 py-2 rounded-[8px] bg-accent text-white text-[13px] cursor-pointer border-none hover:opacity-90 transition-opacity disabled:opacity-40">保存</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <Toast :visible="toast.visible" :message="toast.message" :is-error="toast.isError" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings.js'
import SOPBlockCard from '../components/SOPBlockCard.vue'
import SOPChainEditor from '../components/SOPChainEditor.vue'
import SOPSuggestionQueue from '../components/SOPSuggestionQueue.vue'
import Toast from '../components/Toast.vue'

const settings = useSettingsStore()

// ── State ──
const blocks = ref([])
const chains = ref([])
const selectedChain = ref(null)
const chainBlocks = ref([])
const searchText = ref('')
const addBlockId = ref(null)
const branchParent = ref(null)

// Toast
const toast = ref({ visible: false, message: '', isError: false })
let toastTimer = null
function showToast(msg, isError = false) {
  clearTimeout(toastTimer)
  toast.value = { visible: true, message: msg, isError }
  toastTimer = setTimeout(() => { toast.value.visible = false }, 2500)
}

// ── Modals ──
const showBlockModal = ref(false)
const editingBlock = ref(null)
const blockForm = ref({ title: '', description: '', content: '', tagsStr: '' })

const showChainModal = ref(false)
const editingChain = ref(null)
const chainForm = ref({ name: '', description: '' })

function openBlockModal(block = null) {
  editingBlock.value = block
  if (block) {
    const t = block.tags
    let tags = []
    if (t) {
      if (Array.isArray(t)) tags = t
      else { try { tags = JSON.parse(t) } catch { tags = [] } }
    }
    blockForm.value = {
      title: block.title || '',
      description: block.description || '',
      content: block.content || '',
      tagsStr: tags.join(', '),
    }
  } else {
    blockForm.value = { title: '', description: '', content: '', tagsStr: '' }
  }
  showBlockModal.value = true
}

function closeBlockModal() { showBlockModal.value = false; editingBlock.value = null }

async function saveBlock() {
  const tags = blockForm.value.tagsStr.split(',').map(t => t.trim()).filter(Boolean)
  const payload = { title: blockForm.value.title, description: blockForm.value.description, content: blockForm.value.content, tags }
  try {
    if (editingBlock.value?.id) {
      await settings.apiPut(`/sop/blocks/${editingBlock.value.id}`, payload)
    } else {
      await settings.apiPost('/sop/blocks', payload)
    }
    closeBlockModal()
    await loadBlocks()
    if (selectedChain.value) await loadChainDetail(selectedChain.value.id)
    showToast(editingBlock.value?.id ? '环节已更新' : '环节已创建')
  } catch (e) { showToast('保存失败', true) }
}

async function deleteBlock(block) {
  if (!confirm(`确定删除环节「${block.title}」？\n\n已在链路中的也会被移除。`)) return
  try {
    await settings.apiDelete(`/sop/blocks/${block.id}`)
    closeBlockModal()
    await loadBlocks()
    if (selectedChain.value) await loadChainDetail(selectedChain.value.id)
    await loadChains()
    showToast('环节已删除')
  } catch (e) { showToast('删除失败', true) }
}

function openChainModal(chain = null) {
  editingChain.value = chain
  chainForm.value = { name: chain?.name || '', description: chain?.description || '' }
  showChainModal.value = true
}

function closeChainModal() { showChainModal.value = false; editingChain.value = null }

async function saveChain() {
  try {
    if (editingChain.value?.id) {
      await settings.apiPut(`/sop/chains/${editingChain.value.id}`, chainForm.value)
    } else {
      await settings.apiPost('/sop/chains', chainForm.value)
    }
    closeChainModal()
    await loadChains()
    if (editingChain.value?.id && selectedChain.value?.id === editingChain.value.id) {
      await selectChain({ id: editingChain.value.id })
    }
    showToast(editingChain.value?.id ? '链路已更新' : '链路已创建')
  } catch (e) { showToast('保存失败', true) }
}

// ── Data ──
async function loadBlocks() {
  try { blocks.value = await settings.apiGet('/sop/blocks') } catch { blocks.value = [] }
}
async function loadChains() {
  try { chains.value = await settings.apiGet('/sop/chains') } catch { chains.value = [] }
}
async function loadChainDetail(chainId) {
  try {
    const data = await settings.apiGet(`/sop/chains/${chainId}`)
    chainBlocks.value = data.blocks || []
  } catch { chainBlocks.value = [] }
}

const filteredBlocks = computed(() => {
  if (!searchText.value) return blocks.value
  const q = searchText.value.toLowerCase()
  return blocks.value.filter(b =>
    b.title.toLowerCase().includes(q) || (b.description || '').toLowerCase().includes(q)
  )
})

const blocksNotInChain = computed(() => {
  if (!selectedChain.value) return blocks.value
  const inChain = new Set(chainBlocks.value.map(cb => cb.block?.id).filter(Boolean))
  return blocks.value.filter(b => !inChain.has(b.id))
})

// ── Chain actions ──
async function selectChain(chain) {
  selectedChain.value = chain
  branchParent.value = null
  addBlockId.value = null
  await loadChainDetail(chain.id)
}

async function deleteChain(chain) {
  if (!confirm(`确定删除链路「${chain.name}」？`)) return
  try {
    await settings.apiDelete(`/sop/chains/${chain.id}`)
    if (selectedChain.value?.id === chain.id) { selectedChain.value = null; chainBlocks.value = [] }
    await loadChains()
    showToast('链路已删除')
  } catch { showToast('删除失败', true) }
}

async function addBlockToChain() {
  if (!addBlockId.value || !selectedChain.value) return
  try {
    const payload = { block_id: addBlockId.value }
    if (branchParent.value) payload.parent_id = branchParent.value.cb_id
    await settings.apiPost(`/sop/chains/${selectedChain.value.id}/blocks`, payload)
    addBlockId.value = null
    branchParent.value = null
    await loadChainDetail(selectedChain.value.id)
    await loadChains()
    showToast('已添加')
  } catch { showToast('添加失败', true) }
}

function openBranchAdd(item) {
  branchParent.value = item
  addBlockId.value = null
  showToast(`选择环节后添加到「${item.block.title}」下`)
}

async function removeBlockFromChain(item) {
  if (!selectedChain.value) return
  try {
    await settings.apiDelete(`/sop/chains/${selectedChain.value.id}/blocks/${item.cb_id}`)
    await loadChainDetail(selectedChain.value.id)
    await loadChains()
    showToast('已移除')
  } catch { showToast('移除失败', true) }
}

async function moveBlock(item, delta) {
  if (!selectedChain.value) return
  const list = [...chainBlocks.value]
  const idx = list.findIndex(b => b.cb_id === item.cb_id)
  if (idx === -1) return

  const currentParent = item.parent_id || null
  let targetIdx = -1
  for (let i = idx + delta; i >= 0 && i < list.length; i += delta) {
    if ((list[i].parent_id || null) === currentParent) { targetIdx = i; break }
  }
  if (targetIdx === -1) return

  const tmp = list[idx].sort_order
  list[idx].sort_order = list[targetIdx].sort_order
  list[targetIdx].sort_order = tmp
  await saveReorder(list)
}

async function onReorderBlocks({ cb_id, targetIndex }) {
  // Move the block to targetIndex in the flat list, respecting depth
  if (!selectedChain.value) return
  const list = [...chainBlocks.value]

  // Build flat order respecting parent-child grouping
  const mainBlocks = list.filter(b => !b.parent_id).sort((a, b) => a.sort_order - b.sort_order)
  const srcItem = list.find(b => b.cb_id === cb_id)
  if (!srcItem || srcItem.parent_id) return // only reorder top-level blocks for now

  // Remove from current position
  const oldIdx = mainBlocks.findIndex(b => b.cb_id === cb_id)
  if (oldIdx === -1) return
  const [moved] = mainBlocks.splice(oldIdx, 1)
  const insertIdx = Math.min(targetIndex, mainBlocks.length)
  mainBlocks.splice(insertIdx, 0, moved)

  // Reassign sort_order
  const newList = []
  let order = 0
  for (const mb of mainBlocks) {
    mb.sort_order = order++
    newList.push(mb)
    const children = list.filter(b => b.parent_id === mb.cb_id).sort((a, b) => a.sort_order - b.sort_order)
    for (const child of children) {
      child.sort_order = order++
      newList.push(child)
    }
  }

  await saveReorder(newList)
}

async function onDropBlock({ block, targetIndex }) {
  // Block dragged from left panel → insert at targetIndex
  if (!selectedChain.value) return
  try {
    // First add to end to get a cb_id
    const res = await settings.apiPost(`/sop/chains/${selectedChain.value.id}/blocks`, { block_id: block.id })
    await loadChainDetail(selectedChain.value.id)

    // Then move to target position
    if (targetIndex < chainBlocks.value.length - 1) {
      const added = chainBlocks.value.find(b => b.block?.id === block.id)
      if (added) {
        await onReorderBlocks({ cb_id: added.cb_id, targetIndex })
      }
    }
    await loadChainDetail(selectedChain.value.id)
    await loadChains()
    showToast(`「${block.title}」已添加`)
  } catch { showToast('添加失败', true) }
}

async function saveReorder(list) {
  const order = list.map(b => ({ cb_id: b.cb_id, sort_order: b.sort_order }))
  try {
    await settings.apiPut(`/sop/chains/${selectedChain.value.id}/reorder`, { order })
    await loadChainDetail(selectedChain.value.id)
  } catch { showToast('排序失败', true) }
}

// ── Suggestions ──
const suggestions = ref([])
const analyzing = ref(false)
const unmatchedCount = ref(0)

async function loadSuggestions() {
  try { suggestions.value = await settings.apiGet('/sop/suggestions?status=pending&limit=20') } catch { suggestions.value = [] }
}

async function loadUnmatchedCount() {
  try {
    const data = await settings.apiGet('/sop/wiki-unmatched')
    unmatchedCount.value = Array.isArray(data) ? data.length : 0
  } catch { unmatchedCount.value = 0 }
}

async function triggerAnalysis() {
  analyzing.value = true
  try {
    const data = await settings.apiPost('/sop/evolution/analyze', { limit: 100 })
    showToast(`分析完成：${data.message}`)
    await Promise.all([loadSuggestions(), loadUnmatchedCount()])
  } catch { showToast('分析失败', true) }
  finally { analyzing.value = false }
}

async function confirmSuggestion(s) {
  try {
    const data = await settings.apiPost(`/sop/suggestions/${s.id}/confirm`, {})
    const labels = { created_block: '创建环节', inserted_into_chain: '插入链路', updated_block: '更新环节', created_chain: '创建链路' }
    showToast(`已${labels[data.action] || '处理'}`)
    await Promise.all([loadSuggestions(), loadBlocks(), loadChains()])
    if (selectedChain.value) await loadChainDetail(selectedChain.value.id)
  } catch { showToast('确认失败', true) }
}

async function rejectSuggestion(s) {
  try {
    await settings.apiPost(`/sop/suggestions/${s.id}/reject`, { reason: '手动拒绝' })
    showToast('建议已拒绝')
    await loadSuggestions()
  } catch { showToast('拒绝失败', true) }
}

// ── Init ──
onMounted(async () => {
  await Promise.all([loadBlocks(), loadChains(), loadSuggestions(), loadUnmatchedCount()])
})
</script>
