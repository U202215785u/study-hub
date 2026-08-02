import assert from 'node:assert/strict'
import { chromium } from 'playwright'

const origin = process.env.STUDY_UI_ORIGIN || 'http://127.0.0.1:5178'
let browser
try { browser = await chromium.launch({ headless: true }) }
catch { browser = await chromium.launch({ channel: 'chrome', headless: true }) }
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } })
try {
  await page.goto(origin, { waitUntil: 'networkidle' })
  await page.evaluate(() => localStorage.removeItem('study-hub:dashboard-layout:v1'))
  await page.reload({ waitUntil: 'networkidle' })

  await page.getByRole('button', { name: '编辑首页' }).click()
  await page.locator('[data-hide-id="knowledge"]').click()
  await page.locator('[data-editor-save]').click()
  assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 0)
  await page.reload({ waitUntil: 'networkidle' })
  assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 0, 'saved hidden module must survive reload')

  await page.getByRole('button', { name: '编辑首页' }).click()
  await page.locator('[data-editor-restore]').click()
  assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 1)

  await page.getByRole('button', { name: '编辑首页' }).click()
  await page.locator('[data-hide-id="knowledge"]').click()
  await page.locator('[data-editor-cancel]').click()
  assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 1, 'cancel must restore pre-edit visibility')

  await page.getByRole('button', { name: '编辑首页' }).click()
  const source = page.locator('[data-editor-module-id="quick-command"] .dashboard-editor__handle')
  const target = page.locator('[data-editor-module-id="daily-memory"]')
  await source.dragTo(target)
  await page.locator('[data-editor-save]').click()
  const order = await page.locator('[data-module-id]').evaluateAll((nodes) => nodes.map((node) => node.dataset.moduleId))
  assert.ok(order.indexOf('quick-command') < order.indexOf('daily-memory'), 'drag order must be applied')
} finally { await browser.close() }

console.log('Study UI layout persistence checks passed')
