const DEFAULT_ERROR_MESSAGE = '工作台服务暂时不可用，请稍后重试。'

function createRequestId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `wb-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function getApiBase() {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured) return configured.replace(/\/+$/, '')

  if (typeof window !== 'undefined') {
    const stored = window.localStorage?.getItem('api_base')
    if (stored) return stored.replace(/\/+$/, '')
    return window.location.origin
  }

  return ''
}

function errorFromPayload(payload, status, requestId) {
  const error = payload?.error
  return new WorkbenchApiError({
    status,
    code: error?.code || (status >= 500 ? 'WB_UPSTREAM_UNAVAILABLE' : 'WB_REQUEST_FAILED'),
    message: error?.message || DEFAULT_ERROR_MESSAGE,
    details: error?.details || {},
    retryable: error?.retryable ?? status >= 429,
    requestId: payload?.meta?.request_id || requestId,
  })
}

export class WorkbenchApiError extends Error {
  constructor({ status = 0, code = 'WB_REQUEST_FAILED', message = DEFAULT_ERROR_MESSAGE, details = {}, retryable = false, requestId = '' } = {}) {
    super(message)
    this.name = 'WorkbenchApiError'
    this.status = status
    this.code = code
    this.details = details
    this.retryable = retryable
    this.requestId = requestId
  }
}

async function parseResponse(response, requestId) {
  const raw = await response.text()
  let payload

  try {
    payload = raw ? JSON.parse(raw) : null
  } catch {
    throw new WorkbenchApiError({
      status: response.status,
      code: 'WB_UPSTREAM_UNAVAILABLE',
      message: DEFAULT_ERROR_MESSAGE,
      retryable: true,
      requestId,
    })
  }

  if (!response.ok || payload?.ok === false) {
    throw errorFromPayload(payload, response.status, requestId)
  }
  if (!payload || payload.ok !== true || !('data' in payload)) {
    throw new WorkbenchApiError({
      status: response.status,
      code: 'WB_SCHEMA_MISMATCH',
      message: '工作台返回的数据格式无法识别。',
      retryable: false,
      requestId: payload?.meta?.request_id || requestId,
    })
  }
  return payload.data
}

async function request(path, { signal } = {}) {
  const requestId = createRequestId()
  const electronApi = typeof window !== 'undefined' ? window.electronAPI : null

  if (electronApi?.apiRequest) {
    let result
    try {
      result = await electronApi.apiRequest('GET', path)
    } catch (error) {
      if (error?.name === 'AbortError') throw error
      throw new WorkbenchApiError({ status: 0, retryable: true, requestId, message: DEFAULT_ERROR_MESSAGE })
    }
    if (result?.error) {
      const payload = typeof result.error === 'object' ? { error: result.error } : { error: { message: result.error } }
      throw errorFromPayload(payload, 0, requestId)
    }
    return parseEnvelope(result?.data ?? result, requestId)
  }

  let response
  try {
    response = await fetch(`${getApiBase()}${path}`, {
      method: 'GET',
      signal,
      headers: {
        Accept: 'application/json',
        'X-Request-ID': requestId,
      },
    })
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new WorkbenchApiError({ status: 0, retryable: true, requestId, message: DEFAULT_ERROR_MESSAGE })
  }
  return parseResponse(response, requestId)
}

function parseEnvelope(payload, requestId) {
  if (payload?.ok === false) throw errorFromPayload(payload, 0, requestId)
  if (!payload || payload.ok !== true || !('data' in payload)) {
    throw new WorkbenchApiError({
      status: 0,
      code: 'WB_SCHEMA_MISMATCH',
      message: '工作台返回的数据格式无法识别。',
      requestId,
    })
  }
  return payload.data
}

function appendParam(params, name, value) {
  if (value === undefined || value === null || value === '') return
  params.set(name, String(value))
}

export function getCases(filters = {}, signal) {
  const params = new URLSearchParams()
  appendParam(params, 'status', filters.status)
  appendParam(params, 'task_type', filters.task_type)
  appendParam(params, 'risk_level', filters.risk_level)
  appendParam(params, 'feature_code', filters.feature_code)
  appendParam(params, 'q', filters.q)
  appendParam(params, 'page', filters.page || 1)
  appendParam(params, 'page_size', filters.page_size || 20)
  appendParam(params, 'sort_by', filters.sort_by || 'updated_at')
  appendParam(params, 'sort_order', filters.sort_order || 'desc')
  if (filters.include_archived === true) params.set('include_archived', 'true')
  return request(`/api/workbench/cases?${params.toString()}`, { signal })
}

export function getCase(caseId, signal) {
  if (!caseId) {
    return Promise.reject(new WorkbenchApiError({
      code: 'WB_INVALID_QUERY',
      message: '缺少案件 ID。',
      retryable: false,
    }))
  }
  return request(`/api/workbench/cases/${encodeURIComponent(caseId)}`, { signal })
}

export const listCases = getCases

export const workbenchApi = {
  getCases,
  listCases,
  getCase,
}
