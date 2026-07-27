import { beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const assistantSource = readFileSync(
  resolve(process.cwd(), '../extension/bing-assistant.js'),
  'utf8'
)

describe('Bing Search Assistant state and interactions', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('use built-in rules')))
    window.matchMedia = vi.fn().mockReturnValue({ matches: false })
    vi.stubGlobal('chrome', {
      runtime: { getURL: path => `chrome-extension://studyhub/${path}` },
      storage: {
        local: {
          get: vi.fn().mockResolvedValue({
            studyhub_v3_state: { collapsed: false, closed: false }
          }),
          set: vi.fn().mockResolvedValue(undefined)
        },
        sync: {
          get: vi.fn().mockResolvedValue({}),
          set: vi.fn().mockResolvedValue(undefined)
        }
      }
    })
  })

  it('defaults missing pinned state to draggable and toggles AI collapse by click', async () => {
    window.eval(assistantSource)
    document.dispatchEvent(new Event('DOMContentLoaded'))

    let host
    await vi.waitFor(() => {
      host = document.getElementById('studyhub-assistant-host')
      expect(host?.shadowRoot?.querySelector('.sh-btn-pin')).toBeTruthy()
    })

    const shadow = host.shadowRoot
    const pinButton = shadow.querySelector('.sh-btn-pin')
    expect.soft(pinButton.title).toContain('未固定')

    const aiSection = shadow.querySelector('.sh-ai-section')
    const wasCollapsed = aiSection.classList.contains('collapsed')
    shadow.querySelector('.sh-ai-header').click()
    expect(aiSection.classList.contains('collapsed')).toBe(!wasCollapsed)
  })
})
