import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), 'utf8')

const navigation = await read('src/design-system/patterns/CapsuleNavigation.vue')
const calendar = await read('src/design-system/widgets/CalendarAgendaWidget.vue')
const commands = await read('src/design-system/widgets/QuickCommandWidget.vue')
const automation = await read('src/design-system/widgets/AutomationQueueWidget.vue')
const headerWidgets = [
  'WorkHeatmapWidget.vue',
  'CalendarAgendaWidget.vue',
  'TodayFocusWidget.vue',
  'AutomationQueueWidget.vue',
  'KnowledgeWidget.vue',
  'QuickCommandWidget.vue',
  'CreationWidget.vue',
  'WorkflowWidget.vue',
]

assert.match(navigation, /font:\s*700\s+12px\/1\s+var\(--ui-font-sans\)/, 'homepage navigation actions must share the button typography token')
assert.match(calendar, /import\s+UiButton\s+from/, 'calendar action must use the shared button component')
assert.match(calendar, /<UiButton[^>]*class="calendar-agenda__today"[^>]*size="xs"[^>]*shape="pill"/, 'calendar today action must use the compact pill contract')
assert.match(commands, /import\s+UiButton\s+from/, 'quick commands must use the shared button component')
assert.doesNotMatch(commands, /<button\s+type="button"[^>]*data-command-id/, 'quick commands must not define a second button typography contract')
assert.doesNotMatch(automation, /\.queue-widget\s+\.queue-widget__(?:more|start)\s*\{[^}]*padding\s*:/s, 'automation controls must use public button spacing props')

for (const file of headerWidgets) {
  const source = await read(`src/design-system/widgets/${file}`)
  assert.match(source, /<UiCompactHeader[^>]*size="md"/, `${file} homepage card title must use md`) 
}

const memory = await read('src/design-system/widgets/DailyMemoryWidget.vue')
assert.match(memory, /\.memory-widget__title[^}]*font-size:18px/, 'daily memory homepage card title must use md')
assert.doesNotMatch(automation, /\.queue-widget__title\{[^}]*font-size:/, 'automation card title must not override the shared md size')

console.log('Homepage button typography and component contracts passed')
