import { describe, expect, it, vi } from 'vitest'
import { useAutomationQueue } from './useAutomationQueue'

describe('useAutomationQueue completion state machine', () => {
  it('reports only a new done transition after an error and retry cycle', async () => {
    const apiGet = vi.fn()
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', status: 'error', module_name: 'Module' }] })
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', status: 'error', module_name: 'Module' }] })
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', status: 'pending', module_name: 'Module' }] })
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', status: 'done', module_name: 'Module' }] })
      .mockResolvedValueOnce({ tasks: [{ task_id: 'q1', status: 'done', module_name: 'Module' }] })
    const onCompleted = vi.fn()
    const queue = useAutomationQueue({ apiGet, apiPost: vi.fn().mockResolvedValue({ status: 'queued' }), apiDelete: vi.fn(), onCompleted })

    await queue.refresh()
    await queue.refresh()
    await queue.retry('q1')
    await queue.refresh()
    await queue.refresh()

    expect(onCompleted).toHaveBeenCalledTimes(1)
    expect(onCompleted).toHaveBeenCalledWith(expect.objectContaining({ task_id: 'q1', status: 'done' }))
  })
})
