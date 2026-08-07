import { describe, expect, it, vi } from 'vitest'
import { useDailyReview } from './useDailyReview'

describe('useDailyReview error contract', () => {
  it('keeps the review open and reports an error when the polish payload is incomplete', async () => {
    const notify = vi.fn()
    const review = useDailyReview({
      apiPost: vi.fn().mockResolvedValue({ error: 'upstream failed' }),
      apiGet: vi.fn(),
      notify,
    })
    review.input.value = 'today notes'

    await review.polish()

    expect(review.status.value).toBe('')
    expect(review.result.value).toBe('')
    expect(review.input.value).toBe('today notes')
    expect(notify).toHaveBeenCalledWith(expect.any(String), true)
  })

  it('rejects a weekly report without a report field', async () => {
    const notify = vi.fn()
    const review = useDailyReview({
      apiPost: vi.fn(),
      apiGet: vi.fn().mockResolvedValue({ detail: 'missing report' }),
      notify,
    })

    await review.weeklyReport()

    expect(review.status.value).toBe('')
    expect(review.result.value).toBe('')
    expect(notify).toHaveBeenCalledWith(expect.any(String), true)
  })

  it('sends the local UTC+8 date around midnight instead of the UTC date', async () => {
    const apiPost = vi.fn().mockResolvedValue({ polished: 'result' })
    const review = useDailyReview({
      apiPost,
      apiGet: vi.fn().mockResolvedValue([]),
      now: () => new Date('2026-08-02T16:30:00.000Z'),
    })
    review.input.value = 'today notes'

    await review.polish()

    expect(apiPost).toHaveBeenCalledWith('/review/polish', { raw_text: 'today notes', date: '2026-08-03' })
  })
})
