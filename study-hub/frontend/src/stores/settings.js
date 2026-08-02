import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  // API 基地址：优先使用环境变量，其次 Electron 内直连，最后视 DEV 模式决定
  const apiBase = ref(
    import.meta.env.VITE_API_BASE ||
    (typeof window !== 'undefined' && window.electronAPI ? 'http://localhost:8741' : '') ||
    (import.meta.env.DEV ? '/api' : 'http://localhost:8741')
  )

  const shortcuts = ref(loadFromStorage('shortcuts', [
    { name: '抖音', url: 'https://www.douyin.com', icon: '🎵' },
    { name: 'GitHub', url: 'https://github.com', icon: '🐙' },
    { name: 'VSCode', url: 'https://vscode.dev', icon: '💻' },
    { name: 'B站', url: 'https://www.bilibili.com', icon: '📺' },
    { name: '翻译', url: 'https://translate.google.com', icon: '🌐' },
    { name: 'Gmail', url: 'https://mail.google.com', icon: '📧' },
  ]))

  const launcherItems = ref(loadFromStorage('ais', [
    { name: 'Claude', url: 'https://claude.ai', icon: '🧠' },
    { name: 'ChatGPT', url: 'https://chat.openai.com', icon: '🤖' },
    { name: 'DeepSeek', url: 'https://chat.deepseek.com', icon: '🔮' },
    { name: 'Kimi', url: 'https://kimi.moonshot.cn', icon: '🌙' },
  ]))

  const customCommands = ref(loadFromStorage('commands', {}))
  const guideDone = ref(localStorage.getItem('guide_done') === '1')

  function saveToStorage(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)) } catch {}
  }

  function loadFromStorage(key, def) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : def }
    catch { return def }
  }

  function addShortcut(s) { shortcuts.value.push(s); saveToStorage('shortcuts', shortcuts.value) }
  function removeShortcut(i) { shortcuts.value.splice(i, 1); saveToStorage('shortcuts', shortcuts.value) }
  function addLauncher(item) { launcherItems.value.push(item); saveToStorage('ais', launcherItems.value) }
  function removeLauncher(i) { launcherItems.value.splice(i, 1); saveToStorage('ais', launcherItems.value) }

  // Electron IPC 可用时通过主进程代理请求，否则直接用 fetch
  const _electronAPI = typeof window !== 'undefined' ? window.electronAPI : null

  async function apiGet(path) {
    if (_electronAPI) {
      const result = await _electronAPI.apiRequest('GET', path)
      if (result.error) throw new Error(result.error)
      return result.data
    }
    const res = await fetch(`${apiBase.value}${path}`)
    return res.json()
  }

  async function apiPost(path, body) {
    if (_electronAPI) {
      const result = await _electronAPI.apiRequest('POST', path, body)
      if (result.error) throw new Error(result.error)
      return result.data
    }
    const res = await fetch(`${apiBase.value}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    return res.json()
  }

  async function apiDelete(path) {
    if (_electronAPI) {
      const result = await _electronAPI.apiRequest('DELETE', path)
      if (result.error) throw new Error(result.error)
      return result.data
    }
    const res = await fetch(`${apiBase.value}${path}`, { method: 'DELETE' })
    return res.json()
  }

  async function apiPut(path, body) {
    if (_electronAPI) {
      const result = await _electronAPI.apiRequest('PUT', path, body)
      if (result.error) throw new Error(result.error)
      return result.data
    }
    const res = await fetch(`${apiBase.value}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    return res.json()
  }

  async function apiUpload(path, formData) {
    // FormData 无法通过 IPC 序列化，始终用直接 fetch
    // Electron 中 BrowserWindow 的 webSecurity=false 允许直连 localhost
    const res = await fetch(`${apiBase.value}${path}`, { method: 'POST', body: formData })
    return res.json()
  }

  function getSettingsStatus() { return apiGet('/settings/status') }
  function saveAiSettings(payload) { return apiPut('/settings/ai', payload) }
  function deleteAiKey() { return apiDelete('/settings/ai/key') }
  function getSettingsCatalog() { return apiGet('/settings/catalog') }
  function getModelRoutes() { return apiGet('/settings/model-routes') }
  function saveModelRoute(id, payload) { return apiPut(`/settings/model-routes/${id}`, payload) }
  function getServiceSettings() { return apiGet('/settings/services') }
  function saveServiceSettings(id, values) { return apiPut(`/settings/services/${id}`, { values }) }

  return { apiBase, shortcuts, launcherItems, customCommands, guideDone,
           addShortcut, removeShortcut, addLauncher, removeLauncher,
           saveToStorage, loadFromStorage,
           apiGet, apiPost, apiDelete, apiPut, apiUpload,
           getSettingsStatus, saveAiSettings, deleteAiKey, getSettingsCatalog,
           getModelRoutes, saveModelRoute, getServiceSettings, saveServiceSettings }
})
