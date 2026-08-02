<template>
  <main class="space-y-6">
    <section class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-[13px] text-text-secondary">系统控制台</p>
        <h2 class="text-2xl font-bold">设置中心</h2>
      </div>
      <button
        class="rounded-lg border border-border px-3 py-2 text-sm font-medium hover:border-accent hover:text-accent disabled:opacity-50"
        :disabled="loading"
        @click="loadStatus"
      >
        {{ loading ? '正在检测...' : '刷新状态' }}
      </button>
    </section>

    <p v-if="error" class="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ error }}
    </p>

    <section v-if="catalog.length" class="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      <article v-for="category in catalog" :key="category.id" class="rounded-lg border border-border bg-surface px-4 py-3">
        <h3 class="text-sm font-semibold">{{ category.label }}</h3>
        <p class="mt-1 text-xs text-text-secondary">{{ category.items.join(' · ') }}</p>
      </article>
    </section>

    <section v-if="status" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <article v-for="card in cards" :key="card.id" class="rounded-lg border border-border bg-surface p-4">
        <div class="flex items-center justify-between gap-3">
          <h3 class="text-sm font-semibold">{{ card.title }}</h3>
          <span :class="card.ok ? 'text-emerald-600' : 'text-amber-600'" class="text-xs font-medium">
            {{ card.ok ? '可用' : '需要处理' }}
          </span>
        </div>
        <p class="mt-3 break-all text-sm text-text-secondary">{{ card.detail }}</p>
      </article>
    </section>

    <section v-if="status" class="grid gap-4 lg:grid-cols-2">
      <article class="rounded-lg border border-border bg-surface p-5 lg:col-span-2">
        <div class="flex flex-wrap items-end justify-between gap-2">
          <div><h3 class="text-base font-semibold">模型路由</h3><p class="mt-1 text-sm text-text-secondary">每项能力实际使用的服务与模型；只能选择已验证的模型。</p></div>
          <p v-if="routeMessage" class="text-sm text-text-secondary">{{ routeMessage }}</p>
        </div>
        <div class="mt-4 overflow-x-auto">
          <table class="min-w-full text-left text-sm">
            <thead class="border-b border-border text-xs text-text-secondary"><tr><th class="pb-2 pr-4">能力</th><th class="pb-2 pr-4">服务</th><th class="pb-2 pr-4">使用位置</th><th class="pb-2 pr-4">模型</th><th class="pb-2"></th></tr></thead>
            <tbody>
              <tr v-for="route in modelRoutes" :key="route.id" class="border-b border-border/70 last:border-0">
                <td class="py-3 pr-4 font-medium">{{ route.capability }}</td><td class="py-3 pr-4">{{ route.provider }}</td><td class="py-3 pr-4 text-text-secondary">{{ route.used_by.join(' · ') }}</td>
                <td class="py-3 pr-4"><select v-model="route.model" class="w-full rounded-lg border border-border bg-bg px-3 py-2"><option v-for="option in route.options" :key="option" :value="option">{{ option }}</option></select></td>
                <td class="py-3"><button class="whitespace-nowrap rounded-lg border border-border px-3 py-2 text-sm hover:border-accent hover:text-accent disabled:opacity-50" :disabled="savingRoute === route.id" @click="saveModelRoute(route)">{{ savingRoute === route.id ? '保存中...' : '保存' }}</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="rounded-lg border border-border bg-surface p-5 lg:col-span-2">
        <h3 class="text-base font-semibold">服务密钥</h3>
        <p class="mt-1 text-sm text-text-secondary">密钥只会加密保存，不会再次显示。留空的字段会保留原设置。</p>
        <div class="mt-4 grid gap-4 lg:grid-cols-3">
          <form v-for="service in serviceSettings" :key="service.id" class="rounded-lg bg-bg p-4 space-y-3" @submit.prevent="saveServiceSettings(service)">
            <div class="flex items-center justify-between gap-2"><h4 class="font-semibold">{{ service.provider }}</h4><span class="text-xs text-text-secondary">{{ service.fields.every(field => field.configured) ? '已配置' : '待填写' }}</span></div>
            <label v-for="field in service.fields" :key="field.id" class="block text-sm"><span class="text-text-secondary">{{ field.label }}</span><input v-model="serviceForms[service.id][field.id]" class="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2" :type="field.kind === 'url' ? 'url' : 'password'" :autocomplete="field.kind === 'url' ? 'url' : 'new-password'" :placeholder="field.configured ? '已保存，留空则不更改' : '请填写'"></label>
            <button class="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50" :disabled="savingService === service.id">{{ savingService === service.id ? '保存中...' : '保存服务设置' }}</button>
          </form>
        </div>
      </article>

      <article class="rounded-lg border border-border bg-surface p-5">
        <h3 class="text-base font-semibold">服务连接</h3>
        <dl class="mt-4 space-y-3 text-sm">
          <div class="flex justify-between gap-4"><dt class="text-text-secondary">本地服务</dt><dd class="break-all text-right">{{ status.services.local.address }}</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-text-secondary">内容解析</dt><dd>已就绪</dd></div>
          <div class="flex justify-between gap-4"><dt class="text-text-secondary">本地存储</dt><dd>{{ formatBytes(status.storage.bytes) }}</dd></div>
        </dl>
      </article>

      <article class="rounded-lg border border-border bg-surface p-5">
        <h3 class="text-base font-semibold">AI 配置</h3>
        <form class="mt-4 space-y-3" @submit.prevent="saveAiSettings">
          <label class="block text-sm"><span class="text-text-secondary">服务地址</span><input v-model.trim="aiForm.base_url" class="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2" type="url" required></label>
          <label class="block text-sm"><span class="text-text-secondary">模型</span><select v-model="aiForm.model" class="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2"><option value="deepseek-v4-flash">deepseek-v4-flash</option></select></label>
          <label class="block text-sm"><span class="text-text-secondary">密钥</span><input v-model="aiForm.api_key" class="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2" type="password" autocomplete="new-password" placeholder="留空则保留当前密钥"></label>
          <div class="flex flex-wrap gap-2"><button class="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white" :disabled="savingAi">保存 AI 设置</button><button v-if="status.services.ai.configured" type="button" class="rounded-lg border border-border px-3 py-2 text-sm text-red-600" @click="removeAiKey">删除密钥</button></div>
          <p v-if="aiMessage" class="text-sm text-text-secondary">{{ aiMessage }}</p>
        </form>
      </article>

      <article class="rounded-lg border border-border bg-surface p-5 lg:col-span-2">
        <h3 class="text-base font-semibold">工作区与效率</h3>
        <div class="mt-4 grid gap-3 sm:grid-cols-3">
          <div class="rounded-lg bg-bg px-4 py-3"><p class="text-xs text-text-secondary">快捷入口</p><p class="mt-1 font-semibold">{{ settings.shortcuts.length }} 项</p></div>
          <div class="rounded-lg bg-bg px-4 py-3"><p class="text-xs text-text-secondary">AI 启动器</p><p class="mt-1 font-semibold">{{ settings.launcherItems.length }} 项</p></div>
          <div class="rounded-lg bg-bg px-4 py-3"><p class="text-xs text-text-secondary">自定义命令</p><p class="mt-1 font-semibold">{{ Object.keys(settings.customCommands).length }} 项</p></div>
        </div>
        <div class="mt-5 grid gap-5 lg:grid-cols-2">
          <section>
            <div class="flex items-center justify-between"><h4 class="font-semibold">快捷入口</h4><span class="text-xs text-text-secondary">{{ settings.shortcuts.length }} 项</span></div>
            <ul class="mt-3 space-y-2">
              <li v-for="(item, index) in settings.shortcuts" :key="`${item.name}-${item.url}`" class="flex items-center gap-3 rounded-lg bg-bg px-3 py-2 text-sm">
                <span>{{ item.name }}</span><span class="min-w-0 flex-1 truncate text-text-secondary">{{ item.url }}</span>
                <button class="text-text-secondary hover:text-red-600" :aria-label="`移除 ${item.name}`" @click="settings.removeShortcut(index)">×</button>
              </li>
            </ul>
            <form class="mt-3 grid gap-2 sm:grid-cols-3" @submit.prevent="addShortcut">
              <input v-model.trim="shortcutForm.name" class="rounded-lg border border-border bg-bg px-3 py-2 text-sm" placeholder="名称" aria-label="快捷入口名称">
              <input v-model.trim="shortcutForm.url" class="rounded-lg border border-border bg-bg px-3 py-2 text-sm" placeholder="https://..." aria-label="快捷入口地址">
              <button class="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50" :disabled="!shortcutForm.name || !shortcutForm.url">添加快捷入口</button>
            </form>
          </section>
          <section>
            <div class="flex items-center justify-between"><h4 class="font-semibold">AI 启动器</h4><span class="text-xs text-text-secondary">{{ settings.launcherItems.length }} 项</span></div>
            <ul class="mt-3 space-y-2">
              <li v-for="(item, index) in settings.launcherItems" :key="`${item.name}-${item.url}`" class="flex items-center gap-3 rounded-lg bg-bg px-3 py-2 text-sm">
                <span>{{ item.name }}</span><span class="min-w-0 flex-1 truncate text-text-secondary">{{ item.url }}</span>
                <button class="text-text-secondary hover:text-red-600" :aria-label="`移除 ${item.name}`" @click="settings.removeLauncher(index)">×</button>
              </li>
            </ul>
            <form class="mt-3 grid gap-2 sm:grid-cols-3" @submit.prevent="addLauncher">
              <input v-model.trim="launcherForm.name" class="rounded-lg border border-border bg-bg px-3 py-2 text-sm" placeholder="名称" aria-label="启动器名称">
              <input v-model.trim="launcherForm.url" class="rounded-lg border border-border bg-bg px-3 py-2 text-sm" placeholder="https://..." aria-label="启动器地址">
              <button class="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50" :disabled="!launcherForm.name || !launcherForm.url">添加启动器</button>
            </form>
          </section>
        </div>
      </article>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useSettingsStore } from '../stores/settings.js'

const settings = useSettingsStore()
const status = ref(null)
const error = ref('')
const loading = ref(false)
const shortcutForm = ref({ name: '', url: '' })
const launcherForm = ref({ name: '', url: '' })
const aiForm = ref({ base_url: '', model: '', api_key: '' })
const savingAi = ref(false)
const aiMessage = ref('')
const catalog = ref([])
const modelRoutes = ref([])
const serviceSettings = ref([])
const serviceForms = ref({})
const savingRoute = ref('')
const savingService = ref('')
const routeMessage = ref('')

const cards = computed(() => {
  if (!status.value) return []
  const { services, storage } = status.value
  return [
    { id: 'ai', title: 'AI 服务', ok: services.ai.status === 'available', detail: services.ai.model },
    { id: 'content', title: '内容解析', ok: services.content.status === 'available', detail: services.content.label },
    { id: 'local', title: '本地服务', ok: services.local.status === 'available', detail: services.local.address },
    { id: 'storage', title: '本地存储', ok: true, detail: formatBytes(storage.bytes) }
  ]
})

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function addShortcut() {
  if (!shortcutForm.value.name || !shortcutForm.value.url) return
  settings.addShortcut({ ...shortcutForm.value, icon: '+' })
  shortcutForm.value = { name: '', url: '' }
}

function addLauncher() {
  if (!launcherForm.value.name || !launcherForm.value.url) return
  settings.addLauncher({ ...launcherForm.value, icon: '+' })
  launcherForm.value = { name: '', url: '' }
}

async function loadStatus() {
  loading.value = true
  error.value = ''
  try {
    status.value = await settings.getSettingsStatus()
    aiForm.value.base_url = status.value.services.ai.base_url
    aiForm.value.model = status.value.services.ai.model
    const catalogResponse = await settings.getSettingsCatalog()
    catalog.value = catalogResponse.categories || []
    const routesResponse = await settings.getModelRoutes()
    modelRoutes.value = routesResponse.routes || []
    const servicesResponse = await settings.getServiceSettings()
    serviceSettings.value = servicesResponse.services || []
    serviceForms.value = Object.fromEntries(serviceSettings.value.map(service => [service.id, Object.fromEntries(service.fields.map(field => [field.id, '']))]))
  } catch {
    error.value = '暂时无法连接本地服务，请确认服务已启动后重试。'
  } finally {
    loading.value = false
  }
}

async function saveModelRoute(route) {
  savingRoute.value = route.id
  routeMessage.value = ''
  try {
    const saved = await settings.saveModelRoute(route.id, { model: route.model })
    route.model = saved.model
    routeMessage.value = `${route.capability} 已切换为 ${saved.model}。`
  } catch {
    routeMessage.value = '保存失败：只能选择此能力已验证的模型。'
  } finally {
    savingRoute.value = ''
  }
}

async function saveServiceSettings(service) {
  savingService.value = service.id
  try {
    await settings.saveServiceSettings(service.id, serviceForms.value[service.id])
    service.fields.forEach(field => { field.configured = field.configured || Boolean(serviceForms.value[service.id][field.id]) })
    serviceForms.value[service.id] = Object.fromEntries(service.fields.map(field => [field.id, '']))
  } catch {
    error.value = '服务设置保存失败，请检查填写内容。'
  } finally {
    savingService.value = ''
  }
}

async function saveAiSettings() {
  savingAi.value = true
  aiMessage.value = ''
  try {
    const result = await settings.saveAiSettings({ ...aiForm.value })
    aiForm.value.api_key = ''
    status.value.services.ai.configured = result.api_key.configured
    status.value.services.ai.base_url = result.base_url
    status.value.services.ai.model = result.model
    aiMessage.value = '已加密保存。'
  } catch {
    aiMessage.value = '保存失败，请检查填写内容。'
  } finally {
    savingAi.value = false
  }
}

async function removeAiKey() {
  if (!window.confirm('删除后 AI 功能将停止，确认删除吗？')) return
  const result = await settings.deleteAiKey()
  status.value.services.ai.configured = result.api_key.configured
  aiMessage.value = '密钥已删除。'
}

onMounted(loadStatus)
</script>
