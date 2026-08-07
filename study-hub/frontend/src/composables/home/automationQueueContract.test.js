import { describe, expect, it } from 'vitest'
import { normalizeAutomationTask } from './automationQueueContract'

describe('automation queue DTO contract', () => {
  it('maps a real backend task into a titled, numeric, accessible task', () => {
    expect(normalizeAutomationTask({
      task_id: 'q1',
      module_id: 'douyin-summary',
      module_name: 'Douyin summary',
      status: 'summarizing',
      progress: '正在 AI 深度分析',
    })).toMatchObject({
      id: 'q1',
      title: 'Douyin summary',
      moduleName: 'Douyin summary',
      status: 'summarizing',
      progress: 60,
      progressText: '正在 AI 深度分析',
    })
  })

  it('uses completion progress and preserves every server status', () => {
    for (const status of ['pending', 'extracting', 'summarizing', 'importing', 'done', 'error']) {
      const task = normalizeAutomationTask({ task_id: status, module_name: 'Module', status, progress: status === 'done' ? '完成' : '' })
      expect(task.status).toBe(status)
      expect(Number.isFinite(task.progress)).toBe(true)
    }
    expect(normalizeAutomationTask({ task_id: 'done', module_name: 'Module', status: 'done', progress: '完成' }).progress).toBe(100)
  })

  it('accepts the backend snake_case progress text field', () => {
    expect(normalizeAutomationTask({
      task_id: 'q2',
      module_name: 'Module',
      status: 'summarizing',
      progress: 60,
      progress_text: '正在 AI 深度分析',
    }).progressText).toBe('正在 AI 深度分析')
  })
})
