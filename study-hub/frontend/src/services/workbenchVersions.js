const VERSIONS_PATH = '/api/workbench/versions'
const TEST_VERSIONS_PATH = '/api/workbench/test-versions'

const DEFAULT_ERROR_MESSAGE = '工作台服务暂时不可用，请稍后重试。'

export class WorkbenchVersionsApiError extends Error {
  constructor({
    status = 0,
    code = 'WB_REQUEST_FAILED',
    message = DEFAULT_ERROR_MESSAGE,
    details = {},
    retryable = false,
    requestId = '',
  } = {}) {
    super(message)
    this.name = 'WorkbenchVersionsApiError'
    this.status = status
    this.code = code
    this.details = details
    this.retryable = retryable
    this.requestId = requestId
  }
}

function createRequestId() {
  if (typeof globalThis.crypto?.randomUUID === 'function') return globalThis.crypto.randomUUID()
  return `wb-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function createIdempotencyKey(testVersionId) {
  return `workbench-release-approval-${testVersionId}-${createRequestId()}`
}

function getApiBase(apiBase) {
  if (apiBase !== undefined && apiBase !== null) return String(apiBase).replace(/\/+$/, '')

  const configured = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE
  if (configured) return configured.replace(/\/+$/, '')

  if (typeof window !== 'undefined') {
    const saved = window.localStorage?.getItem('api_base')
    if (saved) return saved.replace(/\/+$/, '')
    return window.location.origin
  }

  return ''
}

async function readPayload(response, requestId) {
  const raw = await response.text()
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    throw new WorkbenchVersionsApiError({
      status: response.status,
      code: 'WB_UPSTREAM_UNAVAILABLE',
      retryable: true,
      requestId,
    })
  }
}

function errorFromPayload(payload, response, requestId) {
  const error = payload?.error || payload?.detail || {}
  return new WorkbenchVersionsApiError({
    status: response.status,
    code: error.code || (response.status === 409 ? 'WB_STATE_CONFLICT' : 'WB_REQUEST_FAILED'),
    message: error.message || (typeof error === 'string' ? error : DEFAULT_ERROR_MESSAGE),
    details: error.details || {},
    retryable: error.retryable ?? response.status >= 429,
    requestId: payload?.meta?.request_id || requestId,
  })
}

function unwrapPayload(payload, response, requestId) {
  if (!response.ok || payload?.ok === false) throw errorFromPayload(payload, response, requestId)
  if (payload?.ok === true) {
    if (!Object.prototype.hasOwnProperty.call(payload, 'data')) {
      throw new WorkbenchVersionsApiError({
        status: response.status,
        code: 'WB_SCHEMA_MISMATCH',
        message: '工作台返回的数据格式无法识别。',
        requestId: payload?.meta?.request_id || requestId,
      })
    }
    return payload.data
  }
  return payload
}

async function request(path, { method = 'GET', body, apiBase, idempotencyKey, signal } = {}) {
  const requestId = createRequestId()
  const headers = {
    Accept: 'application/json',
    'X-Request-ID': requestId,
  }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (method === 'POST') headers['Idempotency-Key'] = idempotencyKey || createIdempotencyKey(path)

  let response
  try {
    response = await fetch(`${getApiBase(apiBase)}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new WorkbenchVersionsApiError({
      code: 'WB_NETWORK_ERROR',
      message: error?.message || DEFAULT_ERROR_MESSAGE,
      retryable: true,
      requestId,
    })
  }

  const payload = await readPayload(response, requestId)
  return unwrapPayload(payload, response, requestId)
}

function appendParam(params, name, value) {
  if (value === undefined || value === null || value === '') return
  params.set(name, String(value))
}

function versionList(data) {
  const items = Array.isArray(data) ? data : data?.items || data?.versions
  if (!Array.isArray(items)) {
    throw new WorkbenchVersionsApiError({
      code: 'WB_SCHEMA_MISMATCH',
      message: '版本列表格式无法识别。',
    })
  }
  return items
}

export async function listVersions({
  workbenchId,
  versionType,
  currentOnly = false,
  ticketId,
  limit = 200,
  offset = 0,
  apiBase,
  signal,
} = {}) {
  const params = new URLSearchParams()
  appendParam(params, 'workbench_id', workbenchId)
  appendParam(params, 'version_type', versionType)
  if (currentOnly) params.set('current_only', 'true')
  appendParam(params, 'ticket_id', ticketId)
  appendParam(params, 'limit', limit)
  appendParam(params, 'offset', offset)

  const data = await request(`${VERSIONS_PATH}?${params.toString()}`, { apiBase, signal })
  const items = versionList(data)
  return {
    items,
    total: data?.total ?? items.length,
    limit: data?.limit ?? limit,
    offset: data?.offset ?? offset,
  }
}

export function listFormalVersions(options = {}) {
  return listVersions({ ...options, versionType: 'formal' })
}

export function listTestVersions(options = {}) {
  return listVersions({ ...options, versionType: 'test' })
}

export async function getVersion(versionId, { apiBase, signal } = {}) {
  if (versionId === undefined || versionId === null || versionId === '') {
    throw new WorkbenchVersionsApiError({
      code: 'WB_INVALID_QUERY',
      message: '缺少版本 ID。',
    })
  }
  const data = await request(`${VERSIONS_PATH}/${encodeURIComponent(versionId)}`, { apiBase, signal })
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new WorkbenchVersionsApiError({
      code: 'WB_SCHEMA_MISMATCH',
      message: '版本详情格式无法识别。',
    })
  }
  return data
}

export function submitReleaseApproval(testVersionId, { apiBase, idempotencyKey, signal } = {}) {
  if (testVersionId === undefined || testVersionId === null || testVersionId === '') {
    throw new WorkbenchVersionsApiError({
      code: 'WB_INVALID_QUERY',
      message: '缺少测试版本 ID。',
    })
  }
  return request(`${TEST_VERSIONS_PATH}/${encodeURIComponent(testVersionId)}/submit-approval`, {
    method: 'POST',
    apiBase,
    idempotencyKey,
    signal,
  })
}

export const fetchVersions = listVersions
export const fetchFormalVersions = listFormalVersions
export const fetchTestVersions = listTestVersions
