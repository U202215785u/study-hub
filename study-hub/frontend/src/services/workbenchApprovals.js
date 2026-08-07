import { unref } from 'vue'
import { useSettingsStore } from '../stores/settings'

const APPROVALS_PATH = '/api/workbench/approvals'

export class WorkbenchApiError extends Error {
  constructor(message, { status = 0, code = 'WB_REQUEST_FAILED', details = null, requestId = '' } = {}) {
    super(message)
    this.name = 'WorkbenchApiError'
    this.status = status
    this.code = code
    this.details = details
    this.requestId = requestId
  }
}

function getApiBase(apiBase) {
  if (apiBase !== undefined) return String(unref(apiBase) || '')
  return String(useSettingsStore().apiBase || '')
}

function createRequestId() {
  if (typeof globalThis.crypto?.randomUUID === 'function') return globalThis.crypto.randomUUID()
  return `wb-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function createIdempotencyKey(approvalId) {
  return `approval-resolve-${approvalId}-${createRequestId()}`
}

async function readPayload(response) {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return { message: text }
  }
}

function getErrorParts(payload) {
  const error = payload?.error || payload?.detail || payload
  if (typeof error === 'string') return { message: error, code: '', details: null }
  return {
    message: error?.message || '工作台请求失败，请稍后重试。',
    code: error?.code || '',
    details: error?.details || null,
  }
}

function unwrapPayload(payload, response) {
  if (payload?.ok === false) {
    const parts = getErrorParts(payload)
    throw new WorkbenchApiError(parts.message, {
      status: response.status,
      code: parts.code || 'WB_REQUEST_FAILED',
      details: parts.details,
      requestId: payload?.meta?.request_id || '',
    })
  }
  return payload?.ok === true ? payload.data : payload
}

async function request(path, { method = 'GET', body, apiBase, idempotencyKey } = {}) {
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
    })
  } catch (error) {
    throw new WorkbenchApiError(error?.message || '无法连接工作台服务，请稍后重试。', {
      code: 'WB_NETWORK_ERROR',
      requestId,
    })
  }

  const payload = await readPayload(response)
  if (!response.ok) {
    const parts = getErrorParts(payload)
    throw new WorkbenchApiError(parts.message, {
      status: response.status,
      code: parts.code || (response.status === 409 ? 'WB_APPROVAL_ALREADY_DECIDED' : 'WB_REQUEST_FAILED'),
      details: parts.details,
      requestId: payload?.meta?.request_id || requestId,
    })
  }
  return unwrapPayload(payload, response)
}

export async function listApprovals({ status = 'pending', apiBase } = {}) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  const data = await request(`${APPROVALS_PATH}?${params.toString()}`, { apiBase })
  const items = Array.isArray(data) ? data : data?.items || []
  return { items, total: data?.total ?? items.length }
}

export async function getPendingApprovals(options = {}) {
  return listApprovals({ ...options, status: 'pending' })
}

export function resolveApproval(approvalId, { approved, response = '', apiBase, idempotencyKey } = {}) {
  if (!approvalId) throw new TypeError('approvalId is required')
  if (typeof approved !== 'boolean') throw new TypeError('approved must be a boolean')
  return request(`${APPROVALS_PATH}/${encodeURIComponent(approvalId)}/resolve`, {
    method: 'POST',
    apiBase,
    idempotencyKey,
    body: { approved, response: String(response) },
  })
}
