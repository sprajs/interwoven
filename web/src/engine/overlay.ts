import { formatYear } from './time.ts'
import type { Engine } from './Engine.ts'

const SERIF = '"EB Garamond Variable", Georgia, "Times New Roman", serif'
const INK = { primary: '38,33,28', secondary: '78,70,60', muted: '106,97,86' }
const PAPER = '244,239,230'
const CELL = 7
const MAX_LABELS = 140
const VISIT_BUDGET = 9000

/** Serif roman for technology and italic for science, as maps set towns and rivers apart. */
function labelFont(level: number, italic: boolean): string {
  const size = [17, 14.5, 13.5, 12.5][level] ?? 12.5
  const weight = level === 0 ? 500 : 400
  return `${italic ? 'italic ' : ''}${weight} ${size}px ${SERIF}`
}

let occupancy = new Uint8Array(0)
let cols = 0
let rows = 0
const widthCache = new Map<string, number>()

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

  drawNodeLabels(engine, ctx, dt, W, H)
  drawAxis(engine, ctx, W)
  if (engine.view.mode === 'density' && engine.pointer && engine.hovered === null) drawDensityProbe(engine, ctx, W, H)
}

function drawNodeLabels(engine: Engine, ctx: CanvasRenderingContext2D, dt: number, W: number, H: number): void {
  const model = engine.model!
  const cam = engine.camera
  const nodes = model.nodes
  const ys = model.y
  const radius = model.radius
  const byPriority = model.byPriority
  const alphaOf = engine.labelAlpha
  const state = engine.state
  const top = cam.insets.top - 2
  const bottom = H - cam.insets.bottom + 6
  const densityMode = engine.mix.stipple > 0.5
  const landmarkMode = engine.view.mode === 'landmarks'
  const rightLimit = W - cam.insets.right + 16
  resetOccupancy(W, H)

  const xs = cam.xScale
  const yScale = cam.yScale
  const cx = cam.centerX
  const cy = cam.centerY
  const wanted = new Set<number>()
  let placed = 0
  const drawU = engine.drawU

  const tryPlace = (i: number, must: boolean): void => {
    if (wanted.has(i)) return
    const node = nodes[i]!
    const v = engine.nodeVisibility(i)
    if (v < 0.3 && !must) return
    if (!must && state[i * 4 + 1]! > 0.5) return
    if (!must && densityMode && node.level > 1) return
    if (engine.nodeU(i) > drawU) return
    const px = (engine.nodeU(i) - cam.cu) * xs + cx
    const py = (ys[i]! - cam.cy) * yScale + cy
    if (px < -40 || px > W + 40 || py < top || py > bottom) return
    const font = labelFont(node.level, node.kind === 'science')
    const gap = radius[i]! + 5
    const width = measure(ctx, node.title, font)
    const height = (node.level === 0 ? 19 : 15)
    const fitsRight = px + gap + width < rightLimit
    const x0 = fitsRight ? px + gap : px - gap - width
    const x1 = x0 + width
    if (!must && blocked(x0 - 2, py - height / 2, x1 + 2, py + height / 2)) return
    occupy(x0 - 2, py - height / 2, x1 + 2, py + height / 2)
    wanted.add(i)
    placed++
  }

  if (engine.view.selected !== null) tryPlace(engine.view.selected, true)
  if (engine.hovered !== null) tryPlace(engine.hovered, true)
  for (const i of engine.emphasis.slice(0, 50)) tryPlace(i, false)

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
    for (let k = start; k < end && placed < MAX_LABELS && visited < VISIT_BUDGET; k++) {
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

  ctx.lineJoin = 'round'
  ctx.textAlign = 'left'
  for (let i = 0; i < alphaOf.length; i++) {
    const a = alphaOf[i]!
    if (a <= 0.01) continue
    const node = nodes[i]!
    const px = (engine.nodeU(i) - cam.cu) * xs + cx
    const py = (ys[i]! - cam.cy) * yScale + cy
    if (px < -200 || px > W + 200 || py < top - 10 || py > bottom + 10) continue
    const v = Math.max(engine.nodeVisibility(i), i === engine.view.selected || i === engine.hovered ? 1 : 0)
    const faded = state[i * 4 + 1]!
    const alpha = a * Math.min(1, v) * (1 - faded * 0.82)
    if (alpha < 0.02) continue
    const font = labelFont(node.level, node.kind === 'science')
    const gap = radius[i]! + 5
    const width = measure(ctx, node.title, font)
    const fitsRight = px + gap + width < rightLimit
    const x = fitsRight ? px + gap : px - gap - width

    ctx.font = font
    // A little clear paper around the words, as if the lines were drawn around them.
    ctx.lineWidth = 3.5
    ctx.strokeStyle = `rgba(${PAPER},${0.9 * alpha})`
    ctx.strokeText(node.title, x, py)
    const emphasised = state[i * 4 + 2]! > 0.3
    const ink = node.level <= 1 || emphasised ? INK.primary : node.level === 2 ? INK.secondary : INK.muted
    ctx.fillStyle = `rgba(${ink},${alpha})`
    ctx.fillText(node.title, x, py)
  }
}

function drawAxis(engine: Engine, ctx: CanvasRenderingContext2D, W: number): void {
  const cam = engine.camera
  const lineY = cam.insets.top - 16

  ctx.fillStyle = `rgba(${INK.primary},0.55)`
  ctx.fillRect(0, lineY, W, 0.75)

  ctx.textAlign = 'center'
  ctx.font = `400 13px ${SERIF}`
  for (const tick of engine.ticks) {
    if (tick.x < 14 || tick.x > W - 14) continue
    ctx.fillStyle = `rgba(${INK.secondary},1)`
    ctx.fillText(formatYear(tick.year), tick.x, lineY - 11)
    ctx.fillStyle = `rgba(${INK.primary},0.6)`
    ctx.fillRect(tick.x - 0.4, lineY, 0.8, 5)
  }
  ctx.textAlign = 'left'
}

function drawDensityProbe(engine: Engine, ctx: CanvasRenderingContext2D, W: number, H: number): void {
  const pointer = engine.pointer!
  const cam = engine.camera
  const model = engine.model!
  if (pointer.y < cam.insets.top || pointer.y > H - cam.insets.bottom) return

  const reach = 40
  const yearAt = (x: number) => model.time.year(Math.min(1, Math.max(0, cam.fromX(x))), engine.warp)
  const a = yearAt(pointer.x - reach)
  const b = yearAt(pointer.x + reach)
  let count = 0
  for (let i = 0; i < model.n; i++) {
    const year = model.nodes[i]!.year
    if (year >= a && year <= b && engine.passesFilters(i)) count++
  }

  const y0 = cam.insets.top - 16
  const y1 = H - cam.insets.bottom
  ctx.fillStyle = `rgba(${INK.primary},0.55)`
  ctx.fillRect(pointer.x - reach, y0, 0.75, y1 - y0)
  ctx.fillRect(pointer.x + reach, y0, 0.75, y1 - y0)

  const primary = `${count.toLocaleString('en-US')} ${count === 1 ? 'entry' : 'entries'}`
  const secondary = `${formatYear(a)} to ${formatYear(b)}`
  const right = pointer.x + reach + 8
  const flip = right + 150 > W - cam.insets.right
  ctx.textAlign = flip ? 'right' : 'left'
  const textX = flip ? pointer.x - reach - 8 : right
  ctx.lineWidth = 4
  ctx.lineJoin = 'round'
  ctx.strokeStyle = `rgba(${PAPER},0.95)`
  ctx.font = `500 16px ${SERIF}`
  ctx.strokeText(primary, textX, y0 + 18)
  ctx.fillStyle = `rgba(${INK.primary},1)`
  ctx.fillText(primary, textX, y0 + 18)
  ctx.font = `italic 400 13.5px ${SERIF}`
  ctx.strokeText(secondary, textX, y0 + 36)
  ctx.fillStyle = `rgba(${INK.secondary},1)`
  ctx.fillText(secondary, textX, y0 + 36)
  ctx.textAlign = 'left'
}
