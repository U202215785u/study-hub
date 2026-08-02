import { describe, expect, it, vi } from 'vitest'
import { useDailyReview } from './useDailyReview'

describe('useDailyReview', () => {
  it('polishes and creates weekly reports without replacing raw input', async () => {
    const apiPost = vi.fn().mockResolvedValue({ polished: '润色结果' })
    const apiGet = vi.fn().mockResolvedValueOnce([]).mockResolvedValueOnce({ report: '周报' })
    const review = useDailyReview({ apiPost, apiGet, now: () => new Date('2026-06-07T08:00:00Z') })
    review.input.value = '今天学了组件设计'

    await review.polish()
    expect(apiPost).toHaveBeenCalledWith('/review/polish', { raw_text: '今天学了组件设计', date: '2026-06-07' })
    expect(review.input.value).toBe('今天学了组件设计')
    expect(review.status.value).toBe('完成')

    await review.weeklyReport()
    expect(review.result.value).toBe('周报')
    expect(review.input.value).toBe('今天学了组件设计')
  })
})
