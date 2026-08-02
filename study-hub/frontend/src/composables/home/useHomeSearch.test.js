import { describe, expect, it, vi } from 'vitest'
import { useHomeSearch } from './useHomeSearch'

describe('useHomeSearch', () => {
  it('submits the current mode, query and category', async () => {
    const apiPost = vi.fn().mockResolvedValue({ answer: '结果', sources: ['笔记'] })
    const search = useHomeSearch({ apiPost })
    search.mode.value = 'kb'
    search.query.value = '原子设计'
    search.category.value = '7'

    await search.submit()

    expect(apiPost).toHaveBeenCalledWith('/rag/query', { question: '原子设计', category_id: 7 })
    expect(search.loading.value).toBe(false)
    expect(search.hasResult.value).toBe(true)
    expect(search.answer.value).toBe('结果')
  })

  it('exposes rejected requests as an error result', async () => {
    const search = useHomeSearch({ apiPost: vi.fn().mockRejectedValue(new Error('offline')) })
    search.query.value = '测试'
    await search.submit()
    expect(search.error.value).toBe('无法连接后端服务')
    expect(search.loading.value).toBe(false)
  })
})
