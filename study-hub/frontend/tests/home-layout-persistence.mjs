import assert from 'node:assert/strict'
import { chromium } from 'playwright'
import { TEST_PORTS, testOrigin } from '../src/config/ports.js'

const origin = process.env.STUDY_UI_ORIGIN || testOrigin(TEST_PORTS.dashboard)
let browser
try { browser = await chromium.launch({ headless: true }) }
catch { browser = await chromium.launch({ channel: 'chrome', headless: true }) }
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } })
page.on('dialog', (dialog) => dialog.accept())
try {
  await page.goto(origin, { waitUntil: 'domcontentloaded' })
  await page.locator('[data-home-motion="widget"]').first().waitFor()
  await page.evaluate(() => localStorage.removeItem('study-hub:dashboard-layout:v1'))
  await page.reload({ waitUntil: 'domcontentloaded' })
  await page.locator('[data-home-motion="widget"]').first().waitFor()

  await page.getByRole('button', { name: '编辑首页' }).click()
  await page.locator('[data-hide-id="knowledge"]').click()
  await page.locator('[data-editor-save]').click()
  await page.waitForTimeout(240)
  assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 0)
  await page.reload({ waitUntil: 'domcontentloaded' })
  await page.locator('[data-home-motion="widget"]').first().waitFor()
  assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 0, 'saved hidden module must survive reload')

  await page.getByRole('button', { name: '编辑首页' }).click()
  await page.locator('[data-editor-restore]').click()
  await page.waitForTimeout(240)
  assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 1)

  await page.getByRole('button', { name: '编辑首页' }).click()
  await page.locator('[data-hide-id="knowledge"]').click()
  await page.locator('[data-editor-cancel]').click()
  await page.waitForTimeout(240)
  assert.equal(await page.locator('[data-figma-node="349:471"]').count(), 1, 'cancel must restore pre-edit visibility')

  await page.getByRole('button', { name: '编辑首页' }).click()
  const grid = page.locator('.bento-dashboard-grid')
  const handle = page.locator('[data-module-id="quick-command"] .home-dashboard-grid__drag-handle')
  const [gridBox, handleBox] = await Promise.all([grid.boundingBox(), handle.boundingBox()])
  assert.ok(gridBox && handleBox, 'editable dashboard must expose a draggable grid handle')
  await handle.dispatchEvent('pointerdown', { button: 0, pointerId: 21, clientX: handleBox.x + handleBox.width / 2, clientY: handleBox.y + handleBox.height / 2 })
  await page.evaluate(({ x, y }) => {
    window.dispatchEvent(new PointerEvent('pointermove', { pointerId: 21, clientX: x, clientY: y }))
    window.dispatchEvent(new PointerEvent('pointerup', { pointerId: 21, clientX: x, clientY: y }))
  }, { x: gridBox.x + 4, y: gridBox.y + 4 })
  await page.locator('[data-editor-save]').click()
  await page.waitForTimeout(240)
  const persisted = await page.evaluate(() => JSON.parse(localStorage.getItem('study-hub:dashboard-layout:v1')))
  assert.deepEqual(persisted.widgets.find((widget) => widget.id === 'quick-command'), { id: 'quick-command', visible: true, x: 0, y: 0, order: 0 }, 'grid drag must persist v2 coordinates')
} finally { await browser.close() }

console.log('Study UI layout persistence checks passed')
