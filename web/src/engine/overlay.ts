import { formatYear, pickTicks } from './time.ts'
import type { Engine } from './Engine.ts'

const FONT_FAMILY = '"Geist Variable", ui-sans-serif, system-ui, sans-serif'
const MONO_FAMILY = '"Geist Mono Variable", ui-monospace, monospace'
const LABEL_FONT = [`600 13px ${FONT_FAMILY}`, `500 11.5px ${FONT_FAMILY}`, `450 11px ${FONT_FAMILY}`, `400 10.5px ${FONT_FAMILY}`]
const INK = { primary: '236,241,250', secondary: '170,182,204', muted: '112,124,148' }
const BG = '5,7,13'
const CELL = 8
const MAX_LABELS = 160
const VISIT_BUDGET = 9000

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

function measure(ctx: CanvasRenderingContext2D, text: string, level: number): number {
  const key = `${level}|${text}`
  let w = widthCache.get(key)
  if (w === undefined) {
    ctx.font = LABEL_FONT[level] ?? LABEL_FONT[3]!
    w = ctx.measureText(text).width
    widthCache.set(key, w)
  }
  return w
}

/** Draws text and axes above the GL layer. Returns the number of labels drawn. */
export function drawOverlay(engine: Engine, ctx: CanvasRenderingContext2D, dt: number): number {
  const model = engine.model!
  const cam = engine.camera
  const W = cam.width
  const H = cam.height
  const dpr = engine.dpr
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, W, H)
  ctx.textBaseline = 'middle'

  const yearToX = (year: number) => cam.toX(model.time.u(year, engine.warp))
  const yearAt = (x: number) => model.time.year(Math.min(1, Math.max(0, cam.fromX(x))), engine.warp)
  const compact = W < 700

  const drawn = drawNodeLabels(engine, ctx, dt, W, H)
  drawLaneLabels(engine, ctx, W, H, compact)
  drawAxis(engine, ctx, yearToX, yearAt, W, compact)
  if (engine.view.mode === 'density' && engine.pointer) drawDensityProbe(engine, ctx, yearAt, W, H)
  return drawn
}

function drawNodeLabels(engine: Engine, ctx: CanvasRenderingContext2D, dt: number, W: number, H: number): number {
  const model = engine.model!
  const cam = engine.camera
  const { nodes, y: ys, radius, byPriority, labelAlpha: alphaOf } = {
    nodes: model.nodes,
    y: model.y,
    radius: model.radius,
    byPriority: model.byPriority,
    labelAlpha: engine.labelAlpha,
  }
  const state = engine.state
  const top = cam.insets.top - 6
  const bottom = H - cam.insets.bottom + 22
  const densityMode = engine.mix.contours > 0.5
  // Labels near the right edge flip left instead of running under an open panel.
  const rightLimit = W - cam.insets.right + 28
  // The lane names own the left column.
  const leftLimit = cam.insets.left - 12
  resetOccupancy(W, H)

  const xs = cam.xScale
  const yScale = cam.yScale
  const cx = cam.centerX
  const cy = cam.centerY
  const wanted = new Set<number>()
  let placed = 0

  const tryPlace = (i: number, must: boolean): void => {
    if (wanted.has(i)) return
    const node = nodes[i]!
    const v = engine.nodeVisibility(i)
    if (v < 0.25 && !must) return
    if (!must && state[i * 4 + 1]! > 0.6) return
    if (!must && densityMode && node.level > 1) return
    const px = (engine.nodeU(i) - cam.cu) * xs + cx
    const py = (ys[i]! - cam.cy) * yScale + cy
    if (px < -80 || px > W + 40 || py < top || py > bottom) return
    const r = radius[i]! + (node.level === 0 ? 11 : 5)
    const width = measure(ctx, node.title, node.level) + (node.level === 0 ? 40 : 0)
    const height = node.level === 0 ? 17 : 14
    const fitsRight = px + r + width < rightLimit
    const x0 = fitsRight ? px + r : px - r - width
    const x1 = x0 + width
    if (!must && x0 < leftLimit) return
    if (blocked(x0, py - height / 2, x1, py + height / 2) && !must) return
    occupy(x0, py - height / 2, x1, py + height / 2)
    wanted.add(i)
    placed++
  }

  // Nodes themselves count as occupied, so labels do not cover important marks.
  for (const i of engine.emphasis.slice(0, 40)) tryPlace(i, i === engine.view.selected || i === engine.hovered)
  if (engine.view.selected !== null) tryPlace(engine.view.selected, true)
  if (engine.hovered !== null) tryPlace(engine.hovered, true)

  // Within each level, labels already showing go first so they do not flicker off.
  let start = 0
  let visited = 0
  const n = byPriority.length
  while (start < n && placed < MAX_LABELS && visited < VISIT_BUDGET) {
    const level = nodes[byPriority[start]!]!.level
    let end = start
    while (end < n && nodes[byPriority[end]!]!.level === level) end++
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

  const fade = Math.min(1, dt * 11)
  let animating = false
  for (let i = 0; i < alphaOf.length; i++) {
    const goal = wanted.has(i) ? 1 : 0
    const a = alphaOf[i]!
    if (a === goal) continue
    const next = Math.abs(goal - a) < 0.01 ? goal : a + (goal - a) * fade
    alphaOf[i] = next
    animating = true
  }
  engine.labelsAnimating = animating

  ctx.lineJoin = 'round'
  let count = 0
  for (let i = 0; i < alphaOf.length; i++) {
    const a = alphaOf[i]!
    if (a <= 0.01) continue
    const node = nodes[i]!
    const px = (engine.nodeU(i) - cam.cu) * xs + cx
    const py = (ys[i]! - cam.cy) * yScale + cy
    if (px < -200 || px > W + 200 || py < top - 10 || py > bottom + 10) continue
    const emphasised = state[i * 4 + 2]! > 0.2
    const v = Math.min(1, Math.max(engine.nodeVisibility(i), i === engine.view.selected ? 1 : 0))
    const dim = 1 - state[i * 4 + 1]! * 0.85
    const alpha = a * v * dim
    if (alpha < 0.02) continue
    const r = radius[i]! + (node.level === 0 ? 11 : 5)
    const titleWidth = measure(ctx, node.title, node.level)
    const totalWidth = titleWidth + (node.level === 0 ? 40 : 0)
    const fitsRight = px + r + totalWidth < rightLimit
    const x = fitsRight ? px + r : px - r - totalWidth

    ctx.font = LABEL_FONT[node.level] ?? LABEL_FONT[3]!
    ctx.lineWidth = 3
    ctx.strokeStyle = `rgba(${BG},${0.82 * alpha})`
    ctx.strokeText(node.title, x, py)
    const ink = node.level <= 1 || emphasised ? INK.primary : node.level === 2 ? INK.secondary : INK.muted
    ctx.fillStyle = `rgba(${ink},${alpha})`
    ctx.fillText(node.title, x, py)
    if (node.level === 0) {
      ctx.font = `400 10.5px ${MONO_FAMILY}`
      ctx.fillStyle = `rgba(${INK.secondary},${alpha * 0.85})`
      ctx.fillText(formatYear(node.year), x + titleWidth + 7, py + 0.5)
    }
    count++
  }
  return count
}

function drawLaneLabels(engine: Engine, ctx: CanvasRenderingContext2D, W: number, H: number, compact: boolean): void {
  const model = engine.model!
  const cam = engine.camera
  // The bottom edge fades out behind the legend and overview strip.
  const fadeTop = H - cam.insets.bottom - 6
  const fade = ctx.createLinearGradient(0, fadeTop, 0, H)
  fade.addColorStop(0, `rgba(${BG},0)`)
  fade.addColorStop(0.3, `rgba(${BG},0.86)`)
  fade.addColorStop(1, `rgba(${BG},0.98)`)
  ctx.fillStyle = fade
  ctx.fillRect(0, fadeTop, W, H - fadeTop)

  const fadeWidth = cam.insets.left + 10
  const g = ctx.createLinearGradient(0, 0, fadeWidth, 0)
  g.addColorStop(0, `rgba(${BG},0.94)`)
  g.addColorStop(0.65, `rgba(${BG},0.6)`)
  g.addColorStop(1, `rgba(${BG},0)`)
  ctx.fillStyle = g
  ctx.fillRect(0, 0, fadeWidth, H)

  const top = cam.insets.top
  const bottom = H - cam.insets.bottom
  for (const lane of model.lanes) {
    const y0 = cam.toY(lane.y0)
    const y1 = cam.toY(lane.y1)
    if (y1 < top || y0 > bottom) continue
    const y = Math.min(bottom - 12, Math.max(top + 12, cam.toY(lane.center)))
    const hidden = engine.view.hiddenDomains.has(lane.id)
    const alpha = hidden ? 0.3 : 1
    ctx.fillStyle = lane.color
    ctx.globalAlpha = alpha
    ctx.beginPath()
    ctx.arc(20, y, 3.5, 0, Math.PI * 2)
    ctx.fill()
    ctx.globalAlpha = 1
    if (compact) continue
    ctx.font = `500 12px ${FONT_FAMILY}`
    ctx.fillStyle = `rgba(${INK.primary},${0.86 * alpha})`
    ctx.fillText(lane.label, 32, y)
  }
  void W
}

function drawAxis(
  engine: Engine,
  ctx: CanvasRenderingContext2D,
  yearToX: (year: number) => number,
  yearAt: (x: number) => number,
  W: number,
  compact: boolean,
): void {
  const model = engine.model!
  const cam = engine.camera
  const bandBottom = cam.insets.top - 6
  const g = ctx.createLinearGradient(0, 0, 0, bandBottom + 14)
  g.addColorStop(0, `rgba(${BG},0.97)`)
  g.addColorStop(0.72, `rgba(${BG},0.82)`)
  g.addColorStop(1, `rgba(${BG},0)`)
  ctx.fillStyle = g
  ctx.fillRect(0, 0, W, bandBottom + 14)

  const epochY = bandBottom - 34
  const tickY = bandBottom - 13
  ctx.textAlign = 'center'

  // Epoch names sit in the visible part of their band and hide when they would not fit.
  ctx.font = `500 11px ${FONT_FAMILY}`
  for (const epoch of model.epochs) {
    const x0 = Math.max(cam.insets.left * 0.4, yearToX(epoch.start))
    const x1 = Math.min(W, yearToX(epoch.end))
    if (x1 <= x0) continue
    const text = epoch.label
    if (ctx.measureText(text).width + 14 > x1 - x0) continue
    ctx.fillStyle = `rgba(${INK.secondary},0.92)`
    ctx.fillText(text, (x0 + x1) / 2, epochY)
    const edge = yearToX(epoch.start)
    if (edge > 0 && edge < W) {
      ctx.fillStyle = `rgba(${INK.muted},0.5)`
      ctx.fillRect(edge, epochY - 7, 1, 14)
    }
  }

  const left = compact ? 0 : Math.max(0, cam.insets.left * 0.4)
  const ticks = pickTicks(yearToX, yearAt(left), yearAt(W), W, compact ? 54 : 66)
  ctx.font = `400 10.5px ${MONO_FAMILY}`
  for (const tick of ticks) {
    if (tick.x < left + 12 || tick.x > W - 14) continue
    ctx.fillStyle = `rgba(${INK.muted},1)`
    ctx.fillText(formatYear(tick.year), tick.x, tickY)
    ctx.fillStyle = `rgba(${INK.muted},0.45)`
    ctx.fillRect(tick.x, tickY + 8, 1, 5)
  }
  ctx.textAlign = 'left'
}

function drawDensityProbe(
  engine: Engine,
  ctx: CanvasRenderingContext2D,
  yearAt: (x: number) => number,
  W: number,
  H: number,
): void {
  const pointer = engine.pointer!
  const cam = engine.camera
  const model = engine.model!
  if (pointer.y < cam.insets.top || pointer.y > H - cam.insets.bottom) return

  const reach = 40
  const a = yearAt(pointer.x - reach)
  const b = yearAt(pointer.x + reach)
  let count = 0
  for (let i = 0; i < model.n; i++) {
    const year = model.nodes[i]!.year
    if (year >= a && year <= b && engine.passesFilters(i)) count++
  }

  ctx.fillStyle = 'rgba(236,241,250,0.05)'
  ctx.fillRect(pointer.x - reach, cam.insets.top, reach * 2, H - cam.insets.top - cam.insets.bottom)
  ctx.fillStyle = 'rgba(236,241,250,0.35)'
  ctx.fillRect(pointer.x, cam.insets.top, 1, H - cam.insets.top - cam.insets.bottom)

  const primary = `${count.toLocaleString('en-US')} ${count === 1 ? 'entry' : 'entries'}`
  const secondary = `${formatYear(a)} to ${formatYear(b)}`
  ctx.font = `400 10.5px ${MONO_FAMILY}`
  const sw = ctx.measureText(secondary).width
  ctx.font = `600 12.5px ${FONT_FAMILY}`
  const pw = ctx.measureText(primary).width
  const boxW = Math.max(sw, pw) + 20
  const boxX = pointer.x + boxW + 16 > W ? pointer.x - boxW - 10 : pointer.x + 10
  const boxY = Math.max(cam.insets.top + 4, pointer.y - 24)
  ctx.fillStyle = 'rgba(14,18,30,0.92)'
  ctx.beginPath()
  ctx.roundRect(boxX, boxY, boxW, 44, 9)
  ctx.fill()
  ctx.strokeStyle = 'rgba(160,180,220,0.18)'
  ctx.lineWidth = 1
  ctx.stroke()
  ctx.fillStyle = `rgba(${INK.primary},1)`
  ctx.fillText(primary, boxX + 10, boxY + 15)
  ctx.font = `400 10.5px ${MONO_FAMILY}`
  ctx.fillStyle = `rgba(${INK.secondary},1)`
  ctx.fillText(secondary, boxX + 10, boxY + 31)
}
