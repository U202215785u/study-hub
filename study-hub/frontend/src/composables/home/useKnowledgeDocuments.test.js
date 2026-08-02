import { ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { useKnowledgeDocuments } from './useKnowledgeDocuments'

describe('useKnowledgeDocuments', () => {
  it('preserves the current category while sorting and reloading', async () => {
    const apiGet = vi.fn().mockResolvedValue([])
    const category = ref('12')
    const knowledge = useKnowledgeDocuments({ apiGet, apiPost: vi.fn(), apiDelete: vi.fn(), apiUpload: vi.fn(), category })

    await knowledge.setSort('title:asc')
    await knowledge.reload()

    expect(category.value).toBe('12')
    expect(apiGet).toHaveBeenLastCalledWith('/documents?sort_by=title&sort_order=asc')
  })
})
