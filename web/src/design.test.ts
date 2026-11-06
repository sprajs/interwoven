import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { CHAR_WIDTH, contrast, INK, LAYOUT, MARK_RADIUS, PAPER, RULER_LIGHT, SHEET, TYPE, UNIT, X_HEIGHT } from './design.ts'

const root = import.meta.dirname
const css = readFileSync(join(root, 'styles.css'), 'utf8')
const uiFiles = readdirSync(join(root, 'ui'))
  .filter((name) => name.endsWith('.tsx'))
  .map((name) => ({ name, text: readFileSync(join(root, 'ui', name), 'utf8') }))

describe('the type scale', () => {
  it('steps by about 6:5 between neighbours', () => {
    const sizes = Object.values(TYPE).map((step) => step.size)
    for (let i = 1; i < sizes.length; i++) {
      const ratio = sizes[i]! / sizes[i - 1]!
      expect(ratio).toBeGreaterThan(1.15)
      expect(ratio).toBeLessThan(1.25)
    }
  })

  it('sets every step on a leading of whole units, within 120 to 145 percent', () => {
    for (const step of Object.values(TYPE)) {
      expect(step.line % (UNIT / 2)).toBe(0)
      const leading = step.line / step.size
      expect(leading).toBeGreaterThanOrEqual(1.2)
      expect(leading).toBeLessThanOrEqual(1.45)
    }
  })

  it('matches the interface values in the stylesheet', () => {
    for (const [name, step] of Object.entries(TYPE)) {
      expect(css).toContain(`--text-${name}: ${step.size}px;`)
      expect(css).toContain(`--text-${name}--line-height: ${step.line}px;`)
    }
  })
})

describe('measure', () => {
  const characters = (width: number, size: number) => width / (size * CHAR_WIDTH)

  it('keeps a sheet of body text within 45 to 90 characters', () => {
    const count = characters(LAYOUT.sheet - 2 * LAYOUT.sheetPad, TYPE.body.size)
    expect(count).toBeGreaterThanOrEqual(45)
    expect(count).toBeLessThanOrEqual(90)
  })

  it('keeps a column of notes within the 40 to 50 usual for columns', () => {
    const count = characters(LAYOUT.column, TYPE.note.size)
    expect(count).toBeGreaterThanOrEqual(40)
    expect(count).toBeLessThanOrEqual(50)
  })
})

describe('ink', () => {
  it('keeps every text ink above AA contrast on both papers', () => {
    for (const ink of Object.values(INK)) {
      expect(contrast(ink, PAPER)).toBeGreaterThanOrEqual(4.5)
      expect(contrast(ink, SHEET)).toBeGreaterThanOrEqual(4.5)
    }
  })

  it('keeps the ruler readable in both of its shades', () => {
    expect(contrast(INK.primary, RULER_LIGHT)).toBeGreaterThanOrEqual(4.5)
  })

  it('matches the stylesheet', () => {
    expect(css).toContain(`--color-ink: ${INK.primary};`)
    expect(css).toContain(`--color-ink-2: ${INK.secondary};`)
    expect(css).toContain(`--color-ink-3: ${INK.muted};`)
    expect(css).toContain(`--color-paper: ${PAPER};`)
    expect(css).toContain(`--color-sheet: ${SHEET};`)
  })
})

describe('marks', () => {
  it('stand at least as tall as the lowercase of a name, so they can be seen', () => {
    for (const radius of MARK_RADIUS) expect(radius * 2).toBeGreaterThanOrEqual(TYPE.note.size * X_HEIGHT)
  })
})

describe('no one-off values', () => {
  const lint = (pattern: RegExp, why: string) => {
    for (const { name, text } of uiFiles) {
      const found = text.match(pattern)
      expect(found, `${name}: ${why}`).toBeNull()
    }
  }

  it('uses named type steps in the interface', () => {
    lint(/\btext-\[\d/g, 'a text size outside the scale')
    lint(/\bleading-[\w[]/g, 'leading set separately from its type step')
    lint(/\bfont-(bold|semibold|light)\b/g, 'a weight outside the system')
  })

  it('uses the spacing scale, not arbitrary lengths', () => {
    lint(/\b[\w-]+-\[-?[\d.]+(px|rem|em)\]/g, 'an arbitrary length')
    lint(/\bmin-\[/g, 'a breakpoint outside the named ones')
  })

  it('uses only the steps of the spacing scale', () => {
    const allowed = new Set(['0', '1', '2', '3', '4', '6', '8', '12', '16', '18', '24'])
    for (const { name, text } of uiFiles) {
      for (const match of text.matchAll(/(?:^|[\s"'`:-])-?(?:m|p|gap|space)(?:[trblxy])?(?:-[xy])?-(\d+(?:\.\d+)?)\b/g)) {
        expect(allowed.has(match[1]!), `${name}: spacing step ${match[0].trim()}`).toBe(true)
      }
    }
  })

  it('reserves italic for science in the interface', () => {
    lint(/\bitalic\b/g, 'italic used for something other than science: use .science or .note')
    lint(/<em\b/g, 'italic used for emphasis')
  })

  it('draws canvas text only from the type scale', () => {
    for (const file of ['overlay.ts']) {
      const text = readFileSync(join(root, 'engine', file), 'utf8')
      expect(text.match(/\d(?:\.\d+)?px/g), `${file}: a type size outside the scale`).toBeNull()
    }
  })
})
