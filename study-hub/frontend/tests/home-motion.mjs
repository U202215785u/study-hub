import assert from 'node:assert/strict'
import { mkdir, stat } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { DEFAULT_DASHBOARD_LAYOUT } from '../src/design-system/layout/dashboardLayout.js'
import { TEST_PORTS, testOrigin } from '../src/config/ports.js'

const origin = process.env.STUDY_UI_ORIGIN || testOrigin(TEST_PORTS.dashboard)
const output = resolve('test-results/study-ui-motion')
const viewports = [{ width: 390, height: 844 }, { width: 942, height: 638 }, { width: 1440, height: 980 }]
const expectedWidgetCount = DEFAULT_DASHBOARD_LAYOUT.widgets.filter((widget) => widget.visible !== false).length
const storageKey = 'study-hub:dashboard-layout:v1'
await mkdir(output, { recursive: true })

async function launchBrowser() {
  try { return await chromium.launch({ headless: true }) }
  catch (error) {
    try { return await chromium.launch({ channel: 'chrome', headless: true }) }
    catch { throw error }
  }
}

async function openContext(browser, viewport, reducedMotion) {
  const context = await browser.newContext({ viewport, reducedMotion: reducedMotion ? 'reduce' : 'no-preference' })
  await context.addInitScript((key) => localStorage.removeItem(key), storageKey)
  const page = await context.newPage()
  await page.goto(origin, { waitUntil: 'domcontentloaded' })
  await page.locator('[data-home-motion="widget"]').first().waitFor()
  return { context, page }
}

function assertFinalMotionState(report, label) {
  assert.equal(report.length, expectedWidgetCount, `${label}: expected ${expectedWidgetCount} widgets`)
  for (const item of report) {
    assert.equal(item.opacity, '1', `${label}: ${item.id} remains transparent`)
    assert.ok(item.transform === 'none' || item.transform === 'matrix(1, 0, 0, 1, 0, 0)', `${label}: ${item.id} retains transform ${item.transform}`)
  }
}

const browser = await launchBrowser()
try {
  for (const viewport of viewports) {
    const { context, page } = await openContext(browser, viewport, false)
    try {
      await page.waitForTimeout(900)
      const report = await page.locator('[data-home-motion="widget"]').evaluateAll((nodes) => nodes.map((node) => ({ id: node.dataset.flipId, opacity: getComputedStyle(node).opacity, transform: getComputedStyle(node).transform })))
      assertFinalMotionState(report, `normal ${viewport.width}`)

      const reviewTrigger = page.locator('.memory-widget__review')
      await reviewTrigger.focus()
      await reviewTrigger.click()
      await page.keyboard.press('Escape')
      await page.waitForTimeout(240)
      assert.equal(await page.evaluate(() => document.activeElement?.classList.contains('memory-widget__review')), true, `focus did not return at ${viewport.width}px`)

      await page.getByRole('button', { name: '编辑首页' }).click()
      await page.locator('[data-hide-id="knowledge"]').click()
      await page.waitForTimeout(240)
      assert.equal(await page.locator('[data-flip-id="knowledge"]').count(), 0, `hide failed at ${viewport.width}px`)
      await page.locator('[data-show-id="knowledge"]').click()
      await page.waitForTimeout(240)
      assert.equal(await page.locator('[data-flip-id="knowledge"]').count(), 1, `show failed at ${viewport.width}px`)
      await page.locator('[data-editor-cancel]').click()
      await page.waitForTimeout(240)
      assert.equal(await page.locator('[data-flip-id="knowledge"]').count(), 1, `cancel failed at ${viewport.width}px`)

      const screenshot = resolve(output, `home-${viewport.width}.png`)
      await page.screenshot({ path: screenshot, fullPage: true })
      assert.ok((await stat(screenshot)).size > 10_000, `blank or incomplete screenshot at ${viewport.width}px`)
    } finally { await context.close() }
  }

  const { context, page } = await openContext(browser, { width: 1440, height: 980 }, true)
  try {
    const immediate = await page.locator('[data-home-motion="widget"]').evaluateAll((nodes) => nodes.map((node) => ({ opacity: getComputedStyle(node).opacity, transform: getComputedStyle(node).transform })))
    assertFinalMotionState(immediate.map((item, index) => ({ ...item, id: index })), 'reduced motion immediate')
    const before = await page.locator('.home-dashboard-grid').boundingBox()
    await page.waitForTimeout(400)
    const after = await page.locator('.home-dashboard-grid').boundingBox()
    assert.deepEqual(after, before, 'reduced motion layout moved after first frame')
  } finally { await context.close() }
} finally { await browser.close() }

console.log('Home motion, reduced-motion, focus, editor, and responsive checks passed')
