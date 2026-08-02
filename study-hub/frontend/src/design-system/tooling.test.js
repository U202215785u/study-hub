import { describe, expect, it } from 'vitest'
import * as studyUi from './index'

describe('Study UI public surface', () => {
  it('exports an object from the stable entry point', () => {
    expect(studyUi).toBeTypeOf('object')
  })
})
