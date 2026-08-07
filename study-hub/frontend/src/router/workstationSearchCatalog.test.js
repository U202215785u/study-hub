import { describe, expect, it } from 'vitest'
import catalog from '../../../shared/workstation-search-catalog.json'
import router from './index.js'

describe('workstation search catalog', () => {
  it('contains only declared internal routes', () => {
    for (const entry of catalog) {
      const resolved = router.resolve(entry.navigation.path)
      expect(resolved.matched.length, entry.navigation.path).toBeGreaterThan(0)
      expect(resolved.redirectedFrom, entry.navigation.path).toBeUndefined()
    }
  })
})
