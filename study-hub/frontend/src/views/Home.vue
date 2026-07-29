<template>
  <div class="flex flex-col gap-7">
    <!-- 标题 -->
    <div class="text-center mb-1">
      <h1 class="text-[22px] font-bold tracking-tight">学习中枢</h1>
      <div class="mt-1">
        <a href="/kb" target="_blank" rel="noopener noreferrer" class="text-xs text-text-secondary hover:text-accent mr-3">知识库管理 →</a>
        <a href="/wiki" target="_blank" rel="noopener noreferrer" class="text-xs text-accent hover:text-[#a5b0ff]">🧠 Wiki 知识库 →</a>
      </div>
    </div>

    <!-- 搜索框 -->
    <div class="relative flex items-center gap-0">
      <select v-model="searchMode" class="px-3 py-4 bg-surface border-2 border-border border-r-0 rounded-l-[12px] text-text text-sm outline-none cursor-pointer whitespace-nowrap min-w-[90px] appearance-none focus:border-accent">
        <option value="ai">AI 推荐</option>
        <option value="kb">知识库</option>
        <option value="web">全网</option>
        <option value="cmd">命令</option>
      </select>
      <input v-model="searchInput" @keydown.enter="doSearch" type="text" placeholder="输入搜索内容…" autofocus
        class="flex-1 px-4 py-4 bg-surface border-2 border-border border-l border-r-0 text-text text-base outline-none min-w-0 focus:border-accent focus:shadow-[0_0_24px_rgba(124,138,255,0.15)]">
      <select v-model="searchCategory" class="px-2.5 py-4 bg-surface border-2 border-border rounded-r-[12px] text-text text-xs outline-none cursor-pointer max-w-[100px] flex-shrink-0 focus:border-accent">
        <option value="">全部分类</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
      </select>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchLoading" class="bg-surface border border-border rounded-[12px] p-7 text-center text-text-secondary">
      <span>正在搜索…</span>
    </div>
    <div v-else-if="searchResult" class="bg-surface border border-border rounded-[12px] p-5">
      <div v-if="searchError" class="text-danger">{{ searchError }}</div>
      <div v-else>
        <MarkdownRenderer :content="searchAnswer" />
        <div v-if="searchSources" class="text-xs text-text-secondary mt-4">
          来源：{{ searchSources }}
        </div>
      </div>
    </div>

    <!-- 常用网站 -->
    <div>
      <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px] mb-1">常用网站</div>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4">
        <a v-for="(s, i) in settings.shortcuts" :key="i" :href="s.url" target="_blank"
          class="relative aspect-square bg-surface border border-border rounded-[12px] flex flex-col items-center justify-center cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(0,0,0,0.3)] hover:border-accent no-underline text-text gap-2"
          @contextmenu.prevent="openShortcutModal(i)">
          <span class="text-[28px]">{{ s.icon }}</span>
          <span class="text-[13px] text-text-secondary">{{ s.name }}</span>
          <button @click.prevent="confirmRemoveShortcut(i)" class="absolute top-1 right-1 w-[22px] h-[22px] rounded-full border-none bg-white/[0.08] text-text-secondary text-sm flex items-center justify-center hover:bg-danger hover:text-white">×</button>
        </a>
        <div @click="openShortcutModal()"
          class="aspect-square bg-surface border border-dashed border-border rounded-[12px] flex flex-col items-center justify-center cursor-pointer transition-all opacity-60 hover:opacity-100 gap-2">
          <span class="text-[28px]">+</span>
          <span class="text-[13px] text-text-secondary">添加</span>
        </div>
      </div>
    </div>

    <!-- AI 启动器 -->
    <div>
      <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px] mb-1">AI 启动器</div>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div v-for="(a, i) in settings.launcherItems" :key="i"
          class="relative bg-surface border border-border rounded-[12px] p-5 text-center cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(0,0,0,0.3)] hover:border-accent flex flex-col items-center gap-2">
          <div @click="launchAI(a.url)" class="flex flex-col items-center gap-2 flex-1">
            <span class="text-[32px]">{{ a.icon }}</span>
            <span class="text-sm font-semibold">{{ a.name }}</span>
            <span class="text-[11px] text-text-secondary break-all">{{ a.url }}</span>
          </div>
          <button @click.stop="confirmRemoveLauncher(i)" class="absolute top-1 right-1 w-[22px] h-[22px] rounded-full border-none bg-white/[0.08] text-text-secondary text-sm flex items-center justify-center hover:bg-danger hover:text-white">×</button>
        </div>
        <div @click="openAIModal()"
          class="bg-surface border border-dashed border-border rounded-[12px] p-5 text-center cursor-pointer transition-all opacity-60 hover:opacity-100 flex flex-col items-center gap-2">
          <span class="text-[32px]">+</span>
          <span class="text-sm font-semibold">添加 AI</span>
        </div>
      </div>
    </div>

    <!-- 学习工具箱 -->
    <div>
      <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px] mb-1">学习工具箱</div>
      <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4">
        <router-link to="/brainstorm" class="aspect-square bg-surface border border-border rounded-[12px] flex flex-col items-center justify-center cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(0,0,0,0.3)] hover:border-accent no-underline text-text gap-2">
          <span class="text-[28px]">💡</span>
          <span class="text-[13px] text-text-secondary">头脑风暴</span>
        </router-link>
        <router-link to="/learning" class="aspect-square bg-surface border border-border rounded-[12px] flex flex-col items-center justify-center cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(0,0,0,0.3)] hover:border-accent no-underline text-text gap-2">
          <span class="text-[28px]">📋</span>
          <span class="text-[13px] text-text-secondary">学习清单</span>
        </router-link>
        <a v-if="!isElectron" href="/suit/index.html" class="aspect-square bg-surface border border-border rounded-[12px] flex flex-col items-center justify-center cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(0,0,0,0.3)] hover:border-accent no-underline text-text gap-2">
          <span class="text-[28px]">🏋️</span>
          <span class="text-[13px] text-text-secondary">前端套件</span>
        </a>
        <router-link to="/creator" class="aspect-square bg-surface border border-border rounded-[12px] flex flex-col items-center justify-center cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(0,0,0,0.3)] hover:border-accent no-underline text-text gap-2">
          <span class="text-[28px]">🎨</span>
          <span class="text-[13px] text-text-secondary">创作中心</span>
        </router-link>
        <router-link to="/skills" class="aspect-square bg-surface border border-border rounded-[12px] flex flex-col items-center justify-center cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-[0_6px_20px_rgba(0,0,0,0.3)] hover:border-accent no-underline text-text gap-2">
          <span class="text-[28px]">🧩</span>
          <span class="text-[13px] text-text-secondary">Skill 市场</span>
        </router-link>
      </div>
    </div>

    <!-- 知识库 -->
    <div>
      <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px] mb-1">知识库</div>
      <div class="bg-surface border border-border rounded-[12px] p-5">
        <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
          <span class="font-semibold">最近文档</span>
          <div class="flex gap-2 items-center">
            <select v-model="docSort" @change="loadDocuments" class="px-2.5 py-1.5 bg-bg border border-border rounded-[8px] text-text text-[12px] outline-none cursor-pointer focus:border-accent">
              <option value="created_at:desc">最新优先</option>
              <option value="created_at:asc">最早优先</option>
              <option value="title:asc">标题 A-Z</option>
              <option value="title:desc">标题 Z-A</option>
            </select>
            <input ref="fileInput" type="file" accept=".txt,.md,.pdf" multiple class="hidden" @change="handleUpload">
            <button @click="$refs.fileInput.click()" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer hover:bg-surface-hover hover:border-accent">上传文档</button>
            <button @click="doKBSearch" class="px-4 py-2 rounded-[8px] border border-border bg-accent text-white text-[13px] cursor-pointer hover:opacity-90">搜索知识库</button>
            <button @click="openPasteModal" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer hover:bg-surface-hover hover:border-accent">粘贴 Claude 对话</button>
            <button @click="openInbox" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer hover:bg-surface-hover hover:border-accent">打开收件箱</button>
          </div>
        </div>
        <ul v-if="documents.length" class="flex flex-col gap-1.5">
          <li v-for="d in documents.slice(0, 10)" :key="d.id" class="px-3 py-2 rounded-[8px] flex justify-between items-center cursor-pointer hover:bg-surface-hover transition-colors">
            <span @click="viewDocument(d.id)" class="flex items-center gap-2 flex-1">
              <span class="text-sm">{{ d.title }}</span>
              <span v-if="d.category_name" class="text-[11px]" :style="{color: d.category_color || '#7c8aff'}">{{ d.category_icon }} {{ d.category_name }}</span>
              <span class="text-text-secondary text-xs">{{ d.created_at?.slice(0,10) }} · {{ d.char_count || 0 }}字</span>
            </span>
            <div class="flex gap-1 items-center">
              <!-- ASR 失败：重新识别 -->
              <button
                v-if="d.asr_failed"
                @click.stop="reparseDocument(d.id)"
                class="px-2 py-0.5 rounded-[6px] border border-danger bg-danger/10 text-danger text-[11px] hover:bg-danger hover:text-white whitespace-nowrap"
                title="重新识别（ASR 失败）"
              >
                🔄 重识
              </button>
              <button @click.stop="copyDocument(d)" class="px-2 py-0.5 rounded-[6px] border border-border bg-surface text-text-secondary text-[12px] hover:bg-surface-hover hover:border-accent" title="复制全文">复制</button>
              <button @click.stop="deleteDocument(d.id)" class="px-2 py-0.5 rounded-[6px] border border-border bg-surface text-text-secondary text-[12px] hover:bg-danger hover:text-white hover:border-danger" title="删除">删除</button>
            </div>
          </li>
        </ul>
        <div v-else class="text-text-secondary text-sm text-center py-5">知识库为空，请上传文档</div>
      </div>
    </div>

    <!-- 每日复盘 -->
    <div>
      <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px] mb-1">每日复盘</div>
      <div class="bg-surface border border-border rounded-[12px] p-5">
        <textarea v-model="reviewInput" placeholder="写写今天学了什么… 随意写，AI 会帮你润色。" class="w-full min-h-[120px] p-3.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none resize-y focus:border-accent"></textarea>
        <div class="flex gap-2.5 items-center flex-wrap mt-3">
          <button @click="polishReview" :disabled="reviewLoading" class="px-4 py-2 rounded-[8px] border border-border bg-accent text-white text-[13px] cursor-pointer hover:opacity-90 disabled:opacity-50">AI 润色</button>
          <button @click="weeklyReport" :disabled="reviewLoading" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] cursor-pointer hover:bg-surface-hover hover:border-accent disabled:opacity-50">生成本周周报</button>
          <span class="text-xs text-text-secondary">{{ reviewStatus }}</span>
        </div>
        <div v-if="reviewResult" class="mt-4 p-4 bg-bg border border-border rounded-[8px]">
          <MarkdownRenderer :content="reviewResult" />
        </div>
        <div v-if="reviewHistory.length" class="mt-4">
          <h4 class="text-[13px] text-text-secondary mb-2">历史复盘</h4>
          <div v-for="r in reviewHistory.slice(0, 7)" :key="r.id" @click="viewReview(r)"
            class="px-3 py-2.5 rounded-[8px] cursor-pointer text-sm hover:bg-surface-hover transition-colors border-b border-border last:border-b-0">
            {{ r.date }} — {{ (r.raw_text || '').slice(0, 50) }}…
          </div>
        </div>
      </div>
    </div>

    <!-- SOP 建议 -->
    <div>
      <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px] mb-1">SOP 建议</div>
      <div class="bg-surface border border-border rounded-[12px] p-5">
        <div class="flex items-center justify-between mb-3">
          <span class="font-semibold">Wiki → SOP</span>
          <router-link to="/sop" class="px-3 py-1.5 rounded-[8px] border border-border bg-surface text-text text-[12px] cursor-pointer hover:bg-surface-hover hover:border-accent no-underline">前往 SOP →</router-link>
        </div>
        <div class="text-[13px] text-text-secondary mb-3">{{ sopSummary }}</div>
        <div v-if="sopPending.length" class="flex flex-col gap-1.5">
          <div v-for="s in sopPending.slice(0, 5)" :key="s.id" class="px-3 py-2 bg-bg rounded-[8px] flex items-center gap-2">
            <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="sopTypeClass(s.suggestion_type)">{{ sopTypeLabel(s.suggestion_type) }}</span>
            <span class="text-[12px] truncate flex-1">{{ s.suggested_title }}</span>
          </div>
        </div>
        <span v-if="!sopPending.length" class="text-xs text-text-secondary">无待处理建议</span>
      </div>
    </div>

    <!-- 自动化工具 -->
    <div>
      <div class="flex items-center justify-between mb-1">
        <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px]">自动化工具</div>
        <button @click="queuePanelOpen = true" class="text-xs text-accent hover:text-[#a5b0ff] flex items-center gap-1">
          <span>📋</span> 解析队列 <span v-if="queueStats.running > 0" class="bg-accent text-white text-[10px] px-1.5 py-0.5 rounded-full">{{ queueStats.running }}</span>
        </button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="mod in automationModules" :key="mod.id" class="bg-surface border border-border rounded-[12px] p-5 flex flex-col gap-3">
          <div class="flex items-center gap-2.5">
            <span class="text-[28px]">{{ mod.icon }}</span>
            <div>
              <div class="text-[15px] font-semibold">{{ mod.name }}</div>
              <div class="text-xs text-text-secondary">{{ mod.desc }}</div>
            </div>
          </div>
          <DouyinImportPanel v-if="mod.id === 'douyin-summary'" :api="settings" @queued="onDouyinQueued(mod, $event)" />
          <input
            v-else
            v-model="mod.input"
            :placeholder="mod.placeholder"
            @input="mod.inputError = false"
            class="px-3.5 py-2.5 bg-bg border rounded-[8px] text-text text-sm outline-none focus:border-accent transition-colors"
            :class="mod.inputError ? 'border-danger' : 'border-border'"
          >
          <!-- 细粒度进度指示器 -->
          <div v-if="mod.id !== 'douyin-summary' && mod.activeTaskId && taskSteps[mod.activeTaskId]" class="flex flex-col gap-1.5">
            <div class="flex items-center gap-2 text-xs">
              <span class="text-text-secondary">{{ taskProgressText[mod.activeTaskId] || '处理中…' }}</span>
              <span v-if="taskSteps[mod.activeTaskId].some(s => s.status === 'running')" class="inline-block w-3 h-3 border-2 border-accent border-t-transparent rounded-full animate-spin"></span>
            </div>
            <div class="flex gap-1">
              <div v-for="(step, idx) in taskSteps[mod.activeTaskId]" :key="step.key"
                class="h-1.5 flex-1 rounded-full transition-colors"
                :class="{
                  'bg-accent': step.status === 'done',
                  'bg-accent/40 animate-pulse': step.status === 'running',
                  'bg-border': step.status === 'pending',
                  'bg-danger': step.status === 'error'
                }"
                :title="step.label"
              ></div>
            </div>
          </div>
          <div v-if="mod.id !== 'douyin-summary'" class="flex gap-2.5 items-center">
            <button @click="runAutomation(mod)" :disabled="mod.loading" class="px-4 py-2 rounded-[8px] border border-border bg-accent text-white text-[13px] cursor-pointer hover:opacity-90 disabled:opacity-50">开始解析</button>
            <span class="text-[13px] min-h-[20px]" :class="mod.statusClass">{{ mod.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ===== 全局解析队列面板（抽屉） ===== -->
  <div v-if="queuePanelOpen" class="fixed inset-0 bg-black/60 z-[100] flex justify-end" @click.self="queuePanelOpen = false">
    <div class="bg-surface border-l border-border w-[90%] max-w-[420px] h-full flex flex-col">
      <div class="flex items-center justify-between p-5 border-b border-border">
        <h3 class="text-base font-semibold">📋 解析队列</h3>
        <button @click="queuePanelOpen = false" class="text-text-secondary hover:text-text text-lg">×</button>
      </div>
      <div class="p-4 flex flex-col gap-3 overflow-y-auto flex-1">
        <!-- 统计 -->
        <div class="grid grid-cols-4 gap-2 text-center">
          <div class="bg-bg rounded-[8px] p-2">
            <div class="text-lg font-bold">{{ queueStats.pending }}</div>
            <div class="text-[10px] text-text-secondary">待处理</div>
          </div>
          <div class="bg-bg rounded-[8px] p-2">
            <div class="text-lg font-bold text-accent">{{ queueStats.running }}</div>
            <div class="text-[10px] text-text-secondary">进行中</div>
          </div>
          <div class="bg-bg rounded-[8px] p-2">
            <div class="text-lg font-bold text-success">{{ queueStats.done }}</div>
            <div class="text-[10px] text-text-secondary">已完成</div>
          </div>
          <div class="bg-bg rounded-[8px] p-2">
            <div class="text-lg font-bold text-danger">{{ queueStats.error }}</div>
            <div class="text-[10px] text-text-secondary">失败</div>
          </div>
        </div>
        <!-- 任务列表 -->
        <div v-if="queueTasks.length" class="flex flex-col gap-2">
          <div v-for="t in queueTasks" :key="t.task_id" class="bg-bg border border-border rounded-[8px] p-3 flex flex-col gap-2">
            <div class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-2 min-w-0">
                <span class="text-xs px-1.5 py-0.5 rounded bg-surface border border-border flex-shrink-0">{{ t.module_name }}</span>
                <span class="text-xs text-text-secondary truncate">{{ t.input }}</span>
              </div>
              <TaskStatusBadge :status="t.status" class="flex-shrink-0" />
            </div>
            <!-- 步骤条 -->
            <div v-if="t.steps" class="flex gap-1">
              <div v-for="step in t.steps" :key="step.key"
                class="h-1 flex-1 rounded-full transition-colors"
                :class="{
                  'bg-accent': step.status === 'done',
                  'bg-accent/40 animate-pulse': step.status === 'running',
                  'bg-border': step.status === 'pending',
                  'bg-danger': step.status === 'error'
                }"
                :title="step.label"
              ></div>
            </div>
            <!-- API Key 无效错误提示 -->
            <div v-if="t.api_key_error" class="flex items-center gap-2 bg-danger/10 border border-danger/30 rounded-[6px] px-2.5 py-1.5">
              <span class="text-danger text-[11px] flex-1">⚠️ API Key 无效：{{ t.api_key_error_msg }}</span>
              <button @click="retryTask(t.task_id)" class="px-2 py-0.5 rounded-[4px] bg-danger text-white text-[10px] hover:bg-danger/80 flex-shrink-0">🔄 重新加载</button>
            </div>
            <!-- 失败任务：完整错误 + 操作 -->
            <div v-else-if="t.status === 'error' || t.status === 'failed'" class="flex flex-col gap-1.5">
              <div class="text-[11px] text-danger bg-danger/5 border border-danger/20 rounded-[6px] px-2.5 py-1.5">
                <div class="font-medium mb-0.5">❌ 处理失败</div>
                <div class="whitespace-pre-wrap break-all">{{ t.error || t.progress || '未知错误' }}</div>
              </div>
              <div class="flex gap-2 justify-end">
                <button @click="copyTaskDiagnostics(t)" class="px-2 py-1 rounded-[4px] border border-border bg-surface text-[10px] text-text-secondary hover:bg-bg">📋 复制诊断</button>
                <button @click="retryTask(t.task_id)" class="px-2 py-1 rounded-[4px] bg-accent text-white text-[10px] hover:opacity-90">🔄 重试</button>
              </div>
            </div>
            <div v-else class="flex items-center justify-between text-[11px] text-text-secondary">
              <span class="truncate max-w-[140px]">{{ t.progress }}</span>
              <span v-if="t.doc_id">
                <button @click="viewDocument(t.doc_id)" class="text-accent hover:underline">查看文档 #{{ t.doc_id }}</button>
              </span>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-text-secondary text-sm py-8">暂无任务</div>
      </div>
      <div class="p-4 border-t border-border flex gap-2">
        <button @click="clearQueue" class="px-3 py-2 rounded-[8px] border border-border bg-surface text-text text-xs hover:bg-surface-hover">清除已完成</button>
        <button @click="refreshQueue" class="px-3 py-2 rounded-[8px] border border-border bg-accent text-white text-xs hover:opacity-90">刷新</button>
      </div>
    </div>
  </div>

  <!-- ===== 弹窗 ===== -->
  <!-- Shortcut Modal -->
  <div v-if="shortcutModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]" @click.self="shortcutModal = false">
    <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[440px] flex flex-col gap-4">
      <h3 class="text-base">{{ editingShortcutIdx >= 0 ? '编辑快捷方式' : '添加快捷方式' }}</h3>
      <input v-model="shortcutForm.name" placeholder="名称" class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent">
      <input v-model="shortcutForm.url" placeholder="https://…" class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent">
      <input v-model="shortcutForm.icon" placeholder="图标 (emoji)" class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent">
      <div class="flex gap-2.5 justify-end">
        <button @click="shortcutModal = false" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] hover:bg-surface-hover">取消</button>
        <button @click="saveShortcut" class="px-4 py-2 rounded-[8px] border border-border bg-accent text-white text-[13px] hover:opacity-90">保存</button>
      </div>
    </div>
  </div>

  <!-- AI Modal -->
  <div v-if="aiModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]" @click.self="aiModal = false">
    <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[440px] flex flex-col gap-4">
      <h3 class="text-base">添加 AI 服务</h3>
      <input v-model="aiForm.name" placeholder="名称" class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent">
      <input v-model="aiForm.url" placeholder="https://…" class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent">
      <input v-model="aiForm.icon" placeholder="图标 (emoji)" class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent">
      <div class="flex gap-2.5 justify-end">
        <button @click="aiModal = false" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] hover:bg-surface-hover">取消</button>
        <button @click="saveAI" class="px-4 py-2 rounded-[8px] border border-border bg-accent text-white text-[13px] hover:opacity-90">保存</button>
      </div>
    </div>
  </div>

  <!-- Document Modal -->
  <div v-if="docModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]" @click.self="docModal = false">
    <div class="bg-surface border border-border rounded-[12px] p-5 w-[92%] md:w-[88%] max-w-[1200px] flex flex-col gap-4 max-h-[90vh]">
      <h3 class="text-base font-semibold shrink-0">{{ docTitle }}</h3>
      <div class="overflow-y-auto bg-bg p-5 rounded-[8px] flex-1 min-h-0">
        <MarkdownRenderer :content="docContent" />
      </div>
      <div class="flex gap-2.5 justify-end shrink-0">
        <button @click="docModal = false" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] hover:bg-surface-hover">关闭</button>
      </div>
    </div>
  </div>

  <!-- Paste Modal -->
  <div v-if="pasteModal" class="fixed inset-0 bg-black/60 flex items-center justify-center z-[100]" @click.self="pasteModal = false">
    <div class="bg-surface border border-border rounded-[12px] p-6 w-[90%] max-w-[600px] flex flex-col gap-4">
      <h3 class="text-base">粘贴 Claude 对话</h3>
      <textarea v-model="pasteForm.content" placeholder="从 Claude 复制对话内容，粘贴到这里…" class="w-full min-h-[200px] p-3.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none resize-y focus:border-accent"></textarea>
      <input v-model="pasteForm.title" :placeholder="'Claude对话 ' + new Date().toISOString().slice(0,16).replace('T',' ')" class="px-3.5 py-2.5 bg-bg border border-border rounded-[8px] text-text text-sm outline-none focus:border-accent">
      <div class="flex gap-2.5 justify-end">
        <button @click="pasteModal = false" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-text text-[13px] hover:bg-surface-hover">取消</button>
        <button @click="savePaste" class="px-4 py-2 rounded-[8px] border border-border bg-accent text-white text-[13px] hover:opacity-90">存入知识库</button>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '../stores/settings.js'
import { toast } from '../composables/useToast.js'
import { useConfirm } from '../composables/useConfirm.js'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import TaskStatusBadge from '../components/TaskStatusBadge.vue'
import DouyinImportPanel from '../components/DouyinImportPanel.vue'

const settings = useSettingsStore()

// Electron 环境检测
const isElectron = !!(window.electronAPI)

// 安全打开外部链接
function openExternal(url) {
  if (isElectron) {
    window.electronAPI.openExternal(url)
  } else {
    window.open(url, '_blank')
  }
}

// ===== 搜索 =====
const searchMode = ref('ai')
const searchInput = ref('')
const searchCategory = ref('')
const searchLoading = ref(false)
const searchResult = ref(false)
const searchAnswer = ref('')
const searchSources = ref('')
const searchError = ref('')
const categories = ref([])

async function doSearch() {
  const val = searchInput.value.trim()
  if (!val) return
  searchLoading.value = true
  searchResult.value = true
  searchError.value = ''
  searchAnswer.value = ''
  searchSources.value = ''

  try {
    if (searchMode.value === 'web') {
      const sid = 'sh_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 6)
      const bingUrl = `https://www.bing.com/search?q=${encodeURIComponent(val)}&ref=studyhub&sid=${sid}`
      openExternal(bingUrl)
      searchLoading.value = false
      return
    }
    if (searchMode.value === 'cmd') {
      const commands = settings.loadFromStorage('commands', {})
      const url = commands[val]
      if (url) openExternal(url)
      else toast.error(`未知命令: ${val}`)
      searchLoading.value = false
      return
    }
    if (searchMode.value === 'kb') {
      const body = { question: val }
      if (searchCategory.value) body.category_id = parseInt(searchCategory.value)
      const data = await settings.apiPost('/rag/query', body)
      if (data.error) { searchError.value = data.answer || data.error }
      else { searchAnswer.value = data.answer; searchSources.value = data.sources?.join('；') || '' }
    } else {
      const data = await settings.apiPost('/ai-search', { question: val })
      if (data.error) { searchError.value = data.answer || data.error }
      else { searchAnswer.value = data.answer }
    }
  } catch {
    searchError.value = '无法连接后端服务'
  } finally {
    searchLoading.value = false
  }
}

function doKBSearch() {
  searchMode.value = 'kb'
  doSearch()
}

// ===== 快捷方式弹窗 =====
const shortcutModal = ref(false)
const editingShortcutIdx = ref(-1)
const shortcutForm = ref({ name: '', url: '', icon: '' })

function openShortcutModal(idx) {
  editingShortcutIdx.value = idx !== undefined ? idx : -1
  if (idx !== undefined) {
    const s = settings.shortcuts[idx]
    shortcutForm.value = { ...s }
  } else {
    shortcutForm.value = { name: '', url: '', icon: '' }
  }
  shortcutModal.value = true
}

function saveShortcut() {
  const { name, url, icon } = shortcutForm.value
  if (!name || !url) { toast.error('请填写名称和 URL'); return }
  if (editingShortcutIdx.value >= 0) {
    settings.shortcuts[editingShortcutIdx.value] = { name, url, icon: icon || '🔗' }
  } else {
    settings.addShortcut({ name, url, icon: icon || '🔗' })
  }
  shortcutModal.value = false
}

// ===== AI 弹窗 =====
const aiModal = ref(false)
const aiForm = ref({ name: '', url: '', icon: '' })

function openAIModal() {
  aiForm.value = { name: '', url: '', icon: '' }
  aiModal.value = true
}

function saveAI() {
  const { name, url, icon } = aiForm.value
  if (!name || !url) { toast.error('请填写名称和 URL'); return }
  settings.addLauncher({ name, url, icon: icon || '🤖' })
  aiModal.value = false
}

function launchAI(url) { openExternal(url) }

const { confirm } = useConfirm()

async function confirmRemoveShortcut(i) {
  const ok = await confirm({ message: '确定删除这个常用网站吗？' })
  if (ok) settings.removeShortcut(i)
}

async function confirmRemoveLauncher(i) {
  const ok = await confirm({ message: '确定删除这个 AI 服务吗？' })
  if (ok) settings.removeLauncher(i)
}

// ===== 知识库 =====
const documents = ref([])
const docModal = ref(false)
const docTitle = ref('')
const docContent = ref('')
const docSort = ref('created_at:desc')

async function loadDocuments() {
  try {
    const [sortBy, sortOrder] = docSort.value.split(':')
    documents.value = await settings.apiGet(`/documents?sort_by=${sortBy}&sort_order=${sortOrder}`)
  }
  catch { documents.value = [] }
}

async function viewDocument(id) {
  try {
    const doc = await settings.apiGet(`/documents/${id}`)
    if (doc.error) {
      toast.error(doc.error)
      return
    }
    docTitle.value = doc.title
    docContent.value = doc.content || ''
    docModal.value = true
  } catch { toast.error('加载文档失败') }
}

async function copyDocument(doc) {
  try {
    await navigator.clipboard.writeText(doc.content || '')
    toast.success('已复制到剪贴板')
  } catch { toast.error('复制失败') }
}

async function deleteDocument(id) {
  const ok = await confirm({ message: '确定要删除这篇文档吗？', danger: true })
  if (!ok) return
  try {
    await settings.apiDelete(`/documents/${id}`)
    toast.success('文档已删除')
    loadDocuments()
  } catch { toast.error('删除失败') }
}

async function reparseDocument(id) {
  const doc = documents.value.find(d => d.id === id)
  if (!doc) return
  const ok = await confirm({ message: `重新识别 "${doc.title}"？\n将重新提取语音文本并更新文档。` })
  if (!ok) return
  try {
    const data = await settings.apiPost(`/automation/reparse/${id}`)
    if (data.error) {
      toast.error(data.error)
    } else {
      toast.success('已重新提交识别任务，处理完成后自动刷新')
      startQueuePoll()  // 启动轮询，等任务完成后自动刷新文档列表
    }
  } catch { toast.error('重新识别失败') }
}

async function handleUpload(e) {
  const files = e.target.files
  if (!files.length) return
  for (const file of files) {
    const form = new FormData()
    form.append('file', file)
    if (searchCategory.value) form.append('category_id', searchCategory.value)
    try {
      const data = await settings.apiUpload('/upload', form)
      if (data.id) toast.success(`"${file.name}" 上传成功`)
      else toast.error(`上传失败`)
    } catch { toast.error(`上传 "${file.name}" 失败`) }
  }
  e.target.value = ''
  loadDocuments()
}

async function openInbox() {
  try {
    const data = await settings.apiGet('/inbox/open')
    if (data.error) toast.error(data.error)
    else toast.success(`收件箱已打开`)
  } catch { toast.error('打开收件箱失败') }
}

// ===== 粘贴 Claude 对话 =====
const pasteModal = ref(false)
const pasteForm = ref({ title: '', content: '' })

function openPasteModal() {
  pasteForm.value = {
    title: 'Claude对话 ' + new Date().toISOString().slice(0, 16).replace('T', ' '),
    content: ''
  }
  pasteModal.value = true
}

async function savePaste() {
  const { title, content } = pasteForm.value
  if (!content) { toast.error('请粘贴对话内容'); return }
  try {
    const body = { title: title || pasteForm.value.title, content, source: 'claude' }
    if (searchCategory.value) body.category_id = parseInt(searchCategory.value)
    const data = await settings.apiPost('/upload/text', body)
    if (data.id) {
      toast.success(`已存入知识库`)
      pasteModal.value = false
      loadDocuments()
    } else toast.error('存入失败')
  } catch { toast.error('存入失败') }
}

// ===== 每日复盘 =====
const reviewInput = ref('')
const reviewLoading = ref(false)
const reviewStatus = ref('')
const reviewResult = ref('')
const reviewHistory = ref([])

async function polishReview() {
  const text = reviewInput.value.trim()
  if (!text) { toast.error('请先输入今天的笔记'); return }
  reviewLoading.value = true
  reviewStatus.value = '正在润色…'
  try {
    const today = new Date().toISOString().slice(0, 10)
    const data = await settings.apiPost('/review/polish', { raw_text: text, date: today })
    reviewResult.value = data.polished || ''
    reviewStatus.value = '完成'
    loadReviewHistory()
  } catch {
    toast.error('润色失败')
    reviewStatus.value = ''
  } finally { reviewLoading.value = false }
}

async function weeklyReport() {
  reviewLoading.value = true
  reviewStatus.value = '正在生成周报…'
  try {
    const data = await settings.apiGet('/review/weekly')
    reviewResult.value = data.report || ''
    reviewStatus.value = '完成'
  } catch {
    toast.error('周报生成失败')
    reviewStatus.value = ''
  } finally { reviewLoading.value = false }
}

async function loadReviewHistory() {
  try {
    const data = await settings.apiGet('/review/list')
    reviewHistory.value = data
  } catch { reviewHistory.value = [] }
}

function viewReview(r) {
  reviewResult.value = r.polished || r.raw_text || ''
}

// ===== SOP 建议摘要 =====
const sopPending = ref([])
const sopSummary = ref('')

async function loadSopPending() {
  try {
    sopPending.value = await settings.apiGet('/sop/suggestions?status=pending&limit=5')
    sopSummary.value = sopPending.value.length
      ? `${sopPending.value.length} 条待审核建议`
      : '暂无待处理建议'
  } catch {
    sopPending.value = []
    sopSummary.value = '加载失败'
  }
}

function sopTypeLabel(type) {
  return { new_block: '新环节', merge_into_block: '合并', insert_into_chain: '插链', enrich_block: '丰富', extract_chain: '提取流程' }[type] || type
}

function sopTypeClass(type) {
  return {
    new_block: 'bg-green-500/15 text-green-400',
    merge_into_block: 'bg-blue-500/15 text-blue-400',
    insert_into_chain: 'bg-accent/15 text-accent',
    enrich_block: 'bg-yellow-500/15 text-yellow-400',
    extract_chain: 'bg-purple-500/15 text-purple-400',
  }[type] || 'bg-white/10 text-text-secondary'
}

// ===== 自动化工具 =====
const automationModules = ref([
  { id: 'douyin-summary', name: '抖音摘要', icon: '📹', desc: '粘贴抖音分享链接，自动提取文本、识别资源、生成文档', placeholder: '粘贴抖音分享链接…', input: '', batchInput: '', showBatch: false, loading: false, status: '', statusClass: '', activeTaskId: '', inputError: false },
  { id: 'bilibili-summary', name: 'B站解析', icon: '📺', desc: '粘贴B站分享链接，自动解析视频信息、提取语音文本、生成文档', placeholder: '粘贴B站分享链接…', input: '', loading: false, status: '', statusClass: '', activeTaskId: '', inputError: false },
  { id: 'xiaohongshu-summary', name: '小红书解析', icon: '📕', desc: '粘贴小红书分享链接，自动提取笔记内容、图片视频、生成文档', placeholder: '粘贴小红书分享链接…', input: '', loading: false, status: '', statusClass: '', activeTaskId: '', inputError: false },
])

// 全局队列面板状态
const queuePanelOpen = ref(false)
const queueTasks = ref([])
const queueStats = ref({ total: 0, pending: 0, running: 0, done: 0, error: 0 })
const taskSteps = ref({})   // task_id → steps[]
const taskProgressText = ref({}) // task_id → progress text
let queuePollTimer = null
const _seenDoneTasks = new Set()  // 已处理过的完成/失败任务，避免重复刷新文档列表

async function fetchQueue() {
  try {
    const data = await settings.apiGet('/automation/queue/status')
    if (data.stats) queueStats.value = data.stats
    if (data.tasks) {
      queueTasks.value = data.tasks
      // 同步到卡片步骤缓存
      for (const t of data.tasks) {
        if (t.steps) taskSteps.value[t.task_id] = t.steps
        if (t.progress) taskProgressText.value[t.task_id] = t.progress
      }
      // 检测新完成的任务 → 刷新文档列表（用于重新解析等场景）
      let needRefresh = false
      for (const t of data.tasks) {
        if ((t.status === 'done' || t.status === 'error') && !_seenDoneTasks.has(t.task_id)) {
          _seenDoneTasks.add(t.task_id)
          needRefresh = true
        }
      }
      if (needRefresh) loadDocuments()
    }
  } catch { /* ignore */ }
}

function startQueuePoll() {
  stopQueuePoll()
  fetchQueue()
  queuePollTimer = setInterval(fetchQueue, 3000)
}
function stopQueuePoll() {
  if (queuePollTimer) { clearInterval(queuePollTimer); queuePollTimer = null }
}

async function clearQueue() {
  try {
    await settings.apiDelete('/automation/queue/clear')
    fetchQueue()
    toast.success('已清除已完成任务')
  } catch { toast.error('清除失败') }
}

async function retryTask(taskId) {
  try {
    const data = await settings.apiPost(`/automation/queue/retry/${taskId}`)
    if (data.error) {
      if (data.api_key_invalid) {
        toast.error(data.error + ' — 请检查 backend/.env 中的 DASHSCOPE_API_KEY 并重启后端')
      } else {
        toast.error(data.error)
      }
    } else {
      toast.success('任务已重新提交')
      fetchQueue()
    }
  } catch { toast.error('重试失败') }
}
function refreshQueue() { fetchQueue(); toast.success('已刷新') }

async function copyTaskDiagnostics(t) {
  const info = `任务ID: ${t.task_id}
模块: ${t.module_name}
输入: ${t.input}
状态: ${t.status}
错误: ${t.error || t.progress || '未知错误'}
时间: ${new Date().toISOString()}`
  try {
    await navigator.clipboard.writeText(info)
    toast.success('诊断信息已复制')
  } catch {
    toast.error('复制失败')
  }
}

async function runAutomation(mod) {
  // 检查是否有批量输入（仅抖音模块）
  const batchText = (mod.batchInput || '').trim()
  const singleInput = mod.input.trim()
  const hasBatch = mod.id === 'douyin-summary' && batchText

  if (!hasBatch && !singleInput) {
    mod.inputError = true
    toast.error('请粘贴分享链接')
    return
  }
  mod.inputError = false
  if (mod.batchInputError !== undefined) mod.batchInputError = false
  mod.loading = true
  mod.status = '⏳ 已提交，正在处理…'
  mod.statusClass = 'text-text-secondary'

  try {
    let payload
    if (hasBatch) {
      // 批量模式：从 textarea 提取所有行
      const lines = batchText.split('\n').map(l => l.trim()).filter(l => l.length > 0)
      if (singleInput) lines.unshift(singleInput) // 把单独输入框的链接也加上
      payload = { module_id: mod.id, inputs: lines }
    } else {
      payload = { module_id: mod.id, input: singleInput }
    }

    const data = await settings.apiPost('/automation/queue', payload)
    if (data.error) {
      mod.status = data.error
      mod.statusClass = 'text-danger'
      toast.error('提交失败')
    } else if (data.task_ids && data.task_ids.length) {
      mod.activeTaskId = data.task_ids[0]
      const count = data.count || data.task_ids.length
      mod.status = `⏳ 已提交 ${count} 个任务，排队中…`
      // 清空批量输入
      if (hasBatch) mod.batchInput = ''
      startQueuePoll()
    } else {
      mod.status = '提交完成'
    }
  } catch (err) {
    mod.status = '无法连接后端'
    mod.statusClass = 'text-danger'
    toast.error('请求失败')
  } finally { mod.loading = false }
}

function onDouyinQueued(mod, taskIds) {
  if (taskIds.length) mod.activeTaskId = taskIds[0]
  startQueuePoll()
}



// ===== 初始化 =====
onMounted(async () => {
  loadDocuments()
  loadReviewHistory()
  loadSopPending()
  fetchQueue()
  try { categories.value = await settings.apiGet('/categories') } catch { categories.value = [] }
})
onUnmounted(() => {
  stopQueuePoll()
})
</script>
