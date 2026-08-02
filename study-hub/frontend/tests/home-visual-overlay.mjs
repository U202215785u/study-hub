import assert from 'node:assert/strict'
import { chromium } from 'playwright'

const origin = process.env.STUDY_UI_ORIGIN || 'http://127.0.0.1:5178'
const expected = {
  '349:169': { x: 36, y: 244, width: 677, height: 321 },
  '349:516': { x: 727, y: 244, width: 331, height: 321 },
  '349:405': { x: 1072, y: 244, width: 331, height: 484 },
  '349:369': { x: 36, y: 579, width: 331, height: 321 },
  '349:471': { x: 382, y: 579, width: 331, height: 153 },
  '349:493': { x: 727, y: 579, width: 331, height: 321 },
  '349:484': { x: 382, y: 747, width: 158, height: 153 },
  '349:510': { x: 554, y: 747, width: 158, height: 153 },
  '349:459': { x: 1072, y: 747, width: 331, height: 153 },
}
let browser
try { browser = await chromium.launch({ headless: true }) }
catch { browser = await chromium.launch({ channel: 'chrome', headless: true }) }
const page = await browser.newPage({ viewport: { width: 1440, height: 980 } })
try {
  await page.goto(origin, { waitUntil: 'networkidle' })
  await page.evaluate(() => localStorage.removeItem('study-hub:dashboard-layout:v1'))
  await page.reload({ waitUntil: 'networkidle' })
  for (const [nodeId, reference] of Object.entries(expected)) {
    const actual = await page.locator(`[data-figma-node="${nodeId}"]`).boundingBox()
    assert.ok(actual, `${nodeId} must render`)
    for (const key of Object.keys(reference)) {
      assert.ok(Math.abs(actual[key] - reference[key]) <= 4, `${nodeId}.${key}: ${actual[key]} !== ${reference[key]}`)
    }
  }
} finally { await browser.close() }

console.log('Study UI Figma widget overlay geometry passed')
