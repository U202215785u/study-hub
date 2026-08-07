const distanceFrom = (start, event) => Math.hypot(event.clientX - start.clientX, event.clientY - start.clientY)

export function createGridDrag({
  getGridRect,
  columns = 8,
  rowHeight = 153.36,
  gap = 14.31,
  threshold = 6,
  onStart = () => {},
  onMove = () => {},
  onEnd = () => {},
} = {}) {
  let active

  const targetFor = (event) => {
    const rect = getGridRect?.()
    if (!rect?.width || !rect?.height) return { x: 0, y: 0 }
    const columnWidth = rect.width / columns
    return {
      x: Math.min(columns - 1, Math.max(0, Math.floor((event.clientX - rect.left) / columnWidth))),
      y: Math.max(0, Math.floor((event.clientY - rect.top) / (rowHeight + gap))),
    }
  }

  const reset = () => { active = undefined }

  return {
    pointerDown(event, id) {
      if (event.button !== 0) return
      active = { id, pointerId: event.pointerId, clientX: event.clientX, clientY: event.clientY, dragging: false, target: undefined }
    },
    pointerMove(event) {
      if (!active || active.pointerId !== event.pointerId) return
      if (!active.dragging) {
        if (distanceFrom(active, event) < threshold) return
        active.dragging = true
        onStart(active.id)
      }
      active.target = targetFor(event)
      onMove(active.id, active.target)
    },
    pointerUp(event) {
      if (!active || active.pointerId !== event.pointerId) return
      const finished = active
      reset()
      if (finished.dragging) onEnd(finished.id, finished.target || targetFor(event))
    },
    pointerCancel(event) {
      if (active?.pointerId === event.pointerId) reset()
    },
    isDragging() { return Boolean(active?.dragging) },
  }
}
