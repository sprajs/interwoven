import { documentedSpan, EVENT_NAMES, isFinal, type LifeEvent } from '../data/lifecycle.ts'
import { hexRgb, INK as INK_HEX, LAYOUT, LINE, PAPER as PAPER_HEX, ROW_TIER_TYPE, RULE_ALPHA, TIER_INK, TIER_TYPE, TYPE, UNIT, type TypeStep } from '../design.ts'
import { formatYear } from './time.ts'
import type { Engine } from './Engine.ts'

const SERIF = '"EB Garamond Variable", Georgia, "Times New Roman", serif'
const INK = { primary: hexRgb(INK_HEX.primary), secondary: hexRgb(INK_HEX.secondary), muted: hexRgb(INK_HEX.muted) }
const PAPER = hexRgb(PAPER_HEX)
const CELL = UNIT
/** Paper left around words so lines appear to be drawn around them. */
const HALO = 3
const HALO_ALPHA = 0.92
/** The gap between a mark and its name: close enough to belong, not touching. */
const LABEL_GAP = UNIT
const MAX_LABELS = 140
const VISIT_BUDGET = 9000
/** Below these numbers of entries in view, the chart starts to speak in sentences. */
const DATES_BELOW = 34
const SENTENCE_BELOW = 13
const PROSE_BELOW = 6
const PROSE_WIDTH = LAYOUT.column
const PROSE_LINE = TYPE.note.line

/** Rows hold names in a smaller, more even size, as Priestley set his. */
let rowsMode = false

/** A font from the type scale. Italic is kept for science, as maps keep it for water. */
function font(step: TypeStep, italic = false): string {
  return `${italic ? 'italic ' : ''}400 ${TYPE[step].size}px ${SERIF}`
}

function tierStep(level: number): TypeStep {
  return (rowsMode ? ROW_TIER_TYPE : TIER_TYPE)[level] ?? 'note'
}

const labelFont = (level: number, italic: boolean): string => font(tierStep(level), italic)

let occupancy = new Uint8Array(0)
let cols = 0
let rows = 0
const widthCache = new Map<string, number>()
/** Which side of its mark each node's text sits on: 1 right, -1 left. */
const sideOf = new Map<number, number>()

function resetOccupancy(width: number, height: number): void {
  cols = Math.ceil(width / CELL) + 1
  rows = Math.ceil(height / CELL) + 1
  if (occupancy.length < cols * rows) occupancy = new Uint8Array(cols * rows)
  else occupancy.fill(0, 0, cols * rows)
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

function measure(ctx: CanvasRenderingContext2D, text: string, font: string): number {
  const key = `${font}|${text}`
  let w = widthCache.get(key)
  if (w === undefined) {
    ctx.font = font
    w = ctx.measureText(text).width
    widthCache.set(key, w)
  }
  return w
}

/** Forgets widths measured with a fallback font before the web font arrived. */
export function clearTextCache(): void {
  widthCache.clear()
  sideOf.clear()
}

/** Draws text and the axis above the GL layer. */
export function drawOverlay(engine: Engine, ctx: CanvasRenderingContext2D, dt: number): void {
  const cam = engine.camera
  const W = cam.width
  const H = cam.height
  const dpr = engine.dpr
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, W, H)
  ctx.textBaseline = 'middle'

  if (engine.mix.weave > 0.02) drawLifeMarks(engine, ctx, W)
  if (engine.mix.hatching < 0.5) drawLooseEnds(engine, ctx, W)
  drawNodeLabels(engine, ctx, dt, W, H)
  drawPleats(engine, ctx)
  drawAxis(engine, ctx, W)
  drawBracket(engine, ctx, W)
  if (engine.view.mode === 'density' && engine.pointer && engine.hovered === null && engine.pointerZone === 'chart') drawDensityProbe(engine, ctx, W)
  drawPen(engine, ctx)
  if (engine.pointerZone === 'ruler' && engine.pointer && !engine.bracket) drawRulerCursor(engine, ctx)
  else if (engine.rulerHint && !engine.bracket && engine.drawU > 1.02 && !(engine.view.mode === 'story' && engine.view.story)) drawRulerHint(engine, ctx)
}

function drawNodeLabels(engine: Engine, ctx: CanvasRenderingContext2D, dt: number, W: number, H: number): void {
  const model = engine.model!
  const cam = engine.camera
  const nodes = model.nodes
  const ys = engine.yNow
  const radius = model.radius
  const byPriority = model.byPriority
  const alphaOf = engine.labelAlpha
  const state = engine.state
  const frame = engine.frameBounds()
  const top = frame.top + 8
  const bottom = frame.bottom - 8
  const densityMode = engine.mix.hatching > 0.5
  const landmarkMode = engine.view.mode === 'landmarks'
  const inReach = engine.view.mode === 'reach'
  const inStory = engine.view.mode === 'story' && engine.view.story !== null
  rowsMode = engine.mix.weave > 0.5 || inStory
  // In rows, the title sits to the left of its mark and the rule runs on to the right.
  const natural = inReach ? -1 : 1
  const rightLimit = W - cam.insets.right + 16
  resetOccupancy(W, H)

  const xs = cam.xScale
  const yScale = cam.yScale
  const cx = cam.centerX
  const cy = cam.centerY
  const wanted = new Set<number>()
  let placed = 0
  const drawU = engine.drawU

  const foldsActive = engine.pleats.length > 0
  const tryPlace = (i: number, must: boolean, allowLeft = true): void => {
    if (wanted.has(i)) return
    const node = nodes[i]!
    const v = engine.nodeVisibility(i)
    if (v < 0.3 && !must) return
    if (!must && state[i * 4 + 1]! > 0.5) return
    if (!must && densityMode && node.level > 0) return
    if (engine.nodeU(i) > drawU) return
    // What is folded away keeps its marks but gives up its words, unless you asked for it.
    if (!must && foldsActive && engine.inPleat(engine.nodeU(i))) return
    const px = (engine.nodeV(i) - cam.cu) * xs + cx
    const py = (ys[i]! - cam.cy) * yScale + cy
    if (px < -40 || px > W + 40 || py < top || py > bottom) return
    const labelF = labelFont(node.level, node.kind === 'science')
    const gap = radius[i]! + LABEL_GAP
    const width = measure(ctx, node.title, labelF)
    const height = TYPE[tierStep(node.level)].size
    const rightX = px + gap
    const leftX = px - gap - width
    const free = (x: number) => !blocked(x - 2, py - height / 2, x + width + 2, py + height / 2)
    // Text keeps the side it was given, then tries the right, then the left.
    const home = natural === -1 ? leftX : rightX
    const away = natural === -1 ? rightX : leftX
    const side = sideOf.get(i) ?? natural
    const options = side === natural ? [home, away] : [away, home]
    const usable = options.filter((x) => x + width < rightLimit && x > 4 && (allowLeft || x === home))
    const x0 = usable.find(free) ?? (must ? (usable[0] ?? leftX) : undefined)
    if (x0 === undefined) return
    sideOf.set(i, x0 === leftX ? -1 : 1)
    occupy(x0 - 2, py - height / 2, x0 + width + 2, py + height / 2)
    wanted.add(i)
    placed++
  }

  if (engine.view.selected !== null) tryPlace(engine.view.selected, true)
  if (engine.hovered !== null) tryPlace(engine.hovered, true)
  for (const i of engine.emphasis.slice(0, 50)) tryPlace(i, false)
  if (inStory) for (const i of engine.view.story!.members) if (engine.state[i * 4]! > 0.5) tryPlace(i, true)
  if (engine.view.searchHits) for (const i of engine.view.searchHits) tryPlace(i, false)

  // Within each level, text already showing goes first so it does not flicker off.
  let start = 0
  let visited = 0
  const n = byPriority.length
  while (start < n && placed < MAX_LABELS && visited < VISIT_BUDGET) {
    const level = nodes[byPriority[start]!]!.level
    let end = start
    while (end < n && nodes[byPriority[end]!]!.level === level) end++
    if (landmarkMode && level > 0) break
    for (let k = start; k < end && placed < MAX_LABELS; k++) {
      const i = byPriority[k]!
      if (alphaOf[i]! > 0.3) tryPlace(i, false)
    }
    // Everything takes its natural place on the right before anything moves to the left,
    // so a label moving aside cannot crowd out one that fitted where it was.
    for (let k = start; k < end && placed < MAX_LABELS && visited < VISIT_BUDGET; k++) {
      visited++
      const i = byPriority[k]!
      if (alphaOf[i]! <= 0.3) tryPlace(i, false, false)
    }
    for (let k = start; k < end && placed < MAX_LABELS; k++) {
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

  ctx.lineJoin = 'round'
  ctx.textAlign = 'left'
  for (let i = 0; i < alphaOf.length; i++) {
    const a = alphaOf[i]!
    if (a <= 0.01) continue
    const node = nodes[i]!
    const px = (engine.nodeV(i) - cam.cu) * xs + cx
    const py = (ys[i]! - cam.cy) * yScale + cy
    if (px < -200 || px > W + 200 || py < top || py > bottom) continue
    const v = Math.max(engine.nodeVisibility(i), i === engine.view.selected || i === engine.hovered ? 1 : 0)
    const faded = state[i * 4 + 1]!
    const alpha = a * Math.min(1, v) * (1 - faded * 0.82)
    if (alpha < 0.02) continue
    const labelF = labelFont(node.level, node.kind === 'science')
    const gap = radius[i]! + LABEL_GAP
    const width = measure(ctx, node.title, labelF)
    const x = sideOf.get(i) === -1 ? px - gap - width : px + gap

    ctx.font = labelF
    ctx.lineWidth = HALO
    ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA * alpha})`
    ctx.strokeText(node.title, x, py)
    const emphasised = state[i * 4 + 2]! > 0.3
    const ink = INK[emphasised ? 'primary' : (TIER_INK[node.level] ?? 'secondary')]
    ctx.fillStyle = `rgba(${ink},${alpha})`
    ctx.fillText(node.title, x, py)
  }

  drawProse(engine, ctx, dt, W, top, bottom, rightLimit, wanted, inStory)
}

const LOOSE_LENGTH = 3 * UNIT
const LOOSE_FAN = 0.5

/**
 * A link whose other end has no date yet cannot be drawn to anywhere, so it is drawn as a short
 * loose thread leaving the mark. It stays one length, because it does not measure anything.
 * Threads to the right lead to later work and threads to the left build on earlier work.
 */
function drawLooseEnds(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const model = engine.model!
  const cam = engine.camera
  const ends = engine.looseEnds
  const frame = engine.frameBounds()
  ctx.lineWidth = LINE.hair
  ctx.lineCap = 'round'
  for (let i = 0; i < model.n; i++) {
    const list = ends[i]
    if (!list || list.length === 0) continue
    const alpha = engine.nodeVisibility(i) * (1 - engine.state[i * 4 + 1]! * 0.85)
    if (alpha < 0.05 || engine.nodeU(i) > engine.drawU) continue
    const x = cam.toX(engine.nodeV(i))
    const y = (engine.yNow[i]! - cam.cy) * cam.yScale + cam.centerY
    if (x < -LOOSE_LENGTH || x > W + LOOSE_LENGTH || y < frame.top || y > frame.bottom) continue
    const r = model.radius[i]!
    const ink = model.ink
    ctx.strokeStyle = `rgba(${ink[i * 3]! * 255},${ink[i * 3 + 1]! * 255},${ink[i * 3 + 2]! * 255},${alpha * 0.85})`
    let outs = 0
    let ins = 0
    for (const end of list) {
      const k = end.out ? outs++ : ins++
      // Fans out above and below the line of the name, so the threads stay clear of its text.
      const step = Math.ceil((k + 1) / 2) * (k % 2 === 0 ? -1 : 1)
      const angle = (end.out ? 0 : Math.PI) + (end.out ? 1 : -1) * step * LOOSE_FAN * 1.4
      const c = Math.cos(angle)
      const n = Math.sin(angle)
      ctx.setLineDash(end.tentative ? [2, 2.5] : [])
      ctx.beginPath()
      ctx.moveTo(x + c * r, y + n * r)
      ctx.quadraticCurveTo(x + c * (r + LOOSE_LENGTH * 0.6), y + n * (r + LOOSE_LENGTH * 0.4), x + c * (r + LOOSE_LENGTH), y + n * (r + LOOSE_LENGTH * 0.9))
      ctx.stroke()
    }
  }
  ctx.setLineDash([])
}

function wrap(ctx: CanvasRenderingContext2D, text: string, font: string, width: number): string[] {
  ctx.font = font
  const words = text.split(/\s+/)
  const lines: string[] = []
  let line = ''
  for (const word of words) {
    const next = line ? `${line} ${word}` : word
    if (line && measure(ctx, next, font) > width) {
      lines.push(line)
      line = word
    } else {
      line = next
    }
  }
  if (line) lines.push(line)
  return lines
}

const firstSentence = (text: string): string => /^.+?[.!?](\s|$)/.exec(text)?.[0].trim() ?? text
const proseAlpha = new Map<number, number>()
const wrapCache = new Map<string, string[]>()
const edgeAlpha = new Map<number, number>()

/**
 * Semantic zoom: as fewer entries share the page, each says more. First a date, then a
 * sentence, then the whole note and what each link claims, so at the deepest zoom the chart
 * can be read as text. It depends on how many entries are in view rather than on a zoom
 * number, so a filtered chart and a dense one both reach it when there is room.
 */
function drawProse(engine: Engine, ctx: CanvasRenderingContext2D, dt: number, W: number, top: number, bottom: number, rightLimit: number, wanted: Set<number>, inStory: boolean): void {
  const model = engine.model!
  const cam = engine.camera
  const nodes = model.nodes
  const state = engine.state
  const left = 0
  let inView = 0
  for (const i of wanted) {
    const px = cam.toX(engine.nodeV(i))
    if (px >= left && px <= W) inView++
  }
  // The density view keeps to its silhouette, and reach rows are too close until zoomed.
  const quiet = engine.mix.hatching > 0.5
  const fade = Math.min(1, dt * 8)
  const wantedProse = new Set<number>()
  const story = engine.view.story
  // Rows set a limit on how much can sit under a title without running into the next row.
  const rowRoom = inStory && story && story.y.length > 1 ? (story.y[1]! - story.y[0]!) * cam.yScale : engine.mix.weave > 0.5 ? (cam.yScale * 0.976) / Math.max(1, model.n - 1) : Infinity

  if (!quiet) {
    const order = [...wanted].sort((a, b) => nodes[a]!.level - nodes[b]!.level || (model.children[b]!.length - model.children[a]!.length))
    for (const i of order) {
      const node = nodes[i]!
      if (inView >= DATES_BELOW && i !== engine.view.selected) continue
      if (rowRoom < 32) continue
      const px = cam.toX(engine.nodeV(i))
      const py = (engine.yNow[i]! - cam.cy) * cam.yScale + cam.centerY
      if (px < -20 || px > W + 20) continue
      const gap = model.radius[i]! + LABEL_GAP
      const titleWidth = measure(ctx, node.title, labelFont(node.level, node.kind === 'science'))
      const onLeft = sideOf.get(i) === -1
      const titleX = onLeft ? px - gap - titleWidth : px + gap
      const titleH = TYPE[tierStep(node.level)].line / 2
      const width = Math.min(PROSE_WIDTH, onLeft ? Math.max(120, px - gap - 8) : Math.max(120, rightLimit - titleX))
      const bodyX = onLeft ? px - gap - width : titleX

      let text = ''
      if (rowRoom > 60) {
        if (inView < PROSE_BELOW && !inStory) text = node.summary + (node.note ? ` ${node.note}` : '')
        else if (inView < SENTENCE_BELOW && !inStory) text = firstSentence(node.summary)
      }

      const dateFont = font('note')
      const key = `${i}|${text.length}|${Math.round(width)}`
      let lines = wrapCache.get(key)
      if (!lines) {
        lines = text ? wrap(ctx, text, font('note'), width) : []
        wrapCache.set(key, lines)
      }
      // Keeps to the room there is: a line less, and if need be only the date.
      const available = Math.max(0, Math.floor((bottom - py - titleH - 16) / PROSE_LINE))
      let count = Math.min(lines.length, available, 12)
      let height = PROSE_LINE + count * PROSE_LINE
      // Starts a full cell below the title, whose own cells would otherwise count as taken.
      const clear = py + titleH + CELL
      while (count > 0 && blocked(bodyX, clear, bodyX + width, py + titleH + height)) {
        count--
        height = PROSE_LINE + count * PROSE_LINE
      }
      const dateWidth = measure(ctx, node.date_label, dateFont)
      const dateFree = !blocked(onLeft ? px - gap - dateWidth : titleX, clear, onLeft ? px - gap : titleX + dateWidth, py + titleH + PROSE_LINE)
      if (!dateFree) continue
      occupy(onLeft ? px - gap - Math.max(dateWidth, count ? width : 0) : titleX, clear, onLeft ? px - gap : titleX + Math.max(dateWidth, count ? width : 0), py + titleH + height)
      wantedProse.add(i)
      const a = (proseAlpha.get(i) ?? 0) + (1 - (proseAlpha.get(i) ?? 0)) * fade
      proseAlpha.set(i, a)
      const alpha = a * (1 - state[i * 4 + 1]! * 0.82)
      if (alpha < 0.02) continue

      ctx.textAlign = onLeft ? 'right' : 'left'
      const anchorX = onLeft ? px - gap : titleX
      ctx.font = dateFont
      ctx.lineWidth = HALO
      ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA * alpha})`
      ctx.strokeText(node.date_label, anchorX, py + titleH + PROSE_LINE / 2)
      ctx.fillStyle = `rgba(${INK.muted},${alpha})`
      ctx.fillText(node.date_label, anchorX, py + titleH + PROSE_LINE / 2)
      for (let k = 0; k < count; k++) {
        const ly = py + titleH + PROSE_LINE / 2 + (k + 1) * PROSE_LINE
        const line = count < lines.length && k === count - 1 ? `${lines[k]!.replace(/[.,;:]?$/, '')}…` : lines[k]!
        ctx.strokeText(line, anchorX, ly)
        ctx.fillStyle = `rgba(${INK.secondary},${alpha})`
        ctx.fillText(line, anchorX, ly)
      }
      ctx.textAlign = 'left'
    }
  }
  for (const i of proseAlpha.keys()) {
    if (wantedProse.has(i)) continue
    const a = proseAlpha.get(i)! * (1 - fade)
    if (a < 0.02) proseAlpha.delete(i)
    else {
      proseAlpha.set(i, a)
      engine.labelsAnimating = true
    }
  }
  for (const [i, a] of proseAlpha) if (wantedProse.has(i) && a < 0.98) engine.labelsAnimating = true

  // What each link claims, written along it, when there is room or it has your attention.
  if (quiet || engine.mix.weave > 0.5) return
  const selected = engine.view.selected
  const fadeEdge = Math.min(1, dt * 8)
  const showing = new Set<number>()
  model.edges.forEach((edge, k) => {
    const near = selected !== null && (edge.source === selected || edge.target === selected)
    const allowed = near || (inView < SENTENCE_BELOW && wanted.has(edge.source) && wanted.has(edge.target))
    if (!allowed || inStory) return
    if (state[edge.source * 4]! < 0.5 || state[edge.target * 4]! < 0.5) return
    const ax = cam.toX(engine.nodeV(edge.source))
    const bx = cam.toX(engine.nodeV(edge.target))
    const ay = (engine.yNow[edge.source]! - cam.cy) * cam.yScale + cam.centerY
    const by = (engine.yNow[edge.target]! - cam.cy) * cam.yScale + cam.centerY
    const mx = (ax + bx) / 2
    const my = (ay + by) / 2
    if (mx < 0 || mx > W || my < top || my > bottom) return
    const long = inView < PROSE_BELOW && edge.link.statement
    const word = edge.link.relation + (edge.tentative ? ' (awaiting review)' : '')
    const edgeFont = font('note')
    const width = measure(ctx, word, edgeFont)
    const body = long ? wrap(ctx, edge.link.statement!, edgeFont, LAYOUT.column).slice(0, 6) : []
    const boxW = Math.max(width, body.length ? LAYOUT.column : 0)
    const boxH = PROSE_LINE + body.length * PROSE_LINE
    // On the middle of the link if there is room, otherwise just to either side of it.
    const x0 = [mx - boxW / 2, mx + 8, mx - boxW - 8].map((x) => Math.max(4, Math.min(W - boxW - 4, x))).find((x) => !blocked(x, my - 7, x + boxW, my - 7 + boxH))
    if (x0 === undefined) return
    occupy(x0, my - 7, x0 + boxW, my - 7 + boxH)
    showing.add(k)
    const a = (edgeAlpha.get(k) ?? 0) + (1 - (edgeAlpha.get(k) ?? 0)) * fadeEdge
    edgeAlpha.set(k, a)
    if (a < 0.98) engine.labelsAnimating = true
    ctx.font = edgeFont
    ctx.lineWidth = HALO
    ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA * a})`
    ctx.fillStyle = `rgba(${INK.muted},${a})`
    ctx.strokeText(word, x0, my)
    ctx.fillText(word, x0, my)
    ctx.fillStyle = `rgba(${INK.secondary},${a})`
    body.forEach((line, n) => {
      ctx.strokeText(line, x0, my + (n + 1) * PROSE_LINE)
      ctx.fillText(line, x0, my + (n + 1) * PROSE_LINE)
    })
  })
  for (const k of edgeAlpha.keys()) if (!showing.has(k)) edgeAlpha.delete(k)
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
    const light = event.type === 'support_end'
    ctx.lineWidth = light ? LINE.rule : LINE.stroke
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
  const reach = engine.reach!
  const frame = engine.frameBounds()
  const alpha = engine.mix.weave
  const rowPx = (cam.yScale * 0.976) / Math.max(1, model.n - 1)
  const showDots = rowPx >= 3.4
  const showQuestion = rowPx >= TYPE.note.size
  const showNames = rowPx >= TYPE.note.line + UNIT
  const markSize = Math.min(1, Math.max(0.55, rowPx / 11))
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  for (let i = 0; i < model.n; i++) {
    const y = (engine.yNow[i]! - cam.cy) * cam.yScale + cam.centerY
    if (y < frame.top || y > frame.bottom) continue
    const state = engine.state[i * 4 + 1]!
    if (engine.state[i * 4]! < 0.5) continue
    const local = alpha * (1 - state * 0.75)
    const record = engine.life.get(i)
    let lastYear = reach.any[i]!
    if (record) {
      for (const event of record.events) {
        if (event.end <= event.start && event.start <= model.nodes[i]!.year && event.role === 'origin') continue
        lastYear = Math.max(lastYear, event.end)
        const x0 = engine.yearToX(event.start)
        const x1 = engine.yearToX(event.end)
        if (x1 < -20 || x0 > W + 20) continue
        ctx.strokeStyle = `rgba(${INK.primary},${local})`
        if (event.role === 'origin') {
          // Dated records that do not bear on its later life are not marked here.
          continue
        }
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
        if (event.bound === 'by' && event.role !== 'use' && markSize > 0.7) {
          ctx.lineWidth = LINE.hair
          ctx.setLineDash([1.5, 2.5])
          ctx.beginPath()
          ctx.moveTo(x1 - 3, y)
          ctx.lineTo(x1 - 16, y)
          ctx.stroke()
          ctx.setLineDash([])
        }
        if (showNames && event.role !== 'use') {
          const name = EVENT_NAMES[event.type] ?? event.type
          ctx.font = font('note')
          ctx.fillStyle = `rgba(${INK.secondary},${local})`
          ctx.textAlign = 'center'
          ctx.fillText(name, x1, y - PROSE_LINE / 2 - UNIT / 2)
          ctx.textAlign = 'left'
        }
      }
    }
    if (!showDots || isFinal(record)) continue
    const span = documentedSpan(record)
    if (span) lastYear = Math.max(lastYear, span.end)
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
  const warpYear = (u: number) => model.time.year(u, engine.warp)
  ctx.font = font('note')
  for (const pleat of pleats) {
    const x0 = cam.toX(engine.foldNow.map(pleat.u0))
    const x1 = cam.toX(engine.foldNow.map(pleat.u1))
    if (x1 - x0 < 12 || x1 < 0 || x0 > cam.width) continue
    const years = Math.abs(warpYear(pleat.u1) - warpYear(pleat.u0))
    if (years < 1) continue
    ctx.save()
    ctx.translate((x0 + x1) / 2, frame.top + UNIT * 2)
    ctx.rotate(Math.PI / 2)
    ctx.textAlign = 'left'
    const label = `${formatSpan(years)} folded`
    ctx.lineWidth = HALO
    ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
    ctx.strokeText(label, 0, 0)
    ctx.fillStyle = `rgba(${INK.muted},1)`
    ctx.fillText(label, 0, 0)
    ctx.restore()
  }
  ctx.textAlign = 'left'
}

/** A figure and what it means, used wherever the chart answers a question in place. */
function drawNotePair(ctx: CanvasRenderingContext2D, line: string, note: string, x: number, y: number): void {
  ctx.lineWidth = HALO
  ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
  ctx.font = font('body')
  ctx.strokeText(line, x, y)
  ctx.fillStyle = `rgba(${INK.primary},1)`
  ctx.fillText(line, x, y)
  ctx.font = font('note')
  ctx.strokeText(note, x, y + TYPE.note.line)
  ctx.fillStyle = `rgba(${INK.secondary},1)`
  ctx.fillText(note, x, y + TYPE.note.line)
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

/** A year set on the ruler over whatever tick is there. */
function drawRulerYear(ctx: CanvasRenderingContext2D, text: string, x: number, lineY: number): void {
  ctx.font = font('note')
  const width = measure(ctx, text, ctx.font)
  ctx.fillStyle = `rgba(${PAPER},1)`
  ctx.fillRect(x - width / 2 - UNIT, lineY - TYPE.note.line - UNIT / 2, width + UNIT * 2, TYPE.note.line)
  ctx.textAlign = 'center'
  ctx.fillStyle = `rgba(${INK.primary},1)`
  ctx.fillText(text, x, lineY - TYPE.note.line / 2 - UNIT / 2)
  ctx.textAlign = 'left'
}

/** While the chart is being drawn, a rule marks where the pen has got to and in what year. */
function drawPen(engine: Engine, ctx: CanvasRenderingContext2D): void {
  const u = engine.drawU
  if (u > 1.02 || u < 0) return
  const clamped = Math.min(1, u)
  const x = engine.camera.toX(engine.toV(clamped))
  const frame = engine.frameBounds()
  const year = engine.model!.time.year(clamped, engine.warp)
  ctx.fillStyle = `rgba(${INK.primary},0.5)`
  ctx.fillRect(x - 0.4, frame.top, 0.8, frame.bottom - frame.top)
  drawRulerYear(ctx, formatYear(year), x, frame.top)
  ctx.textAlign = 'left'
}

/** The one thing nobody would guess, said once, close to where it happens. */
function drawRulerHint(engine: Engine, ctx: CanvasRenderingContext2D): void {
  const frame = engine.frameBounds()
  ctx.font = font('note')
  ctx.textAlign = 'left'
  ctx.lineWidth = HALO
  ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
  const text = 'Drag along this ruler to open a period'
  const x = engine.camera.insets.left
  ctx.strokeText(text, x, frame.top + TYPE.note.line)
  ctx.fillStyle = `rgba(${INK.muted},1)`
  ctx.fillText(text, x, frame.top + TYPE.note.line)
}

/** The exact year under the pointer, and the invitation to open a period. */
function drawRulerCursor(engine: Engine, ctx: CanvasRenderingContext2D): void {
  const pointer = engine.pointer!
  const frame = engine.frameBounds()
  const lineY = frame.top
  const year = engine.xToYear(pointer.x)
  ctx.fillStyle = `rgba(${INK.primary},0.35)`
  ctx.fillRect(pointer.x - 0.4, lineY, 0.8, frame.bottom - lineY)
  drawRulerYear(ctx, formatYear(year), pointer.x, lineY)
  ctx.textAlign = 'left'
  if (engine.view.mode === 'story' && engine.view.story) return
  const pleat = engine.pleatAtX(pointer.x)
  const hint = pleat && engine.openPeriods.length ? 'Click to unfold' : 'Drag along the ruler to open a period'
  ctx.font = font('note')
  const hintWidth = measure(ctx, hint, ctx.font)
  const x = pointer.x + hintWidth + 3 * UNIT > engine.camera.width ? pointer.x - hintWidth - 2 * UNIT : pointer.x + 2 * UNIT
  ctx.lineWidth = HALO
  ctx.strokeStyle = `rgba(${PAPER},${HALO_ALPHA})`
  ctx.strokeText(hint, x, lineY + TYPE.note.line)
  ctx.fillStyle = `rgba(${INK.secondary},1)`
  ctx.fillText(hint, x, lineY + TYPE.note.line)
}

function drawAxis(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const frame = engine.frameBounds()
  const lineY = frame.top

  ctx.fillStyle = `rgba(${INK.primary},${RULE_ALPHA.frame})`
  ctx.fillRect(0, lineY, W, LINE.hair)
  ctx.fillRect(0, frame.bottom, W, LINE.hair)

  ctx.textAlign = 'center'
  ctx.font = font('note')
  for (const tick of engine.ticks) {
    if (tick.x < 2 * UNIT || tick.x > W - 2 * UNIT) continue
    ctx.fillStyle = `rgba(${INK.secondary},1)`
    ctx.fillText(formatYear(tick.year), tick.x, lineY - TYPE.note.line / 2 - UNIT / 2)
    ctx.fillStyle = `rgba(${INK.primary},${RULE_ALPHA.frame})`
    ctx.fillRect(tick.x - LINE.hair / 2, lineY, LINE.hair, UNIT)
  }
  ctx.textAlign = 'left'
}

function drawDensityProbe(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const pointer = engine.pointer!
  const cam = engine.camera
  const model = engine.model!
  const bounds = engine.frameBounds()
  if (pointer.y < bounds.top || pointer.y > bounds.bottom) return

  const reach = 40
  const yearAt = (x: number) => engine.xToYear(x)
  const a = yearAt(pointer.x - reach)
  const b = yearAt(pointer.x + reach)
  let count = 0
  for (let i = 0; i < model.n; i++) {
    const year = model.nodes[i]!.year
    if (year >= a && year <= b && engine.passesFilters(i)) count++
  }

  const { top: y0, bottom: y1 } = engine.frameBounds()
  ctx.fillStyle = `rgba(${INK.primary},${RULE_ALPHA.frame})`
  ctx.fillRect(pointer.x - reach, y0, LINE.hair, y1 - y0)
  ctx.fillRect(pointer.x + reach, y0, LINE.hair, y1 - y0)

  const primary = `${count.toLocaleString('en-US')} ${count === 1 ? 'entry' : 'entries'}`
  const secondary = `${formatYear(a)} to ${formatYear(b)}`
  const right = pointer.x + reach + UNIT
  const flip = right + 2 * LAYOUT.column / 3 > W - cam.insets.right
  ctx.textAlign = flip ? 'right' : 'left'
  drawNotePair(ctx, primary, secondary, flip ? pointer.x - reach - UNIT : right, y0 + TYPE.body.line)
  ctx.textAlign = 'left'
}
