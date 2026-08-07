import { gzipSync } from 'node:zlib'
import { readdir, readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const assetsDir = fileURLToPath(new URL('../dist/assets/', import.meta.url))
const assets = await readdir(assetsDir)
const chunks = assets.filter((name) => /^animations-[^/]+\.js$/.test(name))

if (chunks.length !== 1) {
  throw new Error(`Expected exactly one animations chunk, found ${chunks.length}`)
}

const file = join(assetsDir, chunks[0])
const source = await readFile(file)
const gzipBytes = gzipSync(source).byteLength
const limit = 45 * 1024

console.log(`${chunks[0]}: ${gzipBytes} bytes gzip (limit ${limit})`)
if (gzipBytes > limit) throw new Error(`animations chunk exceeds ${limit} bytes gzip`)
