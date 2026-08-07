const OVERVIEW_PATH = '/api/workbench/overview'
const DEFAULT_ERROR_MESSAGE = '工作台总览暂时不可用，请稍后重试。'

export class WorkbenchOverviewError extends Error {
  constructor({
    status = 0,
    code = 'WB_REQUEST_FAILED',
    message = DEFAULT_ERROR_MESSAGE,
    details = null,
    retryable = false,
    requestId = '',
  } = {}) {
    super(message)
    this.name = 'WorkbenchOverviewError'
    this.status = status
    this.code = code
    this.details = details
    this.retryable = retryable
    this.requestId = requestId
  }
}

function createRequestId() {
  if (typeof globalThis.crypto?.randomUUID === 'function') {
    return globalThis.crypto.randomUUID()
  }
  return `wb-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function getApiBase(apiBase) {
  if (apiBase !== undefined && apiBase !== null) {
    return String(apiBase).replace(/\/+$/, '')
  }

  const configured = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE
  if (configured) return configured.replace(/\/+$/, '')

  if (typeof window !== 'undefined') {
    try {
      const saved = window.localStorage.getItem('api_base')
      if (saved) return saved.replace(/\/+$/, '')
    } catch {
      // Storage may be unavailable in a restricted browser context.
    }
    return window.location.origin
  }

  return ''
}

function errorFromPayload(payload, { status, requestId }) {
  const error = payload?.error || payload?.detail
  return new WorkbenchOverviewError({
    status,
    code: error?.code || (status >= 500 ? 'WB_UPSTREAM_UNAVAILABLE' : 'WB_REQUEST_FAILED'),
    message: error?.message || DEFAULT_ERROR_MESSAGE,
    details: error?.details || null,
    retryable: error?.retryable ?? status >= 429,
    requestId: payload?.meta?.request_id || requestId,
  })
}

function unwrapEnvelope(payload, { status = 0, requestId = '' } = {}) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new WorkbenchOverviewError({
      status,
      code: 'WB_SCHEMA_MISMATCH',
      message: '工作台总览返回的数据格式无法识别。',
      retryable: false,
      requestId,
    })
  }

  if (payload.ok === false) throw errorFromPayload(payload, { status, requestId })

  if (payload.ok !== true || !Object.prototype.hasOwnProperty.call(payload, 'data')) {
    throw new WorkbenchOverviewError({
      status,
      code: 'WB_SCHEMA_MISMATCH',
      message: '工作台总览返回的数据格式无法识别。',
      retryable: false,
      requestId: payload.meta?.request_id || requestId,
    })
  }

  if (!payload.data || typeof payload.data !== 'object' || Array.isArray(payload.data)) {
    throw new WorkbenchOverviewError({
      status,
      code: 'WB_SCHEMA_MISMATCH',
      message: '工作台总览数据为空或格式不正确。',
      retryable: false,
      requestId: payload.meta?.request_id || requestId,
    })
  }

  return payload.data
}

async function parseResponse(response, requestId) {
  const raw = await response.text()
  let payload = null

  try {
    payload = raw ? JSON.parse(raw) : null
  } catch {
    throw new WorkbenchOverviewError({
      status: response.status,
      code: 'WB_UPSTREAM_UNAVAILABLE',
      message: DEFAULT_ERROR_MESSAGE,
      retryable: true,
      requestId,
    })
  }

  if (!response.ok) throw errorFromPayload(payload, { status: response.status, requestId })
  return unwrapEnvelope(payload, { status: response.status, requestId })
}

async function requestOverview({ apiBase, signal } = {}) {
  const requestId = createRequestId()
  const electronApi = typeof window !== 'undefined' ? window.electronAPI : null

  if (electronApi?.apiRequest) {
    let result
    try {
      result = await electronApi.apiRequest('GET', OVERVIEW_PATH)
    } catch (cause) {
      if (cause?.name === 'AbortError') throw cause
      throw new WorkbenchOverviewError({
        status: 0,
        code: 'WB_NETWORK_ERROR',
        message: DEFAULT_ERROR_MESSAGE,
        retryable: true,
        requestId,
      })
    }
    if (result?.error) {
      const payload = typeof result.error === 'object'
        ? { error: result.error }
        : { error: { message: result.error } }
      throw errorFromPayload(payload, { status: 0, requestId })
    }
    return unwrapEnvelope(result?.data ?? result, { status: 200, requestId })
  }

  let response
  try {
    response = await fetch(`${getApiBase(apiBase)}${OVERVIEW_PATH}`, {
      method: 'GET',
      signal,
      headers: {
        Accept: 'application/json',
        'X-Request-ID': requestId,
      },
    })
  } catch (cause) {
    if (cause?.name === 'AbortError') throw cause
    throw new WorkbenchOverviewError({
      status: 0,
      code: 'WB_NETWORK_ERROR',
      message: DEFAULT_ERROR_MESSAGE,
      retryable: true,
      requestId,
    })
  }

  return parseResponse(response, requestId)
}

export function getOverview(options = {}) {
  return requestOverview(options)
}

export const fetchOverview = getOverview
