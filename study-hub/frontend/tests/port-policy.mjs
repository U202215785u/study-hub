import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { FRONTEND_DEV_PORT, TEST_PORTS, testOrigin } from '../src/config/ports.js'

assert.equal(FRONTEND_DEV_PORT, 5173)
assert.deepEqual(TEST_PORTS, Object.freeze({ workbench: 5180, dashboard: 5181, tutorial: 5182 }))
assert.equal(testOrigin(TEST_PORTS.dashboard), 'http://127.0.0.1:5181')
assert.equal(testOrigin(TEST_PORTS.tutorial), 'http://127.0.0.1:5182')

const testSources = await Promise.all([
  'workbench-api-routing.mjs',
  'home-visual-overlay.mjs',
  'home-responsive.mjs',
  'home-layout-persistence.mjs',
].map((file) => readFile(new URL(`./${file}`, import.meta.url), 'utf8')))

for (const source of testSources) {
  assert.doesNotMatch(source, /127\.0\.0\.1:517[48]/)
  assert.match(source, /TEST_PORTS|testOrigin/)
}

const portGuide = await readFile(new URL('../../docs/端口规范.md', import.meta.url), 'utf8')
assert.match(portGuide, /http:\/\/localhost:8741/)
assert.match(portGuide, /8742.*开发/)
assert.match(portGuide, /前端开发.*5173/)
assert.match(portGuide, /5180-5189/)

console.log('Study Hub port policy checks passed')
