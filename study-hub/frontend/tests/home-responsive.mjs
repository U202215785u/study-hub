import assert from 'node:assert/strict'
import { mkdir, stat } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'

const origin = process.env.STUDY_UI_ORIGIN || 'http://127.0.0.1:5178'
const output = resolve('test-results/study-ui')
const viewports = [
  { width: 1440, height: 980 },
  { width: 1366, height: 768 },
  { width: 1920, height: 1080 },
  { width: 2560, height: 1440 },
]
const nodeIds = ['349:169', '349:516', '349:405', '349:369', '349:471', '349:493', '349:484', '349:510', '349:459']
await mkdir(output, { recursive: true })

async function launchBrowser() {
  try { return await chromium.launch({ headless: true }) }
  catch (error) {
    try { return await chromium.launch({ channel: 'chrome', headless: true }) }
    catch { throw error }
  }
}

const browser = await launchBrowser()
try {
  for (const viewport of viewports) {
    const page = await browser.newPage({ viewport })
    await page.goto(origin, { waitUntil: 'networkidle' })
    const report = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      unnamedButtons: [...document.querySelectorAll('button')].filter((button) => !button.getAttribute('aria-label') && !button.textContent.trim()).length,
      nodeIds: [...document.querySelectorAll('[data-figma-node]')].map((node) => node.dataset.figmaNode),
    }))
    assert.ok(report.scrollWidth <= report.clientWidth, `horizontal overflow at ${viewport.width}px: ${report.scrollWidth} > ${report.clientWidth}`)
    assert.equal(report.unnamedButtons, 0, `unnamed button at ${viewport.width}px`)
    assert.deepEqual(report.nodeIds, nodeIds, `widget order changed at ${viewport.width}px`)
    assert.equal(await page.getByRole('navigation', { name: '主导航' }).count(), 1)
    assert.equal(await page.getByRole('main').count(), 1)
    assert.equal(await page.getByRole('heading', { name: /好, 章$/, level: 1 }).count(), 1)

    if (viewport.width === 1440) {
      const expected = {
        nav: { x: 60, y: 33, width: 1320, height: 72 },
        greeting: { x: 42, y: 155, width: 1356, height: 69 },
        grid: { x: 36, y: 244, width: 1368 },
      }
      for (const [name, anchor] of Object.entries(expected)) {
        const actual = await page.locator(`[data-visual-anchor="${name}"]`).boundingBox()
        assert.ok(actual, `${name} anchor must exist`)
        for (const key of Object.keys(anchor)) assert.ok(Math.abs(actual[key] - anchor[key]) <= 4, `${name}.${key}: ${actual[key]} !== ${anchor[key]}`)
      }
    }

    const target = resolve(output, `home-${viewport.width}.png`)
    await page.screenshot({ path: target, fullPage: true })
    assert.ok((await stat(target)).size > 10_000, `blank or incomplete screenshot at ${viewport.width}px`)
    await page.close()
  }
} finally { await browser.close() }

console.log('Study UI PC geometry and responsive checks passed')
