import { describe, expect, it, vi } from 'vitest'
import { createGridDrag } from './useGridDrag.js'

describe('createGridDrag', () => {
  const grid = () => ({ left: 100, top: 200, width: 800, height: 600 })

  it('does not start dragging until the pointer crosses the movement threshold', () => {
    const onStart = vi.fn()
    const onMove = vi.fn()
    const drag = createGridDrag({ getGridRect: grid, onStart, onMove })

    drag.pointerDown({ button: 0, pointerId: 1, clientX: 110, clientY: 210 }, 'knowledge')
    drag.pointerMove({ pointerId: 1, clientX: 114, clientY: 213 })

    expect(onStart).not.toHaveBeenCalled()
    expect(onMove).not.toHaveBeenCalled()
  })

  it('maps an active pointer to a bounded eight-column grid target and completes once', () => {
    const onStart = vi.fn()
    const onMove = vi.fn()
    const onEnd = vi.fn()
    const drag = createGridDrag({ getGridRect: grid, rowHeight: 100, gap: 10, onStart, onMove, onEnd })

    drag.pointerDown({ button: 0, pointerId: 2, clientX: 101, clientY: 201 }, 'knowledge')
    drag.pointerMove({ pointerId: 2, clientX: 899, clientY: 599 })
    drag.pointerUp({ pointerId: 2, clientX: 999, clientY: 999 })

    expect(onStart).toHaveBeenCalledWith('knowledge')
    expect(onMove).toHaveBeenLastCalledWith('knowledge', { x: 7, y: 3 })
    expect(onEnd).toHaveBeenCalledWith('knowledge', { x: 7, y: 3 })
  })

  it('clears an active drag on pointer cancellation without completing it', () => {
    const onEnd = vi.fn()
    const drag = createGridDrag({ getGridRect: grid, onEnd })

    drag.pointerDown({ button: 0, pointerId: 3, clientX: 120, clientY: 220 }, 'knowledge')
    drag.pointerMove({ pointerId: 3, clientX: 140, clientY: 240 })
    drag.pointerCancel({ pointerId: 3 })
    drag.pointerUp({ pointerId: 3, clientX: 500, clientY: 500 })

    expect(onEnd).not.toHaveBeenCalled()
    expect(drag.isDragging()).toBe(false)
  })
})
