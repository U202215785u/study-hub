import { describe, expect, it } from 'vitest'
import { createHomeDashboardData, toLocalDateKey } from './useHomeDashboardData.js'

describe('home dashboard data mapping', () => {
  it('keeps the local calendar date around positive-offset midnight', () => {
    expect(toLocalDateKey(new Date('2026-08-03T00:30:00+08:00'))).toBe('2026-08-03')
  })

  it('maps real API records into stable widget contracts and caps card content', () => {
    const dashboard = createHomeDashboardData()
    expect(dashboard.mapDocuments([{ id: 3, title: '真实文档', created_at: '2026-08-03T10:00:00' }])[0]).toMatchObject({ id: 3, title: '真实文档' })
    expect(dashboard.mapQueue([{ task_id: 'q1', title: '解析', status: 'running', progress: 55 }])[0]).toMatchObject({ id: 'q1', progress: 55 })
    expect(dashboard.mapCommands([{ id: 'kb', name: '打开知识库', route: '/kb' }])[0]).toMatchObject({ id: 'kb', title: '打开知识库' })
    expect(dashboard.mapDocuments(Array.from({ length: 5 }, (_, id) => ({ id, title: String(id) })))).toHaveLength(2)
  })

  it('maps DDL records into the selected day without inventing schedule times', () => {
    const dashboard = createHomeDashboardData()
    const records = [
      { id: 1, title: '设计复盘', plan_date: '2026-08-03', start_time: '10:00', end_time: '11:00', status: 'in_progress' },
      { id: 2, title: '无时间任务', due_date: '2026-08-03', status: 'todo' },
      { id: 3, title: '其他日期', plan_date: '2026-08-04', start_time: '12:00', status: 'done' },
    ]

    expect(dashboard.mapAgenda(records, '2026-08-03')).toEqual([
      { id: 1, title: '设计复盘', time: '10:00 - 11:00', tone: 'lime' },
      { id: 2, title: '无时间任务', time: '未安排时间', tone: 'lime' },
    ])
    expect(dashboard.mapTodayTasks(records, '2026-08-03')).toEqual([
      { id: 1, title: '设计复盘', time: '10:00 - 11:00', status: 'running', progress: 0 },
      { id: 2, title: '无时间任务', time: '未安排时间', status: 'pending', progress: 0 },
    ])
  })

  it('builds a truthful 196-day activity heatmap from persisted record dates', () => {
    const dashboard = createHomeDashboardData()
    const cells = dashboard.mapActivityHeatmap({
      tasks: [{ id: 1, updated_at: '2026-08-03T09:00:00' }],
      documents: [{ id: 2, created_at: '2026-08-03T10:00:00' }],
      queue: [{ task_id: 'q1', created_at: '2026-08-02T10:00:00' }],
    }, new Date('2026-08-03T12:00:00'))

    expect(cells).toHaveLength(196)
    expect(cells.at(-1)).toMatchObject({ id: '2026-08-03', count: 2, level: 2 })
    expect(cells.at(-2)).toMatchObject({ id: '2026-08-02', count: 1, level: 1 })
    expect(cells.filter((cell) => cell.count > 0)).toHaveLength(2)
  })
})
