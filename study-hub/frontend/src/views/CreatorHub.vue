<template>
  <div class="flex flex-col gap-6">
    <!-- 标题区 -->
    <div class="text-center mb-1">
      <h1 class="text-[22px] font-bold tracking-tight">🎬 运营工作台</h1>
      <p class="text-xs text-text-secondary mt-1">选题 → 矩阵号 → 口播稿 → 剪辑 → 封面 → 发布，一站式搞定</p>
    </div>

    <!-- 仪表盘 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="bg-surface border border-border rounded-[12px] p-4 text-center">
        <div class="text-2xl font-bold text-accent">{{ dashboard.projects?.total || 0 }}</div>
        <div class="text-[11px] text-text-secondary">内容项目</div>
      </div>
      <div class="bg-surface border border-border rounded-[12px] p-4 text-center">
        <div class="text-2xl font-bold text-success">{{ dashboard.projects?.published || 0 }}</div>
        <div class="text-[11px] text-text-secondary">已发布</div>
      </div>
      <div class="bg-surface border border-border rounded-[12px] p-4 text-center">
        <div class="text-2xl font-bold text-warning">{{ dashboard.topics?.unused || 0 }}</div>
        <div class="text-[11px] text-text-secondary">待选选题</div>
      </div>
      <div class="bg-surface border border-border rounded-[12px] p-4 text-center">
        <div class="text-2xl font-bold">{{ dashboard.accounts || 0 }}</div>
        <div class="text-[11px] text-text-secondary">矩阵账号</div>
      </div>
    </div>

    <!-- 6步流水线 -->
    <div class="bg-surface border border-border rounded-[12px] p-5">
      <div class="flex items-center justify-between mb-4">
        <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px]">⚡ 运营流水线</div>
        <button @click="showNewProjectModal = true" class="px-3 py-1.5 rounded-[8px] bg-accent text-white text-[12px] hover:opacity-90">
          + 新建项目
        </button>
      </div>

      <!-- 步骤导航 -->
      <div class="flex items-center gap-1 mb-5 overflow-x-auto pb-2">
        <button v-for="(step, idx) in pipelineSteps" :key="step.key"
          @click="activeStep = step.key"
          class="flex items-center gap-1.5 px-3 py-2 rounded-[8px] text-[12px] whitespace-nowrap transition-all"
          :class="activeStep === step.key ? 'bg-accent text-white' : 'bg-bg text-text-secondary hover:text-text'">
          <span>{{ step.icon }}</span>
          <span>{{ step.label }}</span>
        </button>
      </div>

      <!-- 步骤 1: 找选题 -->
      <div v-if="activeStep === 'topic'" class="flex flex-col gap-4">
        <div class="flex items-center gap-2">
          <input v-model="topicKeyword" placeholder="输入关键词让 AI 找选题…" 
            class="flex-1 px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent"
            @keydown.enter="aiDiscoverTopics">
          <button @click="aiDiscoverTopics" :disabled="topicLoading"
            class="px-4 py-2 rounded-[8px] bg-accent text-white text-[12px] hover:opacity-90 disabled:opacity-50">
            {{ topicLoading ? '发现中…' : 'AI 发现' }}
          </button>
        </div>
        <div class="flex items-center gap-2">
          <input v-model="newTopicTitle" placeholder="或手动输入选题…" 
            class="flex-1 px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent"
            @keydown.enter="addTopic">
          <button @click="addTopic" class="px-4 py-2 rounded-[8px] border border-border bg-surface text-[12px] hover:border-accent">
            添加
          </button>
        </div>
        <div v-if="topics.length" class="flex flex-col gap-2">
          <div v-for="t in topics" :key="t.id" 
            class="flex items-center gap-3 px-3 py-2.5 bg-bg rounded-[8px] hover:bg-surface-hover transition-colors cursor-pointer"
            @click="createProjectFromTopic(t)">
            <span class="text-lg">💡</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate">{{ t.title }}</div>
              <div class="text-[11px] text-text-secondary">{{ t.source }} · {{ t.created_at?.slice(0,10) }}</div>
            </div>
            <button v-if="!t.used" @click.stop="createProjectFromTopic(t)" class="text-[11px] px-2 py-1 rounded-[6px] bg-accent/10 text-accent hover:bg-accent hover:text-white transition-colors">
              创建项目
            </button>
            <span v-else class="text-[11px] text-text-secondary">已用</span>
          </div>
        </div>
        <div v-else class="text-center text-text-secondary text-sm py-8">暂无选题，点击 AI 发现或手动添加</div>
      </div>

      <!-- 步骤 2: 矩阵号 -->
      <div v-if="activeStep === 'accounts'" class="flex flex-col gap-4">
        <div class="flex items-center gap-2">
          <select v-model="newAccount.platform" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
            <option value="">选择平台</option>
            <option value="douyin">抖音</option>
            <option value="xiaohongshu">小红书</option>
            <option value="bilibili">B站</option>
            <option value="wechat">公众号</option>
            <option value="youtube">YouTube</option>
          </select>
          <input v-model="newAccount.account_name" placeholder="账号名称" 
            class="flex-1 px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
          <button @click="addAccount" class="px-4 py-2 rounded-[8px] bg-accent text-white text-[12px] hover:opacity-90">
            添加
          </button>
        </div>
        <div v-if="accounts.length" class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div v-for="a in accounts" :key="a.id" class="flex items-center gap-3 px-3 py-2.5 bg-bg rounded-[8px]">
            <span class="text-xl">{{ platformIcon(a.platform) }}</span>
            <div class="flex-1">
              <div class="text-sm font-medium">{{ a.name }}</div>
              <div class="text-[11px] text-text-secondary">{{ a.platform }} · {{ a.followers }} 粉丝</div>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-text-secondary text-sm py-8">暂无账号，请添加你的矩阵账号</div>
      </div>

      <!-- 步骤 3: 口播稿 -->
      <div v-if="activeStep === 'script'" class="flex flex-col gap-4">
        <div class="flex items-center gap-2 flex-wrap">
          <select v-model="scriptProjectId" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
            <option value="">选择项目</option>
            <option v-for="p in projects.filter(x => x.status !== 'published')" :key="p.id" :value="p.id">
              {{ p.title }} ({{ statusLabel(p.status) }})
            </option>
          </select>
          <select v-model="scriptStyle" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
            <option value="口播">口播</option>
            <option value="剧情">剧情</option>
            <option value="科普">科普</option>
            <option value="带货">带货</option>
          </select>
          <button @click="generateScript" :disabled="scriptLoading || !scriptProjectId"
            class="px-4 py-2 rounded-[8px] bg-accent text-white text-[12px] hover:opacity-90 disabled:opacity-50">
            {{ scriptLoading ? '生成中…' : 'AI 写稿' }}
          </button>
          <button @click="generateTTS" :disabled="ttsLoading || !scriptProjectId || !currentScript"
            class="px-4 py-2 rounded-[8px] border border-border bg-surface text-[12px] hover:border-accent disabled:opacity-50">
            {{ ttsLoading ? '合成中…' : '语音合成' }}
          </button>
        </div>
        <div v-if="currentAudioUrl" class="flex items-center gap-3 bg-bg border border-border rounded-[8px] p-3">
          <audio :src="apiBase + currentAudioUrl" controls class="flex-1 h-[32px]"></audio>
          <span class="text-[11px] text-text-secondary">{{ ttsVoiceName }}</span>
        </div>
        
        <!-- 口播稿编辑器 -->
        <div v-if="currentScript" class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <span class="text-[12px] text-text-secondary">口播稿编辑器</span>
            <div class="flex gap-2">
              <button @click="polishScript" :disabled="scriptLoading" class="text-[11px] px-2 py-1 rounded-[6px] border border-border hover:border-accent">
                ✨ 润色
              </button>
              <button @click="saveScript" class="text-[11px] px-2 py-1 rounded-[6px] bg-accent text-white hover:opacity-90">
                保存
              </button>
            </div>
          </div>
          <textarea v-model="currentScript" rows="12" 
            class="w-full px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent resize-y font-mono leading-relaxed"></textarea>
        </div>
        <div v-else-if="!scriptProjectId" class="text-center text-text-secondary text-sm py-8">先选择一个项目</div>
        <div v-else class="text-center text-text-secondary text-sm py-8">点击「AI 写稿」生成口播稿，然后「语音合成」生成音频</div>
      </div>

      <!-- 步骤 4: 视频剪辑 -->
      <div v-if="activeStep === 'video'" class="flex flex-col gap-4">
        <div class="flex items-center gap-2">
          <select v-model="videoProjectId" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
            <option value="">选择项目</option>
            <option v-for="p in projects.filter(x => x.status === 'script' || x.status === 'recording')" :key="p.id" :value="p.id">
              {{ p.title }}
            </option>
          </select>
          <button @click="generateEditingPlan" :disabled="videoLoading || !videoProjectId"
            class="px-4 py-2 rounded-[8px] border border-border bg-surface text-[12px] hover:border-accent disabled:opacity-50">
            {{ videoLoading ? '生成中…' : '生成剪辑方案' }}
          </button>
          <button @click="autoEditVideo" :disabled="autoEditLoading || !videoProjectId"
            class="px-4 py-2 rounded-[8px] bg-accent text-white text-[12px] hover:opacity-90 disabled:opacity-50">
            {{ autoEditLoading ? '剪辑中…' : '自动剪辑' }}
          </button>
          <button @click="capcutExport" :disabled="capcutLoading || !videoProjectId"
            class="px-4 py-2 rounded-[8px] border border-border bg-surface text-[12px] hover:border-accent disabled:opacity-50">
            {{ capcutLoading ? '生成中…' : '剪映导出指南' }}
          </button>
        </div>
        <div v-if="editingPlan" class="bg-bg border border-border rounded-[8px] p-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-[12px] font-medium">剪辑方案</span>
            <button @click="updateProjectStatus(videoProjectId, 'editing')" class="text-[11px] px-2 py-1 rounded-[6px] bg-accent text-white hover:opacity-90">
              标记为剪辑中
            </button>
          </div>
          <pre class="text-[12px] text-text-secondary whitespace-pre-wrap font-mono leading-relaxed">{{ editingPlan }}</pre>
        </div>
        <div v-if="currentVideoUrl" class="bg-bg border border-border rounded-[8px] p-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-[12px] font-medium">自动剪辑结果</span>
            <button @click="updateProjectStatus(videoProjectId, 'editing')" class="text-[11px] px-2 py-1 rounded-[6px] bg-accent text-white hover:opacity-90">
              标记为剪辑中
            </button>
          </div>
          <video :src="apiBase + currentVideoUrl" controls class="max-w-full rounded-[8px]"></video>
          <div class="text-[11px] text-text-secondary mt-2">基于 TTS 音频 + 自动字幕生成的基础口播视频</div>
        </div>
        <div v-if="capcutGuide" class="bg-bg border border-border rounded-[8px] p-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-[12px] font-medium">剪映导入指南</span>
            <button @click="copyText(capcutGuide)" class="text-[11px] px-2 py-1 rounded-[6px] border border-border hover:border-accent">
              复制指南
            </button>
          </div>
          <pre class="text-[12px] text-text-secondary whitespace-pre-wrap font-mono leading-relaxed max-h-[300px] overflow-y-auto">{{ capcutGuide }}</pre>
        </div>
        <div v-if="!editingPlan && !currentVideoUrl && !capcutGuide" class="text-center text-text-secondary text-sm py-8">选择项目后，可生成剪辑方案、自动剪辑或剪映导出指南</div>
      </div>

      <!-- 步骤 5: 封面图 -->
      <div v-if="activeStep === 'cover'" class="flex flex-col gap-4">
        <div class="flex items-center gap-2">
          <select v-model="coverProjectId" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
            <option value="">选择项目</option>
            <option v-for="p in projects.filter(x => x.status === 'editing' || x.status === 'cover' || x.status === 'ready')" :key="p.id" :value="p.id">
              {{ p.title }}
            </option>
          </select>
          <select v-model="coverStyle" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
            <option value="default">通用</option>
            <option value="xiaohongshu">小红书</option>
            <option value="douyin">抖音</option>
            <option value="bilibili">B站</option>
          </select>
          <button @click="generateCover" :disabled="coverLoading || !coverProjectId"
            class="px-4 py-2 rounded-[8px] bg-accent text-white text-[12px] hover:opacity-90 disabled:opacity-50">
            {{ coverLoading ? '生成中…' : 'AI 生成封面' }}
          </button>
        </div>
        <div v-if="currentCoverUrl" class="flex flex-col items-center gap-3">
          <img :src="apiBase + currentCoverUrl" class="max-w-[320px] rounded-[8px] border border-border" alt="封面">
          <div class="flex gap-2">
            <button @click="generateCover" class="text-[11px] px-3 py-1.5 rounded-[6px] border border-border hover:border-accent">
              🔄 重新生成
            </button>
            <button @click="updateProjectStatus(coverProjectId, 'ready')" class="text-[11px] px-3 py-1.5 rounded-[6px] bg-accent text-white hover:opacity-90">
              确认使用
            </button>
          </div>
        </div>
        <div v-else class="text-center text-text-secondary text-sm py-8">选择项目生成封面</div>
      </div>

      <!-- 步骤 6: 多平台发布 -->
      <div v-if="activeStep === 'publish'" class="flex flex-col gap-4">
        <div class="flex items-center gap-2">
          <select v-model="publishProjectId" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
            <option value="">选择项目</option>
            <option v-for="p in projects.filter(x => x.status === 'cover' || x.status === 'ready')" :key="p.id" :value="p.id">
              {{ p.title }}
            </option>
          </select>
        </div>
        <div class="flex flex-wrap gap-2">
          <label v-for="pf in publishPlatforms" :key="pf.key" 
            class="flex items-center gap-2 px-3 py-2 bg-bg border border-border rounded-[8px] cursor-pointer hover:border-accent transition-colors"
            :class="{ 'border-accent bg-accent/10': selectedPublishPlatforms.includes(pf.key) }">
            <input type="checkbox" v-model="selectedPublishPlatforms" :value="pf.key" class="accent-accent">
            <span>{{ pf.icon }}</span>
            <span class="text-[12px]">{{ pf.label }}</span>
          </label>
        </div>
        <div class="flex items-center gap-2">
          <button @click="publishContent" :disabled="publishLoading || !publishProjectId || !selectedPublishPlatforms.length"
            class="px-4 py-2 rounded-[8px] border border-border bg-surface text-[12px] hover:border-accent disabled:opacity-50">
            {{ publishLoading ? '适配中…' : '生成各平台文案' }}
          </button>
          <button @click="autoPublish" :disabled="autoPublishLoading || !publishProjectId || !selectedPublishPlatforms.length"
            class="px-4 py-2 rounded-[8px] bg-accent text-white text-[12px] hover:opacity-90 disabled:opacity-50">
            {{ autoPublishLoading ? '发布中…' : '一键发布' }}
          </button>
        </div>
        <div v-if="publishConfig" class="text-[11px] text-text-secondary">
          发布配置: Postiz {{ publishConfig.postiz?.configured ? '✅' : '❌' }} | n8n {{ publishConfig.n8n?.configured ? '✅' : '❌' }}
        </div>
        
        <!-- 平台文案展示 -->
        <div v-if="platformContents" class="flex flex-col gap-3">
          <div v-for="(content, pf) in platformContents" :key="pf" class="bg-bg border border-border rounded-[8px] p-4">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[12px] font-medium">{{ platformName(pf) }} 文案</span>
              <div class="flex gap-2">
                <button @click="copyText(content)" class="text-[11px] px-2 py-1 rounded-[6px] border border-border hover:border-accent">
                  复制
                </button>
                <button @click="confirmPublished(pf)" class="text-[11px] px-2 py-1 rounded-[6px] bg-success text-white hover:opacity-90">
                  已发布
                </button>
              </div>
            </div>
            <pre class="text-[12px] text-text-secondary whitespace-pre-wrap max-h-[200px] overflow-y-auto">{{ content }}</pre>
          </div>
        </div>
        <!-- 一键发布结果 -->
        <div v-if="autoPublishResults" class="flex flex-col gap-3">
          <div v-for="(result, pf) in autoPublishResults" :key="pf" class="bg-bg border border-border rounded-[8px] p-4"
            :class="{ 'border-success': result.status === 'published', 'border-warning': result.status === 'ready' }">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[12px] font-medium">{{ platformName(pf) }}</span>
              <span class="text-[11px] px-2 py-0.5 rounded-full" 
                :class="result.status === 'published' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'">
                {{ result.status === 'published' ? '已发布' : '待手动' }}
              </span>
            </div>
            <pre class="text-[12px] text-text-secondary whitespace-pre-wrap max-h-[150px] overflow-y-auto">{{ result.content }}</pre>
            <div v-if="result.postiz?.error || result.n8n?.error" class="text-[11px] text-danger mt-1">
              自动发布失败: {{ result.postiz?.error || result.n8n?.error }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 项目列表 -->
    <div class="bg-surface border border-border rounded-[12px] p-5">
      <div class="flex items-center justify-between mb-4">
        <div class="text-[13px] font-semibold text-text-secondary uppercase tracking-[1.5px]">📁 内容项目</div>
        <div class="flex gap-2">
          <select v-model="projectFilter" class="px-2 py-1 bg-bg border border-border rounded-[6px] text-[11px] outline-none">
            <option value="">全部状态</option>
            <option value="idea">选题中</option>
            <option value="script">写稿中</option>
            <option value="recording">录制中</option>
            <option value="editing">剪辑中</option>
            <option value="cover">封面中</option>
            <option value="ready">待发布</option>
            <option value="published">已发布</option>
          </select>
        </div>
      </div>
      <div v-if="filteredProjects.length" class="flex flex-col gap-2">
        <div v-for="p in filteredProjects" :key="p.id" 
          class="flex items-center gap-3 px-3 py-2.5 bg-bg rounded-[8px] hover:bg-surface-hover transition-colors">
          <span class="text-lg">{{ statusIcon(p.status) }}</span>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium truncate">{{ p.title }}</div>
            <div class="text-[11px] text-text-secondary">{{ statusLabel(p.status) }} · {{ p.platform || '未指定' }} · {{ p.created_at?.slice(0,10) }}</div>
          </div>
          <div class="flex gap-1">
            <button v-if="p.status === 'idea'" @click="selectProjectForScript(p)" class="text-[11px] px-2 py-1 rounded-[6px] bg-accent/10 text-accent hover:bg-accent hover:text-white">
              写稿
            </button>
            <button v-if="p.status === 'script'" @click="selectProjectForVideo(p)" class="text-[11px] px-2 py-1 rounded-[6px] bg-accent/10 text-accent hover:bg-accent hover:text-white">
              剪辑
            </button>
            <button v-if="p.status === 'editing'" @click="selectProjectForCover(p)" class="text-[11px] px-2 py-1 rounded-[6px] bg-accent/10 text-accent hover:bg-accent hover:text-white">
              封面
            </button>
            <button v-if="p.status === 'cover' || p.status === 'ready'" @click="selectProjectForPublish(p)" class="text-[11px] px-2 py-1 rounded-[6px] bg-accent/10 text-accent hover:bg-accent hover:text-white">
              发布
            </button>
          </div>
        </div>
      </div>
      <div v-else class="text-center text-text-secondary text-sm py-8">暂无项目</div>
    </div>

    <!-- 新建项目弹窗 -->
    <div v-if="showNewProjectModal" class="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center" @click.self="showNewProjectModal = false">
      <div class="bg-surface border border-border rounded-[16px] p-6 w-[90%] max-w-[420px] flex flex-col gap-4">
        <h3 class="text-base font-semibold">新建内容项目</h3>
        <input v-model="newProject.title" placeholder="项目标题" 
          class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
        <select v-model="newProject.platform" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
          <option value="">选择主平台（可选）</option>
          <option value="douyin">抖音</option>
          <option value="xiaohongshu">小红书</option>
          <option value="bilibili">B站</option>
          <option value="wechat">公众号</option>
        </select>
        <select v-model="newProject.topic_id" class="px-3 py-2 bg-bg border border-border rounded-[8px] text-sm outline-none focus:border-accent">
          <option value="">关联选题（可选）</option>
          <option v-for="t in topics.filter(x => !x.used)" :key="t.id" :value="t.id">{{ t.title }}</option>
        </select>
        <div class="flex gap-2 justify-end">
          <button @click="showNewProjectModal = false" class="px-4 py-2 rounded-[8px] border border-border text-[12px] hover:bg-surface-hover">取消</button>
          <button @click="createProject" class="px-4 py-2 rounded-[8px] bg-accent text-white text-[12px] hover:opacity-90">创建</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toastVisible" class="fixed bottom-6 left-1/2 -translate-x-1/2 px-5 py-2.5 rounded-[8px] text-sm border z-[200] transition-opacity"
      :class="toastError ? 'border-danger text-danger' : 'border-border text-text bg-surface'">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || ''
const apiBase = API_BASE

// ===== 状态 =====
const activeStep = ref('topic')
const dashboard = ref({})
const topics = ref([])
const accounts = ref([])
const projects = ref([])
const projectFilter = ref('')

// 选题
const topicKeyword = ref('')
const newTopicTitle = ref('')
const topicLoading = ref(false)

// 账号
const newAccount = ref({ platform: '', account_name: '' })

// 口播稿
const scriptProjectId = ref('')
const scriptStyle = ref('口播')
const currentScript = ref('')
const scriptLoading = ref(false)
const ttsLoading = ref(false)
const currentAudioUrl = ref('')
const ttsVoiceName = ref('')

// 视频
const videoProjectId = ref('')
const editingPlan = ref('')
const videoLoading = ref(false)
const autoEditLoading = ref(false)
const capcutLoading = ref(false)
const currentVideoUrl = ref('')
const capcutGuide = ref('')

// 封面
const coverProjectId = ref('')
const coverStyle = ref('default')
const currentCoverUrl = ref('')
const coverLoading = ref(false)

// 发布
const publishProjectId = ref('')
const selectedPublishPlatforms = ref([])
const platformContents = ref(null)
const publishLoading = ref(false)
const autoPublishLoading = ref(false)
const autoPublishResults = ref(null)
const publishConfig = ref(null)

// 新建项目
const showNewProjectModal = ref(false)
const newProject = ref({ title: '', platform: '', topic_id: '' })

// Toast
const toastVisible = ref(false)
const toastMessage = ref('')
const toastError = ref(false)
let toastTimer = null

// ===== 常量 =====
const pipelineSteps = [
  { key: 'topic', label: '找选题', icon: '💡' },
  { key: 'accounts', label: '矩阵号', icon: '👥' },
  { key: 'script', label: '口播稿', icon: '📝' },
  { key: 'video', label: '视频剪辑', icon: '🎬' },
  { key: 'cover', label: '封面图', icon: '🖼️' },
  { key: 'publish', label: '多平台发布', icon: '🚀' },
]

const publishPlatforms = [
  { key: 'douyin', label: '抖音', icon: '🎵' },
  { key: 'xiaohongshu', label: '小红书', icon: '📕' },
  { key: 'bilibili', label: 'B站', icon: '📺' },
  { key: 'wechat', label: '公众号', icon: '💬' },
]

// ===== 计算属性 =====
const filteredProjects = computed(() => {
  if (!projectFilter.value) return projects.value
  return projects.value.filter(p => p.status === projectFilter.value)
})

// ===== 工具函数 =====
function showToast(msg, isError = false) {
  toastMessage.value = msg
  toastError.value = isError
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2500)
}

function platformIcon(platform) {
  const map = { douyin: '🎵', xiaohongshu: '📕', bilibili: '📺', wechat: '💬', youtube: '📺' }
  return map[platform] || '📱'
}

function platformName(key) {
  const map = { douyin: '抖音', xiaohongshu: '小红书', bilibili: 'B站', wechat: '公众号' }
  return map[key] || key
}

function statusLabel(status) {
  const map = {
    idea: '选题中', script: '写稿中', recording: '录制中',
    editing: '剪辑中', cover: '封面中', ready: '待发布', published: '已发布', archived: '已归档'
  }
  return map[status] || status
}

function statusIcon(status) {
  const map = {
    idea: '💡', script: '📝', recording: '🎙️',
    editing: '✂️', cover: '🖼️', ready: '✅', published: '🚀', archived: '📦'
  }
  return map[status] || '📄'
}

async function apiGet(path) {
  const resp = await fetch(`${API_BASE}${path}`)
  if (!resp.ok) throw new Error(await resp.text())
  return resp.json()
}

async function apiPost(path, body = {}) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!resp.ok) throw new Error(await resp.text())
  return resp.json()
}

// ===== 数据加载 =====
async function loadDashboard() {
  try {
    const data = await apiGet('/operations/dashboard')
    dashboard.value = data
  } catch (e) {
    console.error('dashboard error:', e)
  }
}

async function loadTopics() {
  try {
    const data = await apiGet('/operations/topics?unused_only=false')
    topics.value = data.topics || []
  } catch (e) {
    console.error('topics error:', e)
  }
}

async function loadAccounts() {
  try {
    const data = await apiGet('/operations/accounts')
    accounts.value = data.accounts || []
  } catch (e) {
    console.error('accounts error:', e)
  }
}

async function loadProjects() {
  try {
    const data = await apiGet('/operations/projects?limit=100')
    projects.value = data.projects || []
  } catch (e) {
    console.error('projects error:', e)
  }
}

// ===== 选题操作 =====
async function aiDiscoverTopics() {
  topicLoading.value = true
  try {
    const data = await apiPost('/operations/topics/ai-discover', { keyword: topicKeyword.value, count: 5 })
    showToast(`发现 ${data.topics?.length || 0} 个选题`)
    await loadTopics()
  } catch (e) {
    showToast('发现失败: ' + e.message, true)
  }
  topicLoading.value = false
}

async function addTopic() {
  if (!newTopicTitle.value.trim()) return
  try {
    await apiPost('/operations/topics', { title: newTopicTitle.value, source: 'manual' })
    newTopicTitle.value = ''
    showToast('选题已添加')
    await loadTopics()
  } catch (e) {
    showToast('添加失败: ' + e.message, true)
  }
}

async function createProjectFromTopic(topic) {
  try {
    const data = await apiPost('/operations/projects', { title: topic.title, topic_id: topic.id })
    showToast('项目已创建')
    await loadProjects()
    await loadTopics()
  } catch (e) {
    showToast('创建失败: ' + e.message, true)
  }
}

// ===== 账号操作 =====
async function addAccount() {
  if (!newAccount.value.platform || !newAccount.value.account_name) {
    showToast('请填写完整信息', true)
    return
  }
  try {
    await apiPost('/operations/accounts', newAccount.value)
    newAccount.value = { platform: '', account_name: '' }
    showToast('账号已添加')
    await loadAccounts()
  } catch (e) {
    showToast('添加失败: ' + e.message, true)
  }
}

// ===== 项目操作 =====
async function createProject() {
  if (!newProject.value.title.trim()) {
    showToast('请填写标题', true)
    return
  }
  try {
    const body = { title: newProject.value.title, platform: newProject.value.platform }
    if (newProject.value.topic_id) body.topic_id = parseInt(newProject.value.topic_id)
    await apiPost('/operations/projects', body)
    showToast('项目已创建')
    showNewProjectModal.value = false
    newProject.value = { title: '', platform: '', topic_id: '' }
    await loadProjects()
  } catch (e) {
    showToast('创建失败: ' + e.message, true)
  }
}

async function updateProjectStatus(projectId, status) {
  try {
    await apiPost(`/operations/projects/${projectId}/status?status=${status}`)
    showToast('状态已更新')
    await loadProjects()
  } catch (e) {
    showToast('更新失败: ' + e.message, true)
  }
}

// ===== 口播稿操作 =====
async function generateScript() {
  if (!scriptProjectId.value) return
  scriptLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${scriptProjectId.value}/script/generate`, {
      style: scriptStyle.value,
      duration: 60
    })
    currentScript.value = data.script || ''
    showToast('口播稿已生成')
    await loadProjects()
  } catch (e) {
    showToast('生成失败: ' + e.message, true)
  }
  scriptLoading.value = false
}

async function saveScript() {
  if (!scriptProjectId.value || !currentScript.value) return
  try {
    await apiPost(`/operations/projects/${scriptProjectId.value}/script/update`, {
      script_content: currentScript.value
    })
    showToast('已保存')
  } catch (e) {
    showToast('保存失败: ' + e.message, true)
  }
}

async function polishScript() {
  if (!scriptProjectId.value) return
  scriptLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${scriptProjectId.value}/script/polish`)
    currentScript.value = data.script || ''
    showToast('润色完成')
  } catch (e) {
    showToast('润色失败: ' + e.message, true)
  }
  scriptLoading.value = false
}

function selectProjectForScript(p) {
  scriptProjectId.value = p.id
  currentScript.value = ''
  activeStep.value = 'script'
}

// ===== 视频操作 =====
async function generateEditingPlan() {
  if (!videoProjectId.value) return
  videoLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${videoProjectId.value}/video/editing-plan`)
    editingPlan.value = data.editing_plan || ''
    showToast('剪辑方案已生成')
    await loadProjects()
  } catch (e) {
    showToast('生成失败: ' + e.message, true)
  }
  videoLoading.value = false
}

function selectProjectForVideo(p) {
  videoProjectId.value = p.id
  editingPlan.value = ''
  currentVideoUrl.value = ''
  capcutGuide.value = ''
  activeStep.value = 'video'
}

async function autoEditVideo() {
  if (!videoProjectId.value) return
  autoEditLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${videoProjectId.value}/auto-edit`, {
      use_tts_audio: true,
      add_subtitles: true,
      resolution: '1080p'
    })
    if (data.error) {
      showToast(data.error, true)
    } else {
      currentVideoUrl.value = data.video_url
      showToast('自动剪辑完成')
      await loadProjects()
    }
  } catch (e) {
    showToast('剪辑失败: ' + e.message, true)
  }
  autoEditLoading.value = false
}

async function capcutExport() {
  if (!videoProjectId.value) return
  capcutLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${videoProjectId.value}/video/capcut-export`)
    capcutGuide.value = data.guide
    showToast('剪映导出指南已生成')
  } catch (e) {
    showToast('生成失败: ' + e.message, true)
  }
  capcutLoading.value = false
}

// ===== 封面操作 =====
async function generateCover() {
  if (!coverProjectId.value) return
  coverLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${coverProjectId.value}/cover/generate`, {
      style: coverStyle.value
    })
    if (data.error) {
      showToast(data.error, true)
    } else {
      currentCoverUrl.value = data.cover_url
      showToast('封面已生成')
      await loadProjects()
    }
  } catch (e) {
    showToast('生成失败: ' + e.message, true)
  }
  coverLoading.value = false
}

function selectProjectForCover(p) {
  coverProjectId.value = p.id
  currentCoverUrl.value = ''
  activeStep.value = 'cover'
}

// ===== 发布操作 =====
async function publishContent() {
  if (!publishProjectId.value || !selectedPublishPlatforms.value.length) return
  publishLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${publishProjectId.value}/publish`, {
      platforms: selectedPublishPlatforms.value
    })
    platformContents.value = data.platforms
    autoPublishResults.value = null
    showToast('各平台文案已生成')
    await loadProjects()
  } catch (e) {
    showToast('生成失败: ' + e.message, true)
  }
  publishLoading.value = false
}

async function autoPublish() {
  if (!publishProjectId.value || !selectedPublishPlatforms.value.length) return
  autoPublishLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${publishProjectId.value}/auto-publish`, {
      platforms: selectedPublishPlatforms.value
    })
    autoPublishResults.value = data.results
    platformContents.value = null
    showToast(data.message)
    await loadProjects()
  } catch (e) {
    showToast('发布失败: ' + e.message, true)
  }
  autoPublishLoading.value = false
}

async function loadPublishConfig() {
  try {
    publishConfig.value = await apiGet('/operations/publish/config')
  } catch (e) {
    console.error('publish config error:', e)
  }
}

async function confirmPublished(platform) {
  try {
    await apiPost(`/operations/projects/${publishProjectId.value}/publish/confirm`, { platform })
    showToast('已标记为发布')
    await loadProjects()
  } catch (e) {
    showToast('标记失败: ' + e.message, true)
  }
}

function selectProjectForPublish(p) {
  publishProjectId.value = p.id
  platformContents.value = null
  autoPublishResults.value = null
  selectedPublishPlatforms.value = []
  activeStep.value = 'publish'
  loadPublishConfig()
}

async function generateTTS() {
  if (!scriptProjectId.value || !currentScript.value) return
  ttsLoading.value = true
  try {
    const data = await apiPost(`/operations/projects/${scriptProjectId.value}/tts/generate`, {
      voice: 'zh_dubbing_female',
      speed: 1.0
    })
    if (data.error) {
      showToast(data.error, true)
    } else {
      currentAudioUrl.value = data.audio_url
      ttsVoiceName.value = data.voice
      showToast('语音合成完成')
      await loadProjects()
    }
  } catch (e) {
    showToast('合成失败: ' + e.message, true)
  }
  ttsLoading.value = false
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    showToast('已复制')
  } catch {
    showToast('复制失败', true)
  }
}

// ===== 生命周期 =====
onMounted(() => {
  loadDashboard()
  loadTopics()
  loadAccounts()
  loadProjects()
})
</script>
