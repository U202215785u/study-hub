import assert from 'node:assert/strict'
import { mkdir, stat } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { TEST_PORTS, testOrigin } from '../src/config/ports.js'

const origin = process.env.STUDY_UI_ORIGIN || testOrigin(TEST_PORTS.dashboard)
const output = resolve('test-results/study-ui')
const viewports = [
  { width: 1440, height: 980 },
  { width: 942, height: 638 },
  { width: 1366, height: 768 },
  { width: 1920, height: 1080 },
  { width: 2560, height: 1440 },
  { width: 390, height: 844 },
]
const nodeIds = ['349:169', '349:516', '349:405', '349:369', '349:471', '349:493', '349:459', '349:484', '349:510']
await mkdir(output, { recursive: true })

async function launchBrowser() {
  try { return await chromium.launch({ headless: true }) }
  catch (error) {
    try { return await chromium.launch({ channel: 'chrome', headless: true }) }
    catch { throw error }
  }
}

async function waitForHomeReady(page) {
  await page.locator('[data-home-motion="widget"]').first().waitFor()
  await page.waitForFunction(() => {
    const widgets = [...document.querySelectorAll('[data-home-motion="widget"]')]
    const stableMotion = widgets.every((node) => {
      const style = getComputedStyle(node)
      return style.opacity === '1' && (style.transform === 'none' || style.transform === 'matrix(1, 0, 0, 1, 0, 0)')
    })
    const contentReady = [...document.querySelectorAll('.dashboard-module-card')].every((card) => card.querySelector(':scope > .dashboard-module-card__content'))
    return widgets.length === 9 && stableMotion && contentReady
  }, undefined, { timeout: 20_000 })
}

const browser = await launchBrowser()
try {
  for (const viewport of viewports) {
    const page = await browser.newPage({ viewport })
    await page.goto(origin, { waitUntil: 'domcontentloaded' })
    await waitForHomeReady(page)
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

    const [stageBox, navBox, gridBox, footerBox] = await Promise.all([
      page.locator('[data-dashboard-stage]').boundingBox(),
      page.locator('[data-visual-anchor="nav"]').boundingBox(),
      page.locator('[data-visual-anchor="grid"]').boundingBox(),
      page.locator('.home-footer').boundingBox(),
    ])
    assert.ok(stageBox && navBox && gridBox && footerBox, `adaptive layout anchors must exist at ${viewport.width}px`)
    const mobile = viewport.width < 768
    const scale = Math.min(viewport.width / 1440, viewport.height / 980)
    if (mobile) {
      assert.ok(gridBox.height > viewport.height, 'mobile grid must remain vertically scrollable')
      const mobileCards = await page.evaluate(() => [...document.querySelectorAll('.dashboard-module-card')].map((card) => ({
        scrollWidth: card.scrollWidth, clientWidth: card.clientWidth, scrollHeight: card.scrollHeight, clientHeight: card.clientHeight,
      })))
      assert.equal(mobileCards.some((card) => card.scrollWidth > card.clientWidth + 1 || card.scrollHeight > card.clientHeight + 1), false, 'mobile dashboard cards must not clip their content')
    }
    if (!mobile) {
    assert.ok(Math.abs(stageBox.width - 1440 * scale) <= 2, `stage width is not proportional at ${viewport.width}px`)
    assert.ok(Math.abs(stageBox.height - 980 * scale) <= 2, `stage height is not proportional at ${viewport.width}px`)
    assert.ok(Math.abs(stageBox.x - (viewport.width - stageBox.width) / 2) <= 2, `stage is not horizontally centered at ${viewport.width}px`)
    assert.ok(Math.abs(stageBox.y - (viewport.height - stageBox.height) / 2) <= 2, `stage is not vertically centered at ${viewport.width}px`)
    assert.ok(Math.abs(navBox.x - (stageBox.x + 60 * scale)) <= 3, `navigation x is not tied to the stage at ${viewport.width}px`)
    assert.ok(Math.abs(navBox.width - 1320 * scale) <= 3, `navigation width is not tied to the stage at ${viewport.width}px`)
    assert.ok(Math.abs(gridBox.x - (stageBox.x + 36 * scale)) <= 3, `grid x is not tied to the stage at ${viewport.width}px`)
    assert.ok(Math.abs(gridBox.width - 1368 * scale) <= 3, `grid width is not tied to the stage at ${viewport.width}px`)
    assert.ok(footerBox.y + footerBox.height <= viewport.height + 2, `footer falls below the viewport at ${viewport.width}px`)
    }

    const cardLayoutReport = await page.evaluate((stageScale) => [...document.querySelectorAll('.dashboard-module-card')].map((card) => {
      const content = card.querySelector(':scope > .dashboard-module-card__content')
      if (!content) return { missingContent: true }
      const style = getComputedStyle(content)
      const paddings = ['Top', 'Right', 'Bottom', 'Left'].map((side) => Number.parseFloat(style[`padding${side}`]) * stageScale)
      return {
        missingContent: false,
        paddings,
        expectedInset: 16 * stageScale,
        overflows: content.scrollWidth > content.clientWidth + 1 || content.scrollHeight > content.clientHeight + 1,
      }
    }), mobile ? 1 : scale)
    assert.equal(cardLayoutReport.length, 9, `expected nine dashboard cards at ${viewport.width}px`)
    assert.equal(cardLayoutReport.some(({ missingContent }) => missingContent), false, `a dashboard card has no content region at ${viewport.width}px`)
    for (const card of cardLayoutReport) {
      for (const inset of card.paddings) assert.ok(Math.abs(inset - card.expectedInset) <= 1, `card inset is not 16px at ${viewport.width}px`)
      assert.equal(card.overflows, false, `dashboard card content overflows at ${viewport.width}px`)
    }

    if (viewport.width === 942) {
      const compactWidgetReport = await page.evaluate(() => {
        const selectors = [
          '.heatmap-widget',
          '.calendar-agenda',
          '.memory-widget',
          '.command-widget',
          '.creation-widget',
          '.workflow-widget',
        ]
        const overflowing = selectors.filter((selector) => {
          const element = document.querySelector(selector)
          return !element || element.scrollWidth > element.clientWidth + 2 || element.scrollHeight > element.clientHeight + 2
        })
        const wrapping = [
          '.calendar-agenda h2',
          '.creation-widget nav button',
          '.workflow-widget li button',
        ].filter((selector) => [...document.querySelectorAll(selector)].some((element) => {
          const style = getComputedStyle(element)
          return style.whiteSpace !== 'nowrap' || element.scrollWidth > element.clientWidth + 1
        }))
        const heatmap = document.querySelector('.heatmap-widget__grid')?.getBoundingClientRect()
        const caption = document.querySelector('.heatmap-widget > p')?.getBoundingClientRect()
        return {
          overflowing,
          wrapping,
          heatmapClearsCaption: !caption || Boolean(heatmap && heatmap.bottom <= caption.top - 2),
        }
      })
      assert.deepEqual(compactWidgetReport.overflowing, [], `compact widgets overflow: ${compactWidgetReport.overflowing.join(', ')}`)
      assert.deepEqual(compactWidgetReport.wrapping, [], `compact labels wrap: ${compactWidgetReport.wrapping.join(', ')}`)
      assert.equal(compactWidgetReport.heatmapClearsCaption, true, 'heatmap overlaps its caption at compact PC size')
    }

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
