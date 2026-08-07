import assert from 'node:assert/strict'
import { chromium } from 'playwright'
import { TEST_PORTS, testOrigin } from '../src/config/ports.js'

const origin = process.env.STUDY_UI_ORIGIN || testOrigin(TEST_PORTS.dashboard)
const expected = {
  '349:169': { x: 36, y: 244, width: 677, height: 321 },
  '349:516': { x: 727, y: 244, width: 331, height: 321 },
  '349:405': { x: 1072, y: 244, width: 331, height: 489 },
  '349:369': { x: 36, y: 579, width: 331, height: 321 },
  '349:471': { x: 382, y: 579, width: 331, height: 153 },
  '349:493': { x: 727, y: 579, width: 331, height: 321 },
  '349:459': { x: 382, y: 747, width: 331, height: 153 },
  '349:484': { x: 1072, y: 747, width: 158, height: 153 },
  '349:510': { x: 1244, y: 747, width: 158, height: 153 },
}
let browser
try { browser = await chromium.launch({ headless: true }) }
catch { browser = await chromium.launch({ channel: 'chrome', headless: true }) }
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } })
try {
  await page.goto(origin, { waitUntil: 'domcontentloaded' })
  await page.evaluate(() => localStorage.removeItem('study-hub:dashboard-layout:v1'))
  await page.reload({ waitUntil: 'domcontentloaded' })
  await page.locator('[data-home-motion="widget"]').first().waitFor()
  await page.waitForFunction(() => [...document.querySelectorAll('[data-home-motion="widget"]')].every((node) => {
    const style = getComputedStyle(node)
    return style.opacity === '1' && (style.transform === 'none' || style.transform === 'matrix(1, 0, 0, 1, 0, 0)')
  }), undefined, { timeout: 20_000 })
  for (const [nodeId, reference] of Object.entries(expected)) {
    const actual = await page.locator(`[data-figma-node="${nodeId}"]`).boundingBox()
    assert.ok(actual, `${nodeId} must render`)
    for (const key of Object.keys(reference)) {
      assert.ok(Math.abs(actual[key] - reference[key]) <= 4, `${nodeId}.${key}: ${actual[key]} !== ${reference[key]}`)
    }
  }
} finally { await browser.close() }

console.log('Study UI Figma widget overlay geometry passed')
