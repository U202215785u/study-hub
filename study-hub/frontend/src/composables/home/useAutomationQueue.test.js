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

  it('reports only a task entering done and reports it again after a retry cycle', async () => {
    const onCompleted = vi.fn()
    const apiGet = vi.fn()
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', title: '解析任务', status: 'done' }] })
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', title: '解析任务', status: 'done' }] })
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', title: '解析任务', status: 'running' }] })
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', title: '解析任务', status: 'done' }] })
    const queue = useAutomationQueue({ apiGet, apiPost: vi.fn(), apiDelete: vi.fn(), onCompleted })

    await queue.refresh()
    await queue.refresh()
    await queue.refresh()
    await queue.refresh()

    expect(onCompleted).toHaveBeenCalledTimes(2)
    expect(onCompleted).toHaveBeenLastCalledWith(expect.objectContaining({ task_id: 'q1', status: 'done' }))
  })

  it('does not report a task that enters error as a successful completion', async () => {
    const onCompleted = vi.fn()
    const queue = useAutomationQueue({
      apiGet: vi.fn().mockResolvedValue({ tasks: [{ task_id: 'q1', status: 'error' }] }),
      apiPost: vi.fn(),
      apiDelete: vi.fn(),
      onCompleted,
    })

    await queue.refresh()

    expect(onCompleted).not.toHaveBeenCalled()
  })
})
