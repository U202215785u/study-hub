const { app, BrowserWindow, shell, ipcMain } = require('electron')
const { join } = require('path')
const { spawn } = require('child_process')
const http = require('http')
const fs = require('fs')
const os = require('os')
const Store = require('electron-store')

// ===== 持久化存储 =====
const store = new Store({
  name: 'study-hub-settings',
  defaults: {
    apiBase: 'http://localhost:8741',
    autoExtract: true,
    customAdapters: {},
    customSelectors: {}
  }
})

// ===== 路径 =====
const PROJECT_ROOT = join(__dirname, '..')
const FRONTEND_DIST = join(PROJECT_ROOT, 'frontend', 'dist')
const BACKEND_DIR = join(PROJECT_ROOT, 'backend')

// ===== 后端管理 =====
let backendProcess = null
let backendPort = 8741
let backendRunning = false
let backendPid = null

function findPython() {
  const candidates = []
  if (process.platform === 'win32') {
    const username = os.userInfo().username
    candidates.push(
      `C:\\Users\\${username}\\AppData\\Local\\Programs\\Python\\Python312\\python.exe`,
      `C:\\Users\\${username}\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`,
      `C:\\Python312\\python.exe`,
      join(PROJECT_ROOT, 'venv', 'Scripts', 'python.exe'),
      'python', 'python3'
    )
  } else {
    candidates.push(
      '/usr/local/bin/python3', '/usr/bin/python3',
      join(PROJECT_ROOT, 'venv', 'bin', 'python3'),
      'python3', 'python'
    )
  }
  for (const c of candidates) {
    try { if (fs.existsSync(c)) { console.log('[backend] Python:', c); return c } } catch {}
  }
  return process.platform === 'win32' ? 'python' : 'python3'
}

function sanitizePidFile() {
  const pidFile = join(BACKEND_DIR, 'data', 'server.pid')
  if (!fs.existsSync(pidFile)) return
  try {
    const pid = parseInt(fs.readFileSync(pidFile, 'utf8').trim(), 10)
    try { process.kill(pid, 0) } catch { fs.unlinkSync(pidFile); console.log('[backend] 清理过期PID') }
  } catch { try { fs.unlinkSync(pidFile) } catch {} }
}

function healthCheck(timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const check = () => {
      const req = http.get(`http://localhost:${backendPort}/health`, (res) => {
        if (res.statusCode === 200) resolve(true); else retry()
      })
      req.on('error', () => retry())
      req.setTimeout(2000, () => { req.destroy(); retry() })
    }
    const retry = () => {
      if (Date.now() - start > timeoutMs) reject(new Error(`后端启动超时`))
      else setTimeout(check, 500)
    }
    check()
  })
}

async function startBackend() {
  const envFile = join(BACKEND_DIR, '.env')
  if (fs.existsSync(envFile)) {
    const m = fs.readFileSync(envFile, 'utf8').match(/PORT=(\d+)/)
    if (m) backendPort = parseInt(m[1], 10)
  }
  sanitizePidFile()
  const pythonPath = findPython()

  if (!fs.existsSync(join(BACKEND_DIR, 'data'))) {
    fs.mkdirSync(join(BACKEND_DIR, 'data'), { recursive: true })
  }

  console.log(`[backend] 启动 ${pythonPath} main.py (端口 ${backendPort})`)
  backendProcess = spawn(pythonPath, ['main.py'], {
    cwd: BACKEND_DIR,
    env: { ...process.env, PORT: String(backendPort), PYTHONUNBUFFERED: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true
  })
  backendPid = backendProcess.pid
  console.log(`[backend] PID: ${backendPid}`)

  backendProcess.stdout.on('data', d => {
    d.toString().trim().split('\n').forEach(l => { if (l) console.log(`[backend] ${l}`) })
  })
  backendProcess.stderr.on('data', d => {
    d.toString().trim().split('\n').forEach(l => { if (l) console.error(`[backend:err] ${l}`) })
  })
  backendProcess.on('exit', (code) => {
    console.log(`[backend] 退出 code=${code}`)
    backendRunning = false; backendProcess = null; backendPid = null
  })
  backendProcess.on('error', (err) => {
    console.error(`[backend] 错误:`, err.message)
    backendRunning = false; backendProcess = null; backendPid = null
  })

  try {
    await healthCheck()
    backendRunning = true
    console.log('[backend] ✅ 已就绪')
  } catch (err) {
    console.error(`[backend] ❌ ${err.message}`)
    backendRunning = false
  }
}

async function stopBackend() {
  if (!backendProcess) return
  console.log('[backend] 正在停止…')
  return new Promise(resolve => {
    const killTimeout = setTimeout(() => {
      try { backendProcess.kill('SIGKILL') } catch {}
      backendProcess = null; backendPid = null; backendRunning = false
      resolve()
    }, 5000)
    backendProcess.on('exit', () => {
      clearTimeout(killTimeout)
      backendProcess = null; backendPid = null; backendRunning = false
      console.log('[backend] 已停止')
      resolve()
    })
    try {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', String(backendPid), '/f', '/t'], { windowsHide: true })
      } else {
        backendProcess.kill('SIGTERM')
      }
    } catch {}
  })
}

// ===== 主窗口 =====
let mainWindow = null

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400, height: 900,
    minWidth: 1024, minHeight: 700,
    title: '学习中枢',
    backgroundColor: '#0f0f14',
    show: false,
    webPreferences: {
      preload: join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webviewTag: true
    }
  })

  // 拦截 window.open / <a target="_blank"> → 系统浏览器
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//.test(url)) shell.openExternal(url)
    return { action: 'deny' }
  })

  // 加载前端
  const indexPath = join(FRONTEND_DIST, 'index.html')
  if (fs.existsSync(indexPath)) {
    mainWindow.loadFile(indexPath)
    console.log('[window] 加载:', indexPath)
  } else {
    console.warn('[window] 前端未构建，尝试 http://localhost:5173')
    mainWindow.loadURL('http://localhost:5173')
  }

  mainWindow.once('ready-to-show', () => mainWindow.show())
  mainWindow.on('closed', () => { mainWindow = null })
}

// ===== IPC 处理器 =====
function registerIpcHandlers() {
  // API 代理
  ipcMain.handle('api-request', async (event, { method, path, body }) => {
    const apiBase = store.get('apiBase', 'http://localhost:8741').replace(/\/+$/, '')
    const url = `${apiBase}${path}`
    try {
      const opts = { method: method || 'GET', headers: {} }
      if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        opts.headers['Content-Type'] = 'application/json'
        opts.body = JSON.stringify(body)
      }
      const resp = await fetch(url, opts)
      const data = await resp.json()
      if (!resp.ok) return { error: data.error || data.detail || `HTTP ${resp.status}` }
      if (data.error) return { error: data.error }
      return { data }
    } catch (err) {
      return { error: `无法连接后端: ${err.message}` }
    }
  })

  // 文件上传
  ipcMain.handle('api-upload', async (event, path, formData) => {
    // FormData 直接从 renderer 传过来比较复杂，这里先返回错误提示用 fetch 降级
    return { error: 'upload-via-ipc-not-supported' }
  })

  // 设置读写
  ipcMain.handle('get-setting', (e, key) => store.get(key))
  ipcMain.handle('set-setting', (e, key, value) => { store.set(key, value); return true })
  ipcMain.handle('delete-setting', (e, key) => { store.delete(key); return true })

  // 系统浏览器
  ipcMain.handle('open-external', async (e, url) => {
    if (/^https?:\/\//.test(url)) { await shell.openExternal(url); return true }
    return false
  })

  // 后端状态
  ipcMain.handle('get-backend-status', () => ({
    running: backendRunning, port: backendPort, pid: backendPid
  }))

  // 应用信息
  ipcMain.handle('get-app-info', () => ({
    version: require('./package.json').version,
    platform: process.platform, arch: process.arch,
    electronVersion: process.versions.electron
  }))
}

// ===== 生命周期 =====
app.whenReady().then(async () => {
  registerIpcHandlers()
  await startBackend()
  createMainWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', async () => {
  await stopBackend()
})
