import { describe, expect, it } from 'vitest'
import { createHomeDashboardData } from './useHomeDashboardData.js'

describe('home dashboard data mapping', () => {
  it('maps real API records into stable widget contracts and caps card content', () => {
    const dashboard = createHomeDashboardData()
    expect(dashboard.mapDocuments([{ id: 3, title: '真实文档', created_at: '2026-08-03T10:00:00' }])[0]).toMatchObject({ id: 3, title: '真实文档' })
    expect(dashboard.mapQueue([{ task_id: 'q1', title: '解析', status: 'running', progress: 55 }])[0]).toMatchObject({ id: 'q1', progress: 55 })
    expect(dashboard.mapCommands([{ id: 'kb', name: '打开知识库', route: '/kb' }])[0]).toMatchObject({ id: 'kb', title: '打开知识库' })
    expect(dashboard.mapDocuments(Array.from({ length: 5 }, (_, id) => ({ id, title: String(id) })))).toHaveLength(2)
  })
})
