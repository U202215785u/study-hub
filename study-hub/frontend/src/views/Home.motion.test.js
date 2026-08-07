import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const source = readFileSync('src/views/Home.vue', 'utf8')

describe('Home motion ownership', () => {
  it('wraps every visible widget in MotionWrapper while retaining props and event forwarding', () => {
    expect(source).toContain('<MotionWrapper\n          v-for="(widget, index) in visibleWidgets"')
    expect(source).toContain('v-bind="propsFor(widget.id)"')
    expect(source).toContain('v-on="listenersFor(widget.id)"')
    expect(source).toContain(':delay="index * 0.06"')
  })
})
