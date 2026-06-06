const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  // API 请求代理
  apiRequest: (method, path, body) =>
    ipcRenderer.invoke('api-request', { method, path, body }),

  // 文件上传 (降级到直接 fetch)
  apiUpload: (path, formData) =>
    ipcRenderer.invoke('api-upload', path, formData),

  // 设置管理
  getSetting: (key) => ipcRenderer.invoke('get-setting', key),
  setSetting: (key, value) => ipcRenderer.invoke('set-setting', key, value),
  deleteSetting: (key) => ipcRenderer.invoke('delete-setting', key),

  // 系统浏览器
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // 后端状态
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),

  // 应用信息
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),

  // 环境标识
  isElectron: true
})
