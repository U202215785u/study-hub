import { describe, expect, it, vi } from 'vitest'
import { isSafeNavigation, useHomeSearch } from './useHomeSearch'

describe('useHomeSearch', () => {
  it('uses the unified internal endpoint and never searches blank input', async () => {
    const apiGet = vi.fn().mockResolvedValue({ groups: [], assistant: { enabled: false } })
    const search = useHomeSearch({ apiGet })
    await search.searchNow()
    expect(apiGet).not.toHaveBeenCalled()

    search.query.value = '设计系统'
    await search.searchNow()
    expect(apiGet).toHaveBeenCalledWith('/workstation/search?q=%E8%AE%BE%E8%AE%A1%E7%B3%BB%E7%BB%9F')
    expect(search.expanded.value).toBe(true)
  })

  it('keeps only the latest response when searches finish out of order', async () => {
    let resolveFirst
    const first = new Promise((resolve) => { resolveFirst = resolve })
    const apiGet = vi.fn().mockReturnValueOnce(first).mockResolvedValueOnce({ groups: [{ id: 'knowledge' }] })
    const search = useHomeSearch({ apiGet })
    search.query.value = 'first'
    const pending = search.searchNow()
    search.query.value = 'second'
    await search.searchNow()
    resolveFirst({ groups: [{ id: 'old' }] })
    await pending
    expect(search.groups.value).toEqual([{ id: 'knowledge' }])
  })

  it('rejects external or unknown navigation targets', () => {
    expect(isSafeNavigation({ kind: 'route', path: '/wiki', query: {} })).toBe(true)
    expect(isSafeNavigation({ kind: 'route', path: 'https://example.com', query: {} })).toBe(false)
    expect(isSafeNavigation({ kind: 'route', path: '/not-real', query: {} })).toBe(false)
  })
})
