import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { TEST_PORTS, testOrigin } from '../src/config/ports.js'

const serviceDir = resolve(dirname(fileURLToPath(import.meta.url)), '..', 'src', 'services')
const files = [
  'workbench.js',
  'workbenchApprovals.js',
  'workbenchEnvironment.js',
  'workbenchOverview.js',
  'workbenchVersions.js',
]
const source = (await Promise.all(files.map((file) => readFile(resolve(serviceDir, file), 'utf8')))).join('\n')

assert.doesNotMatch(
  source,
  /['"`]\/workbench(?:\/|['"`])/,
  'workbench clients must use the /api proxy prefix in development',
)
assert.match(source, /\/api\/workbench/)

const origin = process.env.WORKBENCH_FRONTEND_ORIGIN || testOrigin(TEST_PORTS.workbench)
const response = await fetch(`${origin}/api/workbench/overview`, {
  headers: { Accept: 'application/json' },
})

assert.equal(response.ok, true, `expected workbench API proxy to return 2xx, got ${response.status}`)
assert.match(response.headers.get('content-type') || '', /application\/json/i)

const payload = await response.json()
assert.equal(payload.ok, true)
assert.equal(typeof payload.data, 'object')

console.log('workbench API routing check passed')
