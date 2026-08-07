import { readFile, readdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

describe('Study UI documentation coverage', () => {
  it('documents and demonstrates every public component export', async () => {
    const [entry, status, files, readme, designLanguage, homeExample] = await Promise.all([
      readFile(resolve('src/design-system/index.js'), 'utf8'),
      readFile(resolve('docs/study-ui/component-status.md'), 'utf8'),
      readdir(resolve('src/design-system'), { recursive: true }),
      readFile(resolve('src/design-system/README.md'), 'utf8'),
      readFile(resolve('src/design-system/foundations/DesignLanguage.stories.js'), 'utf8'),
      readFile(resolve('src/design-system/examples/HomeDashboardExample.stories.js'), 'utf8'),
    ])
    const exports = [...entry.matchAll(/export \{ default as (\w+) \}/g)].map((match) => match[1])
    const stories = new Set(files.filter((file) => file.endsWith('.stories.js')).map((file) => file.split(/[\\/]/).at(-1).replace('.stories.js', '')))
    const testSources = (await Promise.all(files.filter((file) => file.endsWith('.test.js')).map((file) => readFile(resolve('src/design-system', file), 'utf8')))).join('\n')
    expect(exports.length).toBeGreaterThan(0)
    for (const name of exports) {
      expect(status, `${name} must have a component-status row`).toContain(`| ${name} |`)
      expect(stories, `${name} must have its own Storybook entry`).toContain(name)
      expect(testSources, `${name} must be covered by a design-system test`).toContain(name)
    }
    for (const category of ['设计语言', '通用', '导航', '数据录入', '数据展示', '反馈', '布局', '仪表盘组件', '完整范例']) {
      expect(readme).toContain(category)
    }
    for (const story of ['Overview', 'ColorsAndStatus', 'TypographyAndDensity', 'SpacingAndRadius', 'ShadowAndMotion']) {
      expect(designLanguage).toContain(`export const ${story}`)
    }
    const dashboardWidgets = [
      'WorkHeatmapWidget', 'CalendarAgendaWidget', 'TodayFocusWidget', 'AutomationQueueWidget',
      'KnowledgeWidget', 'DailyMemoryWidget', 'QuickCommandWidget', 'CreationWidget', 'WorkflowWidget',
    ]
    for (const name of dashboardWidgets) {
      const source = await readFile(resolve('src/design-system/widgets', `${name}.stories.js`), 'utf8')
      expect(source).toMatch(/title:\s*'仪表盘组件\//)
    }
    expect(homeExample).toContain("title: '完整范例/首页仪表盘'")
  })
})
