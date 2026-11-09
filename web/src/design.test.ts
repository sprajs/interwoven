import { expect, it } from 'vitest'
import { contrast, INK, PAPER, RULER_DARK, RULER_LIGHT, SHEET } from './design.ts'

it('keeps text readable on the page, sheet and ruler', () => {
  for (const ink of Object.values(INK)) {
    expect(contrast(ink, PAPER)).toBeGreaterThanOrEqual(4.5)
    expect(contrast(ink, SHEET)).toBeGreaterThanOrEqual(4.5)
  }
  expect(contrast(INK.primary, RULER_LIGHT)).toBeGreaterThanOrEqual(4.5)
  expect(contrast(INK.primary, RULER_DARK)).toBeGreaterThanOrEqual(4.5)
})
