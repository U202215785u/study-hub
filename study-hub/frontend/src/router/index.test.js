import { describe, expect, it } from 'vitest'
import router from './index.js'

describe('application routes', () => {
  it('resolves the full content parser workspace', () => {
    expect(router.resolve('/content-parser').name).toBe('contentParser')
  })
})
