import { describe, expect, it, vi } from 'vitest'
import { useKnowledgeDocuments } from './useKnowledgeDocuments'

describe('useKnowledgeDocuments error contract', () => {
  it('does not replace documents with a business-error object', async () => {
    const notify = vi.fn()
    const knowledge = useKnowledgeDocuments({
      apiGet: vi.fn().mockResolvedValue({ error: 'documents unavailable' }),
      apiPost: vi.fn(),
      apiDelete: vi.fn(),
      apiUpload: vi.fn(),
      notify,
    })

    await knowledge.reload()

    expect(knowledge.documents.value).toEqual([])
    expect(notify).toHaveBeenCalledWith('documents unavailable', true)
  })

  it('does not report deletion success when the API returns an error payload', async () => {
    const notify = vi.fn()
    const knowledge = useKnowledgeDocuments({
      apiGet: vi.fn().mockResolvedValue([]),
      apiPost: vi.fn(),
      apiDelete: vi.fn().mockResolvedValue({ detail: 'document not found' }),
      apiUpload: vi.fn(),
      notify,
      confirmAction: () => true,
    })

    await knowledge.remove('missing')

    expect(notify).toHaveBeenCalledWith(expect.any(String), true)
    expect(notify.mock.calls.some(([message]) => message === '文档已删除')).toBe(false)
  })
})
