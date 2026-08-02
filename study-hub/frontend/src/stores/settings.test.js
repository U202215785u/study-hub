import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'
import { useSettingsStore } from './settings.js'

describe('settings API base', () => {
  it('uses the Vite API proxy during browser development', () => {
    setActivePinia(createPinia())
    expect(useSettingsStore().apiBase).toBe('/api')
  })
})
