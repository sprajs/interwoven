import { EVENT_NAMES, plottedLifeEvents, type LifeEvent } from '../data/lifecycle.ts'
import type { RawNode } from '../data/types.ts'
import { BOX, BREAK, FONT_FAMILY, hexRgb, INK as INK_HEX, LAYOUT, LINE, NAME_AREA, NAME_STYLE, PAPER as PAPER_HEX, RULE_ALPHA, RULER_DARK, RULER_LIGHT, SHEET as SHEET_HEX, TYPE, UNIT, type TypeStep } from '../design.ts'
import type { Engine } from './Engine.ts'
import { formatYear } from './time.ts'

const INK = { primary: hexRgb(INK_HEX.primary), secondary: hexRgb(INK_HEX.secondary), muted: hexRgb(INK_HEX.muted) }
const PAPER = hexRgb(PAPER_HEX)
const SHEET = hexRgb(SHEET_HEX)
const CELL = UNIT
/** Paper left around words that sit directly on the chart. */
const HALO = 3
const HALO_ALPHA = 0.92
const LABEL_GAP = UNIT
const MAX_NAMES = 140
const VISIT_BUDGET = 9000
/** Below these numbers of entries in view, boxes start to speak in sentences. */
const SENTENCE_BELOW = 12
const PROSE_BELOW = 5
const NOTE_LINE = TYPE.note.line

/** A font from the type scale. Italic is kept for science, as maps keep it for water. */
function font(step: TypeStep, weight = 400, italic = false): string {
  return `${italic ? 'italic ' : ''}${weight} ${TYPE[step].size}px ${FONT_FAMILY}`
}

/** The font of an entry's name. They are asked for many times a frame, so each is built once. */
const nameFonts = new Map<string, string>()
function nameFont(node: RawNode): string {
  const key = `${node.level}${node.kind}`
  let value = nameFonts.get(key)
  if (value === undefined) {
    const style = NAME_STYLE[node.level] ?? NAME_STYLE[3]!
    value = font(style.step, style.weight, node.kind === 'science')
    nameFonts.set(key, value)
  }
  return value
}
/** In tight rows every name is the small size, and rank shows in its weight. */
const rowFont = (node: RawNode): string => font('note', node.level === 0 ? 600 : 500, node.kind === 'science')
const nameStep = (node: RawNode): TypeStep => (NAME_STYLE[node.level] ?? NAME_STYLE[3]!).step

/** A date short enough to read at a glance. The sheet gives its full wording and basis. */
export function shortDate(node: RawNode): string {
  // These are stored historical years, unlike ruler ticks or camera coordinates: do not round.
  const storedYear = (year: number): string => {
    if (year >= 0) return String(year)
    const [whole, fraction] = String(-year).split('.')
    return `${whole!.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}${fraction === undefined ? '' : `.${fraction}`} BCE`
  }
  const date = node.entry_date
  const qualification = date?.status === 'approximate' ? 'c. ' : ''
  if (node.date_kind === 'known_by') return `by ${qualification}${storedYear(date?.latest?.year ?? node.end ?? node.year)}`
  if (node.date_kind === 'known_from') return `not before ${qualification}${storedYear(date?.earliest?.year ?? node.start ?? node.year)}`
  const start = date?.earliest?.year ?? node.start
  const end = date?.latest?.year ?? node.end
  if (node.date_kind === 'interval' && start !== undefined && end !== undefined) return `${qualification}${storedYear(start)}–${storedYear(end)}`
  return `${qualification}${storedYear(date?.earliest?.year ?? date?.latest?.year ?? node.year)}`
}

let occupancy = new Uint8Array(0)
/** How many marks sit in each cell, so that a box can avoid covering them. */
let marksIn = new Uint16Array(0)
let cols = 0
let rows = 0
const widthCache = new Map<string, number>()

function resetOccupancy(width: number, height: number): void {
  cols = Math.ceil(width / CELL) + 1
  rows = Math.ceil(height / CELL) + 1
  if (occupancy.length < cols * rows) {
    occupancy = new Uint8Array(cols * rows)
    marksIn = new Uint16Array(cols * rows)
  } else {
    occupancy.fill(0, 0, cols * rows)
    marksIn.fill(0, 0, cols * rows)
  }
}

function marksCovered(x0: number, y0: number, x1: number, y1: number): number {
  const c0 = Math.max(0, Math.floor(x0 / CELL))
  const c1 = Math.min(cols - 1, Math.floor(x1 / CELL))
  const r0 = Math.max(0, Math.floor(y0 / CELL))
  const r1 = Math.min(rows - 1, Math.floor(y1 / CELL))
  let count = 0
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) count += marksIn[r * cols + c]!
  return count
}

function blocked(x0: number, y0: number, x1: number, y1: number): boolean {
  const c0 = Math.max(0, Math.floor(x0 / CELL))
  const c1 = Math.min(cols - 1, Math.floor(x1 / CELL))
  const r0 = Math.max(0, Math.floor(y0 / CELL))
  const r1 = Math.min(rows - 1, Math.floor(y1 / CELL))
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) if (occupancy[r * cols + c]) return true
  return false
}

function occupy(x0: number, y0: number, x1: number, y1: number): void {
  const c0 = Math.max(0, Math.floor(x0 / CELL))
  const c1 = Math.min(cols - 1, Math.floor(x1 / CELL))
  const r0 = Math.max(0, Math.floor(y0 / CELL))
  const r1 = Math.min(rows - 1, Math.floor(y1 / CELL))
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) occupancy[r * cols + c] = 1
}

function measure(ctx: CanvasRenderingContext2D, text: string, fontName: string): number {
  const key = `${fontName}|${text}`
  let w = widthCache.get(key)
  if (w === undefined) {
    ctx.font = fontName
    w = ctx.measureText(text).width
    widthCache.set(key, w)
  }
  return w
}

function wrap(ctx: CanvasRenderingContext2D, text: string, fontName: string, width: number): string[] {
  const lines: string[] = []
  let line = ''
  for (const word of text.split(/\s+/)) {
    const next = line ? `${line} ${word}` : word
    if (line && measure(ctx, next, fontName) > width) {
      lines.push(line)
      line = word
    } else {
      line = next
    }
  }
  if (line) lines.push(line)
  return lines
}

/** What a named entry's box holds, worked out once per entry. */
interface BoxShape {
  date: string
  dateWidth: number
  lines: string[]
  width: number
  height: number
  line: number
}
const shapes = new Map<number, BoxShape>()

function shapeOf(ctx: CanvasRenderingContext2D, i: number, node: RawNode): BoxShape {
  let shape = shapes.get(i)
  if (shape) return shape
  const date = shortDate(node)
  const dateWidth = measure(ctx, date, font('note', 500))
  const fontName = nameFont(node)
  const lines = wrap(ctx, node.title, fontName, LAYOUT.column)
  const nameWidth = Math.max(...lines.map((l) => measure(ctx, l, fontName)))
  const line = TYPE[nameStep(node)].line
  shape = { date, dateWidth, lines, line, width: BOX.edge + dateWidth + 2 * BOX.pad + nameWidth + 2 * BOX.pad, height: lines.length * line + UNIT }
  shapes.set(i, shape)
  return shape
}

/** Forgets widths measured with a fallback font before the web font arrived. */
export function clearTextCache(): void {
  widthCache.clear()
  shapes.clear()
}

/** Draws text and the ruler above the GL layer. */
export function drawOverlay(engine: Engine, ctx: CanvasRenderingContext2D, dt: number): void {
  const cam = engine.camera
  const W = cam.width
  const H = cam.height
  ctx.setTransform(engine.dpr, 0, 0, engine.dpr, 0, 0)
  ctx.clearRect(0, 0, W, H)
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'left'
  ctx.lineJoin = 'round'
  resetOccupancy(W, H)

  drawFamilies(engine, ctx, W)
  if (engine.mix.weave > 0.02) drawLifeMarks(engine, ctx, W)
  drawNames(engine, ctx, dt, W)
  drawPleats(engine, ctx)
  drawRuler(engine, ctx, W)
  drawAttention(engine, ctx)
  drawBracket(engine, ctx, W)
  if (engine.view.mode === 'density' && engine.pointer && engine.hovered === null && engine.pointerZone === 'chart') drawDensityProbe(engine, ctx, W)
  if (engine.pointerZone === 'ruler' && engine.pointer && !engine.bracket) drawRulerCursor(engine, ctx)
}

/** Each subject family's name, kept at the left of the view, on a rule above its first row. */
function drawFamilies(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const alpha = engine.mix.families
  if (alpha < 0.02) return
  const pile = engine.mix.pile
  const model = engine.model!
  const cam = engine.camera
  const frame = engine.frameBounds()
  const heading = font('note', 600)
  ctx.save()
  ctx.font = heading
  ctx.fontVariantCaps = 'all-small-caps'
  ctx.letterSpacing = '0.06em'
  model.families.forEach((family, k) => {
    // In the density view each family has a row of its own, and its heading travels there.
    const row = engine.pileRows[k]
    const top = ((row ? family.top + (row.top - family.top) * pile : family.top) - cam.cy) * cam.yScale + cam.centerY
    const bottom = ((row ? family.bottom + (row.bottom - family.bottom) * pile : family.bottom) - cam.cy) * cam.yScale + cam.centerY
    const y = Math.max(frame.top + NOTE_LINE / 2 + 2, top - NOTE_LINE + 1)
    if (y > bottom + NOTE_LINE || y > frame.bottom - NOTE_LINE) return
    const line = y - NOTE_LINE / 2 - 1
    if (top - NOTE_LINE >= frame.top) {
      ctx.fillStyle = `rgba(${INK.primary},${RULE_ALPHA.rule * alpha})`
      ctx.fillRect(0, line, W, LINE.hair)
    }
    // Stays clear of a side sheet on the left, and otherwise sits in the page margin.
    const x = cam.insets.left > LAYOUT.margin ? cam.insets.left : UNIT * 2
    const text = `${family.name}  ${row && pile > 0.5 ? row.count : family.count}`
    const width = measure(ctx, text, heading) * 0.9
    // On a wide page a pile leaves its heading clear, so no patch need cross the time bands.
    const patch = W < BREAK.wide ? 1 : 1 - pile
    if (patch > 0) {
      ctx.fillStyle = `rgba(${PAPER},${alpha * patch})`
      ctx.fillRect(x - 3, y - NOTE_LINE / 2, width + 2 * UNIT + 6, NOTE_LINE)
    }
    ctx.fillStyle = `rgba(${hexRgb(family.ink)},${alpha})`
    ctx.fillRect(x, y - 4, 8, 8)
    ctx.fillStyle = `rgba(${INK.secondary},${alpha})`
    ctx.fillText(text, x + 2 * UNIT, y)
    if (alpha > 0.5) occupy(x, y - NOTE_LINE / 2, x + width + 2 * UNIT, y + NOTE_LINE / 2)
  })
  ctx.restore()
}

/** Where a name sits relative to its mark. */
interface Place {
  dx: number
  dy: number
  width: number
  height: number
}
const lastPlace = new Map<number, Place>()
/** How many marks a box may cover, by rank. A key discovery is worth covering a few. */
const MAY_COVER = [3, 2, 1, 1]
/** Above this many entries, avoiding every mark costs more than it gives. */
const MARK_AVOID_LIMIT = 5000

/**
 * Names enter by rank until the page has as many as it can hold comfortably. Zooming in puts
 * fewer entries in view, so the same allowance reaches further down the ranks: key discoveries
 * first, then more and more of the tree beneath them. Every other entry still shows as a mark.
 */
function drawNames(engine: Engine, ctx: CanvasRenderingContext2D, dt: number, W: number): void {
  const model = engine.model!
  const cam = engine.camera
  const nodes = model.nodes
  const ys = engine.yNow
  const radius = model.radius
  const byPriority = model.byPriority
  const alphaOf = engine.labelAlpha
  const state = engine.state
  const frame = engine.frameBounds()
  const top = frame.top + 4
  const bottom = frame.bottom - 4
  // The piles are the picture here, so only what has your attention is named.
  const densityMode = engine.view.mode === 'density'
  const inReach = engine.view.mode === 'reach'
  const inStory = engine.view.mode === 'story' && engine.view.story !== null
  const boxed = !(inReach || inStory)
  const rightLimit = W - cam.insets.right + 2 * UNIT
  const leftLimit = cam.insets.left > LAYOUT.margin ? cam.insets.left : UNIT

  const xs = cam.xScale
  const yScale = cam.yScale
  const cx = cam.centerX
  const cy = cam.centerY
  const wanted = new Map<number, Place>()
  const foldsActive = engine.pleats.length > 0
  if (boxed && model.n <= MARK_AVOID_LIMIT) {
    for (let i = 0; i < model.n; i++) {
      if (state[i * 4]! < 0.5) continue
      const c = Math.floor(((engine.nodeV(i) - cam.cu) * xs + cx) / CELL)
      const r = Math.floor(((ys[i]! - cam.cy) * yScale + cy) / CELL)
      if (c >= 0 && c < cols && r >= 0 && r < rows) marksIn[r * cols + c]! += 1
    }
  }

  const tryPlace = (i: number, must: boolean): void => {
    if (wanted.has(i)) return
    const node = nodes[i]!
    if (state[i * 4]! < 0.3) return
    if (!must && state[i * 4 + 1]! > 0.5) return
    if (!must && foldsActive && engine.inPleat(engine.nodeU(i))) return
    const px = (engine.nodeV(i) - cam.cu) * xs + cx
    const py = (ys[i]! - cam.cy) * yScale + cy
    if (py < top || py > bottom) return
    if (px < -LAYOUT.column || px > W + LAYOUT.column) return
    const shape = boxed ? shapeOf(ctx, i, node) : null
    const width = shape ? shape.width : measure(ctx, node.title, rowFont(node))
    const height = shape ? shape.height : TYPE.note.size
    if (boxed) {
      // A box flies like a flag above or below its mark, its solid edge the pole at the date.
      const lift = radius[i]! * engine.mix.marks + BOX.lift + height / 2
      const flags = [
        { dx: 0, dy: -lift },
        { dx: 0, dy: lift },
        { dx: -width, dy: -lift },
        { dx: -width, dy: lift },
      ]
      const previous = lastPlace.get(i)
      if (previous) flags.sort((a, b) => Number(b.dx === previous.dx && b.dy === previous.dy) - Number(a.dx === previous.dx && a.dy === previous.dy))
      // A small screen has marks everywhere, and needs its key names more than clear marks.
      const limit = must || W < BREAK.compact ? Infinity : (MAY_COVER[node.level] ?? 1)
      let best: { dx: number; dy: number } | null = null
      let least = Infinity
      for (const flag of flags) {
        const x = px + flag.dx
        const y = py + flag.dy
        if (x + width > rightLimit || x < leftLimit || y - height / 2 < top || y + height / 2 > bottom) continue
        if (blocked(x - 3, y - height / 2 - 1, x + width + 3, y + height / 2 + 1)) continue
        const covered = marksCovered(x, y - height / 2, x + width, y + height / 2)
        if (covered > limit) continue
        // What is already showing stays where it is while that still works.
        if (covered < least && (best === null || previous === undefined || covered + 1 < least)) {
          best = flag
          least = covered
        }
      }
      if (!best && must) best = flags.find((f) => px + f.dx >= leftLimit && px + f.dx + width <= rightLimit) ?? flags[0]!
      if (!best) return
      const x = px + best.dx
      const y = py + best.dy
      occupy(x - 3, y - height / 2 - 1, x + width + 3, y + height / 2 + 1)
      wanted.set(i, { dx: best.dx, dy: best.dy, width, height })
      return
    }
    const gap = radius[i]! * engine.mix.marks + LABEL_GAP
    // In rows, a name sits to the left of its mark and its rule runs on to the right.
    const rightX = px + gap
    const leftX = px - gap - width
    const options = inReach ? [leftX, rightX] : [rightX, leftX]
    const margin = 2
    const usable = options.filter((x) => x + width <= rightLimit && x >= leftLimit)
    const free = (x: number) => !blocked(x - margin, py - height / 2 - 1, x + width + margin, py + height / 2 + 1)
    const x0 = usable.find(free) ?? (must ? (usable[0] ?? Math.max(leftLimit, Math.min(rightX, rightLimit - width))) : undefined)
    if (x0 === undefined) return
    occupy(x0 - margin, py - height / 2 - 1, x0 + width + margin, py + height / 2 + 1)
    wanted.set(i, { dx: x0 - px, dy: 0, width, height })
  }

  if (engine.view.selected !== null) tryPlace(engine.view.selected, true)
  if (engine.hovered !== null) tryPlace(engine.hovered, true)
  if (!densityMode) for (const i of engine.emphasis.slice(0, 40)) tryPlace(i, false)
  if (inStory) for (const i of engine.view.story!.members) if (state[i * 4]! > 0.5) tryPlace(i, true)
  if (engine.view.searchHits) for (const i of engine.view.searchHits) tryPlace(i, false)

  const area = Math.max(1, W - cam.insets.left - cam.insets.right) * Math.max(1, bottom - top)
  const allowance = densityMode ? 0 : Math.max(8, Math.min(MAX_NAMES, Math.round((area / NAME_AREA) * (inReach ? 2 : 1))))

  // Names already showing go first within each rank, so they do not flicker as the view moves.
  let visited = 0
  const n = byPriority.length
  for (let start = 0; start < n && wanted.size < allowance && visited < VISIT_BUDGET; ) {
    const level = nodes[byPriority[start]!]!.level
    let end = start
    while (end < n && nodes[byPriority[end]!]!.level === level) end++
    for (let k = start; k < end && wanted.size < allowance; k++) {
      const i = byPriority[k]!
      if (alphaOf[i]! > 0.3) tryPlace(i, false)
    }
    for (let k = start; k < end && wanted.size < allowance && visited < VISIT_BUDGET; k++) {
      visited++
      const i = byPriority[k]!
      if (alphaOf[i]! <= 0.3) tryPlace(i, false)
    }
    start = end
  }

  const fade = Math.min(1, dt * 10)
  let animating = false
  for (let i = 0; i < alphaOf.length; i++) {
    const goal = wanted.has(i) ? 1 : 0
    const a = alphaOf[i]!
    if (a === goal) continue
    alphaOf[i] = Math.abs(goal - a) < 0.01 ? goal : a + (goal - a) * fade
    animating = true
  }
  engine.labelsAnimating = animating

  engine.boxes.length = 0
  // Lowest rank first, so that the most important box is always on top.
  for (let k = byPriority.length - 1; k >= 0; k--) {
    const i = byPriority[k]!
    const a = alphaOf[i]!
    if (a <= 0.01) continue
    const place = wanted.get(i) ?? lastPlace.get(i)
    if (!place) continue
    lastPlace.set(i, place)
    const py = (ys[i]! - cam.cy) * yScale + cy
    if (py < top || py > bottom) continue
    const attention = i === engine.view.selected || i === engine.hovered
    const alpha = a * Math.min(1, state[i * 4]! + (attention ? 1 : 0)) * (1 - state[i * 4 + 1]! * 0.82)
    if (alpha < 0.02) continue
    const px = (engine.nodeV(i) - cam.cu) * xs + cx
    if (boxed) {
      drawBox(engine, ctx, i, px, py, place, alpha)
      if (a > 0.5) engine.boxes.push({ i, x0: px + place.dx, y0: py + place.dy - place.height / 2, x1: px + place.dx + place.width, y1: py + place.dy + place.height / 2 })
    } else {
      drawRowName(engine, ctx, i, px + place.dx, py, alpha)
    }
  }
  for (const i of lastPlace.keys()) if (alphaOf[i]! <= 0.01) lastPlace.delete(i)

  if (boxed && !densityMode) drawNotes(engine, ctx, dt, wanted, W, top, bottom)
  if (boxed && !densityMode) drawCount(engine, ctx, wanted.size, W, bottom)
  if (boxed && !densityMode) drawLinkWords(engine, ctx, wanted, W, top, bottom)
}

/**
 * A named entry: a flag on a pole at its date. The solid edge runs down to the entry's mark, then
 * come its date on a tint of its ink, and its name.
 */
function drawBox(engine: Engine, ctx: CanvasRenderingContext2D, i: number, px: number, py: number, place: Place, alpha: number): void {
  const model = engine.model!
  const node = model.nodes[i]!
  const shape = shapeOf(ctx, i, node)
  const ink = `${model.ink[i * 3]! * 255},${model.ink[i * 3 + 1]! * 255},${model.ink[i * 3 + 2]! * 255}`
  const y = py + place.dy
  const top = Math.round(y - shape.height / 2)
  const left = Math.round(px + place.dx)
  const flipped = place.dx < 0
  const chip = shape.dateWidth + 2 * BOX.pad
  const attention = i === engine.view.selected || i === engine.hovered || engine.state[i * 4 + 2]! > 0.5
  // The pole, from the far edge of the box to the mark.
  const poleX = Math.round(px) - (flipped ? BOX.edge : 0)
  const inner = flipped ? left : left + BOX.edge

  ctx.fillStyle = `rgba(${SHEET},${alpha})`
  ctx.fillRect(left, top, shape.width, shape.height)
  ctx.fillStyle = `rgba(${ink},${BOX.chipAlpha * alpha})`
  ctx.fillRect(inner, top, chip, shape.height)

  // The border says how far the evidence goes: whole for direct, broken for inferred, dotted for a proxy.
  ctx.setLineDash(node.evidence_strength === 'scoped_inference' ? [4, 3] : node.evidence_strength === 'awareness_proxy' ? [1, 2.5] : [])
  ctx.lineWidth = attention ? LINE.stroke : BOX.border
  ctx.strokeStyle = attention ? `rgba(${INK.primary},${alpha})` : `rgba(${ink},${BOX.borderAlpha * alpha})`
  ctx.strokeRect(left + 0.5, top + 0.5, shape.width - 1, shape.height - 1)
  ctx.setLineDash([])
  ctx.fillStyle = `rgba(${ink},${alpha})`
  const poleTop = place.dy < 0 ? top : Math.round(py)
  const poleBottom = place.dy < 0 ? Math.round(py) : top + shape.height
  ctx.fillRect(poleX, poleTop, BOX.edge, poleBottom - poleTop)

  ctx.font = font('note', 500)
  ctx.fillStyle = `rgba(${INK.primary},${alpha})`
  ctx.fillText(shape.date, inner + BOX.pad, y + 0.5)

  ctx.font = nameFont(node)
  const firstY = y - ((shape.lines.length - 1) * shape.line) / 2 + 0.5
  shape.lines.forEach((line, k) => ctx.fillText(line, inner + chip + BOX.pad, firstY + k * shape.line))
}

/** In tight rows there is no room for a box, so a name is set directly on the page. */
function drawRowName(engine: Engine, ctx: CanvasRenderingContext2D, i: number, x: number, y: number, alpha: number): void {
  const node = engine.model!.nodes[i]!
  ctx.font = rowFont(node)
  ctx.lineWidth = HALO
  ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA * alpha})`
  ctx.strokeText(node.title, x, y)
  ctx.fillStyle = `rgba(${INK.primary},${alpha})`
  ctx.fillText(node.title, x, y)
}

const firstSentence = (text: string): string => /^.+?[.!?](\s|$)/.exec(text)?.[0].trim() ?? text
const noteAlpha = new Map<number, number>()
const noteCache = new Map<string, string[]>()

/** With few entries in view, boxes open to say more: first a sentence, then the whole summary. */
function drawNotes(engine: Engine, ctx: CanvasRenderingContext2D, dt: number, wanted: Map<number, Place>, W: number, top: number, bottom: number): void {
  const model = engine.model!
  const cam = engine.camera
  let inView = 0
  for (let i = 0; i < model.n; i++) {
    if (engine.state[i * 4]! < 0.5 || engine.state[i * 4 + 1]! > 0.5) continue
    const x = cam.toX(engine.nodeV(i))
    const y = (engine.yNow[i]! - cam.cy) * cam.yScale + cam.centerY
    if (x >= 0 && x <= W && y >= top && y <= bottom) inView++
    if (inView >= SENTENCE_BELOW) break
  }
  const fade = Math.min(1, dt * 8)
  const showing = new Set<number>()
  if (inView < SENTENCE_BELOW) {
    const noteFont = font('note')
    for (const [i, place] of wanted) {
      const node = model.nodes[i]!
      const text = inView < PROSE_BELOW ? node.summary : firstSentence(node.summary)
      if (!text) continue
      const py = (engine.yNow[i]! - cam.cy) * cam.yScale + cam.centerY
      const left = cam.toX(engine.nodeV(i)) + place.dx
      const width = Math.max(place.width, LAYOUT.column)
      const key = `${i}|${text.length}|${Math.round(width)}`
      let lines = noteCache.get(key)
      if (!lines) {
        lines = wrap(ctx, text, noteFont, width - 2 * BOX.pad - BOX.edge)
        noteCache.set(key, lines)
      }
      // The note opens away from the mark, so that the mark and its line stay in sight.
      const upward = place.dy < 0
      const edge = py + place.dy + (upward ? -place.height / 2 : place.height / 2)
      const room = Math.floor((upward ? edge - top - UNIT : bottom - edge - UNIT) / NOTE_LINE)
      let count = Math.min(lines.length, room, 10)
      const spanOf = (k: number) => (upward ? [edge - k * NOTE_LINE - UNIT, edge - 2] : [edge + 2, edge + k * NOTE_LINE + UNIT]) as [number, number]
      while (count > 0 && blocked(left, spanOf(count)[0], left + width, spanOf(count)[1])) count--
      if (count <= 0 || left + width > W || left < 0) continue
      const y0 = upward ? edge - count * NOTE_LINE - UNIT : edge
      occupy(left, y0, left + width, y0 + count * NOTE_LINE + UNIT)
      showing.add(i)
      const a = (noteAlpha.get(i) ?? 0) + (1 - (noteAlpha.get(i) ?? 0)) * fade
      noteAlpha.set(i, a)
      if (a < 0.98) engine.labelsAnimating = true
      const alpha = a * (1 - engine.state[i * 4 + 1]! * 0.82)
      const height = count * NOTE_LINE + UNIT
      ctx.fillStyle = `rgba(${SHEET},${alpha})`
      ctx.fillRect(left, y0, width, height)
      ctx.strokeStyle = `rgba(${INK.primary},${RULE_ALPHA.rule * alpha})`
      ctx.lineWidth = LINE.hair
      ctx.strokeRect(left + 0.5, y0 + 0.5, width - 1, height - 1)
      ctx.font = noteFont
      ctx.fillStyle = `rgba(${INK.secondary},${alpha})`
      for (let k = 0; k < count; k++) {
        const line = count < lines.length && k === count - 1 ? `${lines[k]!.replace(/[.,;:]?$/, '')}…` : lines[k]!
        ctx.fillText(line, left + BOX.edge + BOX.pad, y0 + UNIT / 2 + NOTE_LINE / 2 + k * NOTE_LINE)
      }
    }
  }
  for (const i of noteAlpha.keys()) if (!showing.has(i)) noteAlpha.delete(i)
}

/** Says how much of the tree is showing as names, so the rest is known to be there. */
function drawCount(engine: Engine, ctx: CanvasRenderingContext2D, named: number, W: number, bottom: number): void {
  const model = engine.model!
  const cam = engine.camera
  let inView = model.n
  if (model.n <= MARK_AVOID_LIMIT) {
    inView = 0
    for (let i = 0; i < model.n; i++) {
      if (engine.state[i * 4]! < 0.5) continue
      const x = cam.toX(engine.nodeV(i))
      const y = (engine.yNow[i]! - cam.cy) * cam.yScale + cam.centerY
      if (x >= 0 && x <= W && y >= cam.insets.top && y <= bottom) inView++
    }
  }
  const text = named >= inView ? `All ${inView} in view are named` : `${named} of ${inView} in view are named. Zoom in for more.`
  ctx.font = font('note')
  const width = measure(ctx, text, ctx.font)
  const x = cam.insets.left
  const y = bottom - NOTE_LINE / 2
  if (blocked(x, y - NOTE_LINE / 2, x + width, y + NOTE_LINE / 2)) return
  ctx.lineWidth = HALO
  ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
  ctx.strokeText(text, x, y)
  ctx.fillStyle = `rgba(${INK.muted},1)`
  ctx.fillText(text, x, y)
}

/** What a link claims, written along it, when an entry at one end has been chosen. */
function drawLinkWords(engine: Engine, ctx: CanvasRenderingContext2D, wanted: Map<number, Place>, W: number, top: number, bottom: number): void {
  const model = engine.model!
  const cam = engine.camera
  const selected = engine.view.selected
  if (selected === null) return
  const wordFont = font('note')
  for (const edge of model.edges) {
    if (edge.source !== selected && edge.target !== selected) continue
    if (!wanted.has(edge.source) || !wanted.has(edge.target)) continue
    const ax = cam.toX(engine.nodeV(edge.source))
    const bx = cam.toX(engine.nodeV(edge.target))
    const ay = (engine.yNow[edge.source]! - cam.cy) * cam.yScale + cam.centerY
    const by = (engine.yNow[edge.target]! - cam.cy) * cam.yScale + cam.centerY
    const mx = (ax + bx) / 2
    const my = (ay + by) / 2
    if (mx < 0 || mx > W || my < top || my > bottom) continue
    const word = edge.link.relation + (edge.tentative ? ' (awaiting review)' : '')
    const width = measure(ctx, word, wordFont)
    const x0 = Math.max(UNIT, Math.min(W - width - UNIT, mx - width / 2))
    if (blocked(x0, my - NOTE_LINE / 2, x0 + width, my + NOTE_LINE / 2)) continue
    occupy(x0, my - NOTE_LINE / 2, x0 + width, my + NOTE_LINE / 2)
    ctx.font = wordFont
    ctx.lineWidth = HALO
    ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
    ctx.strokeText(word, x0, my)
    ctx.fillStyle = `rgba(${INK.secondary},1)`
    ctx.fillText(word, x0, my)
  }
}

const END_MARK: Record<string, 'bracket' | 'cross' | 'double' | 'fall' | 'rise'> = {
  withdrawal: 'bracket',
  support_end: 'bracket',
  abandonment: 'cross',
  end_of_use: 'double',
  decline: 'fall',
  revival: 'rise',
}

function strokeMark(ctx: CanvasRenderingContext2D, event: LifeEvent, y: number, x1: number, size: number): void {
  const kind = END_MARK[event.type]
  // The drawing below is at full size, scaled about its own position to suit the row height.
  ctx.save()
  ctx.translate(x1, y)
  ctx.scale(size, size)
  ctx.translate(-x1, -y)
  ctx.beginPath()
  if (kind === 'bracket') {
    // Withdrawal: a closing bracket, because it closes the sale and not necessarily the thing.
    ctx.lineWidth = event.type === 'support_end' ? LINE.rule : LINE.stroke
    ctx.moveTo(x1 - 3, y - 5)
    ctx.lineTo(x1, y - 5)
    ctx.lineTo(x1, y + 5)
    ctx.lineTo(x1 - 3, y + 5)
  } else if (kind === 'cross') {
    ctx.lineWidth = LINE.stroke
    ctx.moveTo(x1 - 4, y - 4)
    ctx.lineTo(x1 + 4, y + 4)
    ctx.moveTo(x1 + 4, y - 4)
    ctx.lineTo(x1 - 4, y + 4)
  } else if (kind === 'double') {
    ctx.lineWidth = LINE.stroke
    ctx.moveTo(x1 - 2, y - 5)
    ctx.lineTo(x1 - 2, y + 5)
    ctx.moveTo(x1 + 1.5, y - 5)
    ctx.lineTo(x1 + 1.5, y + 5)
  } else if (kind === 'fall') {
    ctx.lineWidth = LINE.stroke
    ctx.moveTo(x1 - 4, y - 4)
    ctx.lineTo(x1 + 3, y + 4)
  } else if (kind === 'rise') {
    ctx.lineWidth = LINE.stroke
    ctx.moveTo(x1 - 4, y + 4)
    ctx.lineTo(x1 + 3, y - 4)
  } else {
    // Evidence of use: a short upright stroke on the line.
    ctx.lineWidth = LINE.rule
    ctx.moveTo(x1, y - 3.5)
    ctx.lineTo(x1, y + 3.5)
  }
  ctx.stroke()
  ctx.restore()
}

/**
 * The ends of the reach view's rows. Documented events get a mark. Where the evidence stops,
 * three dots and a question mark say so. They are the same length everywhere, because they
 * measure nothing: this is what the page says about an unknown, and it must not read as a
 * length of time.
 */
function drawLifeMarks(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const model = engine.model!
  const cam = engine.camera
  const frame = engine.frameBounds()
  const alpha = engine.mix.weave
  const rowPx = (cam.yScale * 0.976) / Math.max(1, model.n - 1)
  const showDots = rowPx >= 3.4
  const showQuestion = rowPx >= TYPE.note.size
  const showNames = rowPx >= TYPE.note.line + UNIT
  const markSize = Math.min(1, Math.max(0.55, rowPx / 11))
  ctx.lineCap = 'round'
  for (let i = 0; i < model.n; i++) {
    const y = (engine.yNow[i]! - cam.cy) * cam.yScale + cam.centerY
    if (y < frame.top || y > frame.bottom) continue
    const faded = engine.state[i * 4 + 1]!
    if (engine.state[i * 4]! < 0.5) continue
    const local = alpha * (1 - faded * 0.75)
    const record = model.life.get(model.nodes[i]!.id)
    let lastYear = model.reach.any[i]!
    for (const event of plottedLifeEvents(record)) {
      lastYear = Math.max(lastYear, event.end ?? event.year)
      const x0 = engine.yearToX(event.start ?? event.year)
      const x1 = engine.yearToX(event.end ?? event.year)
      if (x1 < -20 || x0 > W + 20) continue
      ctx.strokeStyle = `rgba(${INK.primary},${local})`
      // A date range is a range: a fine bar between the earliest and latest it can be.
      if (x1 - x0 > 2) {
        ctx.lineWidth = LINE.hair
        ctx.beginPath()
        ctx.moveTo(x0, y)
        ctx.lineTo(x1, y)
        ctx.moveTo(x0, y - 2.5)
        ctx.lineTo(x0, y + 2.5)
        ctx.stroke()
      }
      strokeMark(ctx, event, y, x1, markSize)
      // "By 2023" could have been any time before: a little tail to the left says so.
      if (event.bound && markSize > 0.7) {
        const direction = event.bound === 'by' ? -1 : 1
        ctx.lineWidth = LINE.hair
        ctx.setLineDash([1.5, 2.5])
        ctx.beginPath()
        ctx.moveTo(x1 + direction * 3, y)
        ctx.lineTo(x1 + direction * 16, y)
        ctx.stroke()
        ctx.setLineDash([])
      }
      if (showNames && event.role !== 'use') {
        ctx.font = font('note')
        ctx.fillStyle = `rgba(${INK.secondary},${local})`
        ctx.textAlign = 'center'
        ctx.fillText(EVENT_NAMES[event.type] ?? event.type, x1, y - NOTE_LINE / 2 - UNIT / 2)
        ctx.textAlign = 'left'
      }
    }
    // A scoped withdrawal, abandonment or last-use episode never establishes a global ending.
    if (!showDots) continue
    const x = engine.yearToX(Math.max(lastYear, model.nodes[i]!.year))
    if (x < -30 || x > W) continue
    const start = x + model.radius[i]! + 4
    ctx.fillStyle = `rgba(${INK.muted},${local * 0.72})`
    for (let d = 0; d < 3; d++) ctx.fillRect(start + d * 3.4, y - 0.45, 0.95, 0.95)
    if (showQuestion) {
      ctx.font = font('note')
      ctx.fillText('?', start + 12, y)
    }
  }
}

function formatSpan(years: number): string {
  const y = Math.round(years)
  if (y >= 1000) return `${y.toLocaleString('en-US').replace(/,/g, ' ')} years`
  return y === 1 ? '1 year' : `${y} years`
}

/** Says how much time each fold is hiding, so nothing has quietly gone missing. */
function drawPleats(engine: Engine, ctx: CanvasRenderingContext2D): void {
  const pleats = engine.pleats
  if (pleats.length === 0) return
  const cam = engine.camera
  const model = engine.model!
  const frame = engine.frameBounds()
  ctx.font = font('note')
  for (const pleat of pleats) {
    const x0 = cam.toX(engine.foldNow.map(pleat.u0))
    const x1 = cam.toX(engine.foldNow.map(pleat.u1))
    if (x1 - x0 < 12 || x1 < 0 || x0 > cam.width) continue
    const years = Math.abs(model.time.year(pleat.u1, engine.warp) - model.time.year(pleat.u0, engine.warp))
    if (years < 1) continue
    ctx.save()
    ctx.translate((x0 + x1) / 2, frame.top + UNIT * 2)
    ctx.rotate(Math.PI / 2)
    const label = `${formatSpan(years)} folded`
    ctx.lineWidth = HALO
    ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
    ctx.strokeText(label, 0, 0)
    ctx.fillStyle = `rgba(${INK.muted},1)`
    ctx.fillText(label, 0, 0)
    ctx.restore()
  }
}

/** The ruler: cells of two quiet tones, like a map's scale bar, each headed by the year it starts. */
function drawRuler(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const frame = engine.frameBounds()
  const y0 = frame.top - LAYOUT.ruler
  const cells = engine.ticks
  const yearFont = font('note', 600)
  ctx.fillStyle = RULER_LIGHT
  ctx.fillRect(0, y0, W, LAYOUT.ruler)
  ctx.font = yearFont
  for (let k = 0; k < cells.length; k++) {
    const cell = cells[k]!
    const end = cells[k + 1]?.x ?? engine.axisEndX()
    if (end < 0 || cell.x > W) continue
    const a = Math.max(0, cell.x)
    const b = Math.min(W, end)
    if (cell.odd) {
      ctx.fillStyle = RULER_DARK
      ctx.fillRect(a, y0, b - a, LAYOUT.ruler)
    }
    const text = formatYear(cell.year)
    const width = measure(ctx, text, yearFont)
    if (b - a < width + UNIT) continue
    // The year keeps to the left edge of the view while its cell is still in sight.
    ctx.fillStyle = INK_HEX.primary
    ctx.fillText(text, Math.min(a, b - width - 2 * UNIT) + UNIT, y0 + LAYOUT.ruler / 2 + 0.5)
  }
  ctx.fillStyle = `rgb(${INK.primary})`
  ctx.fillRect(0, frame.top - LINE.hair, W, LINE.hair)
  ctx.fillRect(0, frame.bottom, W, LINE.hair)
}

/** A year set on the ruler over whatever cell is there. */
function drawRulerYear(ctx: CanvasRenderingContext2D, text: string, x: number, rulerTop: number): void {
  const yearFont = font('note', 600)
  const width = measure(ctx, text, yearFont)
  const left = Math.max(0, x - width / 2 - UNIT)
  ctx.fillStyle = PAPER_HEX
  ctx.fillRect(left, rulerTop, width + 2 * UNIT, LAYOUT.ruler)
  ctx.strokeStyle = `rgb(${INK.primary})`
  ctx.lineWidth = LINE.stroke
  ctx.strokeRect(left + 0.75, rulerTop + 0.75, width + 2 * UNIT - 1.5, LAYOUT.ruler - 1.5)
  ctx.font = yearFont
  ctx.fillStyle = `rgb(${INK.primary})`
  ctx.fillText(text, left + UNIT, rulerTop + LAYOUT.ruler / 2 + 0.5)
}

/** A line from whatever has your attention up to the ruler, so its date reads on the timeline. */
function drawAttention(engine: Engine, ctx: CanvasRenderingContext2D): void {
  const i = engine.hovered ?? engine.view.selected
  if (i === null) return
  const cam = engine.camera
  const frame = engine.frameBounds()
  const x = cam.toX(engine.nodeV(i))
  if (x < 0 || x > cam.width) return
  const y = (engine.yNow[i]! - cam.cy) * cam.yScale + cam.centerY
  if (y < frame.top) return
  ctx.fillStyle = `rgba(${INK.primary},0.55)`
  ctx.fillRect(x - LINE.hair / 2, frame.top, LINE.hair, Math.min(y, frame.bottom) - frame.top)
  drawRulerYear(ctx, shortDate(engine.model!.nodes[i]!), x, frame.top - LAYOUT.ruler)
}

/** A figure and what it means, used wherever the chart answers a question in place. */
function drawNotePair(ctx: CanvasRenderingContext2D, line: string, note: string, x: number, y: number): void {
  ctx.lineWidth = HALO
  ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
  ctx.font = font('body', 500)
  ctx.strokeText(line, x, y)
  ctx.fillStyle = `rgba(${INK.primary},1)`
  ctx.fillText(line, x, y)
  ctx.font = font('note')
  ctx.strokeText(note, x, y + NOTE_LINE)
  ctx.fillStyle = `rgba(${INK.secondary},1)`
  ctx.fillText(note, x, y + NOTE_LINE)
}

/** A period being marked out along the ruler: what is outside is about to fold away. */
function drawBracket(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const bracket = engine.bracket
  if (!bracket) return
  const frame = engine.frameBounds()
  const a = Math.min(bracket.x0, bracket.x1)
  const b = Math.max(bracket.x0, bracket.x1)
  ctx.fillStyle = `rgba(${PAPER},0.62)`
  ctx.fillRect(0, frame.top, Math.max(0, a), frame.bottom - frame.top)
  ctx.fillRect(b, frame.top, Math.max(0, W - b), frame.bottom - frame.top)
  ctx.fillStyle = `rgba(${INK.primary},0.75)`
  ctx.fillRect(a - LINE.rule / 2, frame.top - UNIT, LINE.rule, frame.bottom - frame.top + UNIT)
  ctx.fillRect(b - LINE.rule / 2, frame.top - UNIT, LINE.rule, frame.bottom - frame.top + UNIT)
  ctx.fillRect(a, frame.top - UNIT, b - a, LINE.rule)
  if (b - a < 8) return
  const y0 = engine.xToYear(a)
  const y1 = engine.xToYear(b)
  const model = engine.model!
  let count = 0
  for (let i = 0; i < model.n; i++) {
    const year = model.nodes[i]!.year
    if (year >= y0 && year <= y1 && engine.passesFilters(i)) count++
  }
  const line = `${formatYear(y0)} to ${formatYear(y1)}`
  const note = `${count.toLocaleString('en-US')} ${count === 1 ? 'entry' : 'entries'}. Release to open this period.`
  const x = Math.min(W - LAYOUT.column, Math.max(UNIT, a + UNIT))
  drawNotePair(ctx, line, note, x, frame.top + TYPE.body.line)
}

/** The exact year under the pointer, and the invitation to open a period. */
function drawRulerCursor(engine: Engine, ctx: CanvasRenderingContext2D): void {
  const pointer = engine.pointer!
  const frame = engine.frameBounds()
  ctx.fillStyle = `rgba(${INK.primary},0.35)`
  ctx.fillRect(pointer.x - LINE.hair / 2, frame.top, LINE.hair, frame.bottom - frame.top)
  drawRulerYear(ctx, formatYear(engine.xToYear(pointer.x)), pointer.x, frame.top - LAYOUT.ruler)
  if (engine.view.mode === 'story' && engine.view.story) return
  const hint = engine.pleatAtX(pointer.x) && engine.openPeriods.length ? 'Click to unfold' : 'Drag along the ruler to open a period'
  ctx.font = font('note')
  const hintWidth = measure(ctx, hint, ctx.font)
  const x = pointer.x + hintWidth + 3 * UNIT > engine.camera.width ? pointer.x - hintWidth - 2 * UNIT : pointer.x + 2 * UNIT
  ctx.lineWidth = HALO
  ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
  ctx.strokeText(hint, x, frame.top + NOTE_LINE)
  ctx.fillStyle = `rgba(${INK.secondary},1)`
  ctx.fillText(hint, x, frame.top + NOTE_LINE)
}

function drawDensityProbe(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const pointer = engine.pointer!
  const cam = engine.camera
  const model = engine.model!
  const bounds = engine.frameBounds()
  if (pointer.y < bounds.top || pointer.y > bounds.bottom) return

  // One line at one year, read on the ruler, and how much of the record has been reached by then.
  const year = engine.xToYear(pointer.x)
  let total = 0
  let reached = 0
  for (let i = 0; i < model.n; i++) {
    if (!engine.passesFilters(i)) continue
    total++
    if (model.nodes[i]!.year <= year) reached++
  }

  ctx.fillStyle = `rgba(${INK.primary},${RULE_ALPHA.frame})`
  ctx.fillRect(pointer.x - LINE.hair / 2, bounds.top, LINE.hair, bounds.bottom - bounds.top)
  drawRulerYear(ctx, formatYear(year), pointer.x, bounds.top - LAYOUT.ruler)

  const text = `${reached.toLocaleString('en-US')} of ${total.toLocaleString('en-US')} entries dated by ${formatYear(year)}`
  ctx.font = font('note')
  const width = measure(ctx, text, ctx.font)
  const right = pointer.x + UNIT
  const flip = right + width > W - cam.insets.right
  const x = flip ? pointer.x - UNIT - width : right
  const y = bounds.top + NOTE_LINE
  ctx.lineWidth = HALO
  ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
  ctx.strokeText(text, x, y)
  ctx.fillStyle = `rgba(${INK.secondary},1)`
  ctx.fillText(text, x, y)
}
