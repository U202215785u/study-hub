import assert from 'node:assert/strict'
import { mkdir, stat } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'

const origin = process.env.STUDY_UI_ORIGIN || 'http://127.0.0.1:5178'
const output = resolve('test-results/study-ui')
const viewports = [
  { width: 1440, height: 980 },
  { width: 1024, height: 980 },
  { width: 768, height: 1024 },
  { width: 390, height: 844 },
]
await mkdir(output, { recursive: true })

async function launchBrowser() {
  try {
    return await chromium.launch({ headless: true })
  } catch (error) {
    try {
      return await chromium.launch({ channel: 'chrome', headless: true })
    } catch {
      throw error
    }
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
      figmaWidgets: document.querySelectorAll('[data-figma-node]').length,
    }))
    assert.ok(report.scrollWidth <= report.clientWidth, `horizontal overflow at ${viewport.width}px: ${report.scrollWidth} > ${report.clientWidth}`)
    assert.equal(report.unnamedButtons, 0, `unnamed button at ${viewport.width}px`)
    assert.equal(report.figmaWidgets, 6, `expected six mapped widgets at ${viewport.width}px`)
    assert.equal(await page.getByRole('navigation', { name: '主导航' }).count(), 1)
    assert.equal(await page.getByRole('main').count(), 1)
    assert.equal(await page.getByRole('heading', { name: '学习中枢', level: 1 }).count(), 1)

    if (viewport.width === 1024) {
      const taskBox = await page.locator('[data-figma-node="349:405"]').boundingBox()
      const calendarBox = await page.locator('[data-figma-node="349:516"]').boundingBox()
      assert.ok(taskBox && calendarBox, 'expected task and calendar widgets at 1024px')
      assert.ok(
        Math.abs(taskBox.y - calendarBox.y) <= 2,
        `task and calendar widgets should share a row at 1024px: ${taskBox.y} !== ${calendarBox.y}`,
      )
    }

    const target = resolve(output, `home-${viewport.width}.png`)
    await page.screenshot({ path: target, fullPage: true })
    assert.ok((await stat(target)).size > 10_000, `blank or incomplete screenshot at ${viewport.width}px`)
    await page.close()
  }
} finally {
  await browser.close()
}

console.log('Study UI responsive checks passed')
