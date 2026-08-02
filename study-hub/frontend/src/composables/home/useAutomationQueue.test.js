import { afterEach, describe, expect, it, vi } from 'vitest'
import { useAutomationQueue } from './useAutomationQueue'

describe('useAutomationQueue', () => {
  afterEach(() => vi.useRealTimers())

  it('starts polling once, maps server tasks and stops explicitly', async () => {
    vi.useFakeTimers()
    const apiGet = vi.fn().mockResolvedValue({ stats: { running: 1 }, tasks: [{ task_id: 'q1', title: '解析', status: 'running' }] })
    const queue = useAutomationQueue({ apiGet, apiPost: vi.fn(), apiDelete: vi.fn(), interval: 1000 })

    queue.start()
    queue.start()
    await vi.runOnlyPendingTimersAsync()

    expect(apiGet).toHaveBeenCalledTimes(2)
    expect(queue.items.value[0]).toMatchObject({ id: 'q1', task_id: 'q1' })
    queue.stop()
    await vi.advanceTimersByTimeAsync(3000)
    expect(apiGet).toHaveBeenCalledTimes(2)
  })
})
