import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const widgetFiles = [
  'WorkHeatmapWidget.vue',
  'CalendarAgendaWidget.vue',
  'TodayFocusWidget.vue',
  'AutomationQueueWidget.vue',
  'KnowledgeWidget.vue',
  'DailyMemoryWidget.vue',
  'QuickCommandWidget.vue',
  'CreationWidget.vue',
  'WorkflowWidget.vue',
]

const widgetRoots = [
  'heatmap-widget',
  'calendar-agenda',
  'today-focus',
  'queue-widget',
  'knowledge-widget',
  'memory-widget',
  'command-widget',
  'creation-widget',
  'workflow-widget',
]

const widgetSources = new Map()

for (const [index, file] of widgetFiles.entries()) {
  const source = await readFile(new URL(`../src/design-system/widgets/${file}`, import.meta.url), 'utf8')
  widgetSources.set(file, source)
  assert.doesNotMatch(source, /@container\b/, `${file} must not switch to a compact card layout`)
  const rootRule = new RegExp(`\\.${widgetRoots[index]}\\s*\\{[^}]*padding\\s*:`, 's')
  assert.doesNotMatch(source, rootRule, `${file} must inherit its outer inset from DashboardModuleCard`)
}

const sharedComponentUsage = {
  'WorkHeatmapWidget.vue': ['UiCompactHeader'],
  'CalendarAgendaWidget.vue': ['UiCompactHeader'],
  'TodayFocusWidget.vue': ['UiCompactHeader'],
  'AutomationQueueWidget.vue': ['UiInsetSurface', 'UiProgress'],
  'KnowledgeWidget.vue': ['UiCompactHeader', 'UiInsetSurface'],
  'QuickCommandWidget.vue': ['UiCompactHeader', 'UiInsetSurface'],
  'CreationWidget.vue': ['UiCompactHeader', 'UiInsetSurface', 'UiPillButton'],
  'WorkflowWidget.vue': ['UiCompactHeader', 'UiInsetSurface', 'UiPillButton'],
}

for (const [file, components] of Object.entries(sharedComponentUsage)) {
  for (const component of components) {
    assert.match(widgetSources.get(file), new RegExp(`import\\s+${component}\\s+from`), `${file} must use ${component}`)
  }
}

const widgetSource = [...widgetSources.values()].join('\n')
assert.doesNotMatch(widgetSource, /:deep\(\.ui-button\)[^{]*\{[^}]*(?:min-height|padding|font-size)/s, 'widgets must use public button sizes instead of deep overrides')
assert.doesNotMatch(widgetSource, /!important/, 'widgets must not force public component geometry with !important')

const automationSource = widgetSources.get('AutomationQueueWidget.vue')
assert.doesNotMatch(automationSource, /<i><em\b/, 'automation queue must use UiProgress instead of a hand-built progress track')
assert.doesNotMatch(automationSource, /\.queue-widget__(?:row>\.ui-button|more|start)\{[^}]*(?:min-height|font-size|border-radius)/s, 'automation controls must use UiButton size and shape props')

const cardSource = await readFile(new URL('../src/design-system/patterns/DashboardModuleCard.vue', import.meta.url), 'utf8')
assert.match(cardSource, /dashboard-module-card__content[^}]*\{[^}]*padding:\s*16px/s, 'the shared card shell must own the 16px inset')
assert.match(cardSource, /dashboard-module-card__state[^}]*\{[^}]*padding:\s*16px/s, 'loading, error, and empty states must share the 16px inset')
assert.match(cardSource, /data-card-inset="16"/, 'the shared inset must be exposed for visual verification')

const cardStorySource = await readFile(new URL('../src/design-system/patterns/DashboardModuleCard.stories.js', import.meta.url), 'utf8')
assert.doesNotMatch(cardStorySource, /padding:\s*20px/, 'the card story must not add a second content inset')

const frameSource = await readFile(new URL('../src/design-system/patterns/WorkbenchFrame.vue', import.meta.url), 'utf8')
assert.match(frameSource, /data-dashboard-stage/, 'the proportional dashboard stage must be public')
assert.match(frameSource, /width:\s*1440px/, 'the dashboard stage must keep the Figma reference width')
assert.match(frameSource, /height:\s*980px/, 'the dashboard stage must keep the Figma reference height')

console.log('Study UI proportional stage and unified card inset contract passed')
