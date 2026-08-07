const ENVIRONMENT_PATH = '/api/workbench/environment'
const ROADMAP_PATH = '/api/workbench/roadmap'

const allowedEnvironmentStatuses = new Set(['ok', 'degraded', 'error'])
const allowedRoadmapStatuses = new Set(['available', 'missing', 'error'])

export class WorkbenchApiError extends Error {
  constructor(message, details = {}) {
    super(message)
    this.name = 'WorkbenchApiError'
    this.status = details.status ?? 0
    this.code = details.code ?? 'WB_UPSTREAM_UNAVAILABLE'
    this.retryable = details.retryable ?? this.status >= 500
    this.requestId = details.requestId ?? ''
  }
}

function getApiBase() {
  const configured = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE
  if (configured) return configured.replace(/\/$/, '')

  try {
    const saved = window.localStorage.getItem('api_base')
    if (saved) return saved.replace(/\/$/, '')
  } catch {
    // Storage may be unavailable in a restricted browser context.
  }

  if (typeof window !== 'undefined' && window.electronAPI) return 'http://localhost:8741'
  return typeof window !== 'undefined' ? window.location.origin : ''
}

function requestId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `wb-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function getRequestUrl(path) {
  return `${getApiBase()}${path}`
}

async function readResponse(response) {
  try {
    return await response.json()
  } catch {
    throw new WorkbenchApiError('工作台服务返回了无法读取的响应', {
      status: response.status,
      code: 'WB_UPSTREAM_UNAVAILABLE',
      retryable: response.status >= 500,
    })
  }
}

function unwrapResponse(body, response) {
  if (!body || typeof body !== 'object') {
    throw new WorkbenchApiError('工作台服务返回格式不正确', {
      status: response.status,
      code: 'WB_SCHEMA_MISMATCH',
      retryable: false,
    })
  }

  if (body.ok === false) {
    throw new WorkbenchApiError(body.error?.message || '工作台请求失败', {
      status: response.status,
      code: body.error?.code || 'WB_UPSTREAM_UNAVAILABLE',
      retryable: body.error?.retryable,
      requestId: body.meta?.request_id,
    })
  }

  const data = body.ok === true && Object.prototype.hasOwnProperty.call(body, 'data')
    ? body.data
    : body

  if (!response.ok) {
    throw new WorkbenchApiError(body.error?.message || '工作台请求失败', {
      status: response.status,
      code: body.error?.code || 'WB_UPSTREAM_UNAVAILABLE',
      retryable: body.error?.retryable,
      requestId: body.meta?.request_id,
    })
  }
  return data
}

async function request(path, options = {}) {
  const response = await fetch(getRequestUrl(path), {
    ...options,
    headers: {
      Accept: 'application/json',
      'X-Request-ID': requestId(),
      ...(options.headers || {}),
    },
  })
  const body = await readResponse(response)
  return unwrapResponse(body, response)
}

function assertObject(value, code = 'WB_SCHEMA_MISMATCH') {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new WorkbenchApiError('工作台服务返回格式不正确', { code, retryable: false })
  }
  return value
}

export async function getEnvironment() {
  const data = assertObject(await request(ENVIRONMENT_PATH))
  if (!allowedEnvironmentStatuses.has(data.status)) {
    throw new WorkbenchApiError('环境信息格式不正确', { code: 'WB_SCHEMA_MISMATCH', retryable: false })
  }
  return data
}

export async function getRoadmap() {
  const data = assertObject(await request(ROADMAP_PATH))
  if (!allowedRoadmapStatuses.has(data.status) || typeof data.missing !== 'boolean') {
    throw new WorkbenchApiError('项目规划格式不正确', { code: 'WB_SCHEMA_MISMATCH', retryable: false })
  }
  return data
}

export const fetchEnvironment = getEnvironment
export const fetchRoadmap = getRoadmap
