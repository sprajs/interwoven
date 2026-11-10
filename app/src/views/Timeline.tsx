import { useMemo, useRef } from 'react'
import type { Entry } from '../data/model.ts'
import type { Category } from '../dims.ts'
import { roundRect, useCanvas, useSize } from '../lib/canvas.ts'
import { plural } from '../lib/text.ts'
import { useApp, useDimension, useFiltered, useLimits, useMatches, useModel, useScale } from '../store.ts'
import { alpha, font, INK, INK_2, INK_3, NEUTRAL, PAPER, RULE, RULE_SOFT, TINT } from '../theme.ts'
import { makeAxis, panWindow, ticks, zoomWindow, type Axis } from '../time.ts'

const RULER = 30
const PAD_X = 20
const LANE_HEAD = 24
const LANE_FOOT = 10
/** Room kept clear at the bottom for the caption. */
const FOOT = 30
/** The longest leader a name may hang on. */
const LEADER = 30
/** How strongly a minor discovery is drawn, against 1 for a major one. */
const MINOR = 0.6

interface Mark {
  entry: Entry
  x: number
  y: number
  color: string
}

interface Lane {
  category: Category | null
  top: number
  bottom: number
  count: number
}

interface Label {
  mark: Mark
  x: number
  y: number
  width: number
  /** Top of the pile the label hangs over. */
  anchorY: number
}

interface Layout {
  axis: Axis
  cell: number
  size: number
  marks: Mark[]
  byId: Map<string, Mark>
  lanes: Lane[]
  labels: Label[]
}

/**
 * Pile every discovery at its date. A pile is a count that can be checked by eye: each square is
 * one discovery, and squares that would overlap stack upward.
 */
function layout(entries: Entry[], axis: Axis, categories: Category[] | null, of: (e: Entry) => string, colorOf: Map<string, string>, width: number, height: number, measure: (text: string, bold: boolean) => number): Layout {
  const rows = categories ?? [null]
  const inView = entries.filter((e) => e.t! >= axis.t0 && e.t! <= axis.t1)
  const laneOf = (e: Entry) => (categories ? categories.findIndex((c) => c.id === of(e)) : 0)
  const bodyTop = RULER
  const bodyHeight = height - RULER - FOOT

  // Find the largest square at which every pile fits.
  let cell = 4
  let size = 3
  let peaks: number[] = []
  for (const candidate of [18, 16, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3]) {
    const step = candidate + (candidate >= 7 ? 2 : 1)
    const counts = rows.map(() => new Map<number, number>())
    for (const e of inView) {
      const lane = laneOf(e)
      if (lane < 0) continue
      const col = Math.floor((axis.x(e.t!) - axis.x0) / step)
      counts[lane]!.set(col, (counts[lane]!.get(col) ?? 0) + 1)
    }
    peaks = counts.map((m) => Math.max(1, ...m.values()))
    cell = step
    size = candidate
    const needed = peaks.reduce((sum, p) => sum + p * step + LANE_HEAD + LANE_FOOT, 0)
    if (needed <= bodyHeight) break
  }

  // Share out the height: each lane gets what its tallest pile needs, and spare room is split evenly.
  const needs = peaks.map((p) => p * cell + LANE_HEAD + LANE_FOOT)
  const spare = Math.max(0, bodyHeight - needs.reduce((a, b) => a + b, 0)) / rows.length
  const lanes: Lane[] = []
  let y = bodyTop
  rows.forEach((category, i) => {
    const h = needs[i]! + spare
    lanes.push({ category, top: y, bottom: y + h, count: 0 })
    y += h
  })

  // Within a column the major discoveries sit lowest and the minor ones above them, so a pile
  // reads as a dark base with a pale top. With all categories in one pile, each column is grouped
  // by category first, so it reads as a stacked bar.
  const rank = new Map([...colorOf.keys()].map((id, i) => [id, i]))
  const band = (e: Entry) => (categories ? 0 : (rank.get(of(e)) ?? 0))
  const minor = (e: Entry) => (e.tier > 1 ? 1 : 0)
  const ordered = [...inView].sort((a, b) => band(a) - band(b) || minor(a) - minor(b) || a.tier - b.tier || a.t! - b.t!)
  const heights = rows.map(() => new Map<number, number>())
  const marks: Mark[] = []
  for (const e of ordered) {
    const lane = laneOf(e)
    if (lane < 0) continue
    const col = Math.floor((axis.x(e.t!) - axis.x0) / cell)
    const stack = heights[lane]!.get(col) ?? 0
    heights[lane]!.set(col, stack + 1)
    lanes[lane]!.count += 1
    marks.push({ entry: e, x: axis.x0 + col * cell, y: lanes[lane]!.bottom - LANE_FOOT - (stack + 1) * cell, color: colorOf.get(of(e)) ?? INK_3 })
  }

  // Name the landmarks. A name sits directly above its own pile on a short leader, or it is left
  // out: a name that has to travel to find room can no longer be matched to its mark.
  const labels: Label[] = []
  const lineHeight = 17
  const placed: { x0: number; x1: number; y0: number; y1: number }[] = []
  const candidates = marks.filter((m) => m.entry.tier === 0).sort((a, b) => a.entry.t! - b.entry.t!)
  for (const mark of candidates) {
    const lane = laneOf(mark.entry)
    const floor = lanes[lane]!.bottom - LANE_FOOT
    const top = (col: number) => floor - (heights[lane]!.get(col) ?? 0) * cell
    const w = measure(mark.entry.name, true)
    const col = Math.floor((mark.x - axis.x0) / cell)
    const anchorY = top(col)
    for (const left of [mark.x, mark.x + size - w]) {
      if (left < PAD_X || left + w > width - PAD_X) continue
      let skyline = floor
      for (let c = Math.floor((left - 6 - axis.x0) / cell); c <= Math.floor((left + w + 6 - axis.x0) / cell); c++) skyline = Math.min(skyline, top(c))
      const y = skyline - 8 - lineHeight
      const leader = anchorY - (y + lineHeight)
      if (leader > LEADER || y < lanes[lane]!.top + LANE_HEAD + 2) continue
      if (placed.some((p) => left < p.x1 + 14 && left + w > p.x0 - 14 && y < p.y1 + 2 && y + lineHeight > p.y0 - 2)) continue
      placed.push({ x0: left, x1: left + w, y0: y, y1: y + lineHeight })
      labels.push({ mark, x: left, y, width: w, anchorY })
      break
    }
  }
  return { axis, cell, size, marks, byId: new Map(marks.map((m) => [m.entry.id, m])), lanes, labels }
}

export function Timeline() {
  const model = useModel()
  const scale = useScale()
  const limits = useLimits()
  const dimension = useDimension()
  const filtered = useFiltered()
  const matches = useMatches()
  const span = useApp((s) => s.window)
  const lanesOn = useApp((s) => s.lanes)
  const layers = useApp((s) => s.layers)
  const hidden = useApp((s) => s.hidden)
  const selected = useApp((s) => s.selected)
  const hoverId = useApp((s) => s.hover?.id ?? null)
  const [frame, size] = useSize<HTMLDivElement>()
  const measurer = useRef<CanvasRenderingContext2D | null>(null)

  const plan = useMemo(() => {
    if (!size.width || !size.height) return null
    measurer.current ??= document.createElement('canvas').getContext('2d')
    const ctx = measurer.current!
    const measure = (text: string, bold: boolean) => {
      ctx.font = font(13.5, bold ? 600 : 500)
      return ctx.measureText(text).width
    }
    const axis = makeAxis(scale, span[0], span[1], PAD_X, size.width - PAD_X)
    const categories = dimension.categories.filter((c) => !hidden.has(`${dimension.id}:${c.id}`) && filtered.some((e) => dimension.of(e) === c.id))
    const colors = new Map(dimension.categories.map((c) => [c.id, c.color]))
    const dated = filtered.filter((e) => e.t !== undefined)
    return layout(dated, axis, lanesOn ? categories : null, dimension.of, colors, size.width, size.height, measure)
    // The fonts load once; measuring before then only shifts labels slightly.
  }, [size, scale, span, dimension, filtered, lanesOn, hidden])

  const canvas = useCanvas(
    size,
    (ctx, { width, height }) => {
      if (!plan) return
      const { axis, marks, lanes, labels } = plan
      const side = plan.size
      const laneAt = (y: number) => lanes.findIndex((lane) => y >= lane.top && y < lane.bottom)

      // The ruler, with its bands carried down the page so a date can be read anywhere.
      const marksOnRuler = ticks(axis, 84)
      ctx.fillStyle = TINT
      for (let i = 0; i < marksOnRuler.length; i += 2) {
        const x0 = marksOnRuler[i]!.x
        const x1 = marksOnRuler[i + 1]?.x ?? axis.x1
        ctx.fillRect(x0, 0, x1 - x0, height - FOOT)
      }
      ctx.font = font(12.5)
      ctx.textBaseline = 'middle'
      ctx.fillStyle = INK_2
      for (const tick of marksOnRuler) {
        ctx.fillStyle = RULE
        ctx.fillRect(Math.round(tick.x), RULER - 7, 1, 7)
        ctx.fillStyle = INK_2
        const w = ctx.measureText(tick.label).width
        ctx.fillText(tick.label, Math.min(tick.x + 5, width - w - 4), RULER / 2 - 1)
      }
      ctx.fillStyle = RULE
      ctx.fillRect(0, RULER - 0.5, width, 1)

      // Lanes.
      for (const lane of lanes) {
        if (lane.top > RULER) {
          ctx.fillStyle = RULE_SOFT
          ctx.fillRect(0, Math.round(lane.top), width, 1)
        }
        if (!lane.category) continue
        ctx.font = font(11.5, 600)
        ctx.fillStyle = lane.category.color
        ctx.fillRect(PAD_X, lane.top + 11, 8, 8)
        ctx.fillStyle = INK_2
        const name = lane.category.name.toUpperCase()
        ctx.letterSpacing = '0.7px'
        ctx.fillText(name, PAD_X + 14, lane.top + 15.5)
        const w = ctx.measureText(name).width
        ctx.letterSpacing = '0px'
        ctx.font = font(12)
        ctx.fillStyle = INK_3
        ctx.fillText(String(lane.count), PAD_X + 14 + w + 8, lane.top + 15.5)
      }

      // Links, under the marks.
      const focus = hoverId ?? selected
      if (layers.size) {
        ctx.lineWidth = 1
        for (const link of model.links) {
          if (!layers.has(link.layer)) continue
          const a = plan.byId.get(link.from)
          const b = plan.byId.get(link.to)
          if (!a || !b) continue
          const lit = focus !== null && (link.from === focus || link.to === focus)
          if (focus !== null && !lit) continue
          curve(ctx, a.x + side / 2, a.y + side / 2, b.x + side / 2, b.y + side / 2)
          ctx.strokeStyle = alpha(INK, lit ? 0.75 : 0.16)
          ctx.lineWidth = lit ? 1.5 : 1
          ctx.stroke()
        }
        if (focus !== null) {
          // With something in focus, keep the rest of the web faintly in sight.
          ctx.lineWidth = 1
          ctx.strokeStyle = alpha(INK, 0.07)
          for (const link of model.links) {
            if (!layers.has(link.layer) || link.from === focus || link.to === focus) continue
            const a = plan.byId.get(link.from)
            const b = plan.byId.get(link.to)
            if (!a || !b) continue
            curve(ctx, a.x + side / 2, a.y + side / 2, b.x + side / 2, b.y + side / 2)
            ctx.stroke()
          }
        }
      }

      // Marks.
      const linked = new Set<string>()
      if (focus) for (const link of model.linksOf.get(focus) ?? []) if (link.status === 'established') linked.add(link.from).add(link.to)
      const radius = side >= 8 ? 2 : 1
      for (const mark of marks) {
        const { entry } = mark
        const unmatched = matches !== null && !matches.has(entry.id)
        // With links drawn and something in focus, what it is not linked to steps back a little.
        const aside = layers.size > 0 && focus !== null && !linked.has(entry.id) && entry.id !== focus
        roundRect(ctx, mark.x, mark.y, side, side, radius)
        // Paleness means minor and nothing else: what stands aside from a lineage turns grey.
        ctx.fillStyle = unmatched ? alpha(mark.color, 0.13) : aside ? alpha(NEUTRAL, 0.42) : alpha(mark.color, entry.tier <= 1 ? 1 : MINOR)
        ctx.fill()
      }
      for (const id of [selected, hoverId]) {
        const mark = id ? plan.byId.get(id) : undefined
        if (!mark) continue
        roundRect(ctx, mark.x - 2, mark.y - 2, side + 4, side + 4, radius + 2)
        ctx.strokeStyle = INK
        ctx.lineWidth = id === selected ? 2 : 1.25
        ctx.stroke()
      }

      // Names of the landmarks.
      ctx.textBaseline = 'alphabetic'
      const chosen = selected ? plan.byId.get(selected) : undefined
      for (const label of labels) {
        if (matches && !matches.has(label.mark.entry.id)) continue
        // The selected record is always named, so nothing else may sit where its name goes.
        if (chosen && label.mark !== chosen && Math.abs(label.y - (chosen.y - 24)) < 20 && label.x < chosen.x + 260 && label.x + label.width > chosen.x - 260) continue
        if (label.mark === chosen) continue
        const lx = label.mark.x + side / 2
        ctx.strokeStyle = alpha(INK, 0.35)
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(Math.round(lx) + 0.5, label.y + 15)
        ctx.lineTo(Math.round(lx) + 0.5, label.anchorY - 2)
        ctx.stroke()
        ctx.font = font(13.5, 600)
        // A halo of paper keeps the name clear of the leader lines and marks around it.
        ctx.strokeStyle = PAPER
        ctx.lineWidth = 4
        ctx.lineJoin = 'round'
        ctx.strokeText(label.mark.entry.name, label.x, label.y + 12.5)
        const setAside = layers.size > 0 && focus !== null && !linked.has(label.mark.entry.id)
        ctx.fillStyle = setAside ? alpha(INK, 0.4) : INK
        ctx.fillText(label.mark.entry.name, label.x, label.y + 12.5)
      }
      if (chosen) {
        ctx.font = font(13.5, 600)
        const w = ctx.measureText(chosen.entry.name).width
        // It rides above every mark it would cross in its own row, on a leader down to its square.
        // Where that would run into the row's heading, it sits beside its square instead.
        let x = Math.max(PAD_X, Math.min(width - PAD_X - w, chosen.x + side / 2 - w / 2))
        const lane = lanes[laneAt(chosen.y)]
        let top = chosen.y
        for (const mark of marks) if (mark.x + side > x - 4 && mark.x < x + w + 4 && mark.y < top && laneAt(mark.y) === laneAt(chosen.y)) top = mark.y
        let y = top - 10
        if (lane && y - 14 < lane.top + LANE_HEAD) {
          const right = chosen.x + side + 7 + w <= width - PAD_X
          x = right ? chosen.x + side + 7 : chosen.x - 7 - w
          y = chosen.y + side - 1
        } else if (top < chosen.y - 2) {
          ctx.strokeStyle = alpha(INK, 0.45)
          ctx.lineWidth = 1
          ctx.beginPath()
          ctx.moveTo(Math.round(chosen.x + side / 2) + 0.5, y + 4)
          ctx.lineTo(Math.round(chosen.x + side / 2) + 0.5, chosen.y - 3)
          ctx.stroke()
        }
        ctx.strokeStyle = PAPER
        ctx.lineWidth = 5
        ctx.lineJoin = 'round'
        ctx.strokeText(chosen.entry.name, x, y)
        ctx.fillStyle = INK
        ctx.fillText(chosen.entry.name, x, y)
      }
    },
    [plan, matches, selected, hoverId, layers, model],
  )

  const drag = useRef<{ x: number; moved: boolean; span: [number, number] } | null>(null)
  const markAt = (clientX: number, clientY: number): Mark | null => {
    if (!plan || !frame.current) return null
    const box = frame.current.getBoundingClientRect()
    const x = clientX - box.left
    const y = clientY - box.top
    let best: Mark | null = null
    let bestDistance = plan.size / 2 + 4
    for (const mark of plan.marks) {
      const d = Math.max(Math.abs(mark.x + plan.size / 2 - x), Math.abs(mark.y + plan.size / 2 - y))
      if (d < bestDistance) {
        best = mark
        bestDistance = d
      }
    }
    return best
  }

  return (
    <div
      ref={frame}
      className="canvas-frame"
      style={{ cursor: hoverId ? 'pointer' : 'grab' }}
      onPointerDown={(event) => {
        drag.current = { x: event.clientX, moved: false, span }
        event.currentTarget.setPointerCapture(event.pointerId)
      }}
      onPointerMove={(event) => {
        const state = useApp.getState()
        const held = drag.current
        if (held && plan) {
          const dx = event.clientX - held.x
          if (Math.abs(dx) > 3) held.moved = true
          if (held.moved) {
            state.setHover(null)
            state.setWindow(panWindow(scale, held.span, -dx / (plan.axis.x1 - plan.axis.x0), limits))
            return
          }
        }
        const mark = markAt(event.clientX, event.clientY)
        if (mark?.entry.id !== state.hover?.id) {
          const box = frame.current!.getBoundingClientRect()
          state.setHover(mark ? { id: mark.entry.id, x: box.left + mark.x + plan!.size / 2, y: box.top + mark.y } : null)
        }
      }}
      onPointerUp={(event) => {
        const held = drag.current
        drag.current = null
        if (held?.moved) return
        const mark = markAt(event.clientX, event.clientY)
        useApp.getState().select(mark ? mark.entry.id : null)
      }}
      onPointerLeave={() => useApp.getState().setHover(null)}
      onWheel={(event) => {
        if (!plan) return
        const box = event.currentTarget.getBoundingClientRect()
        const state = useApp.getState()
        if (Math.abs(event.deltaX) > Math.abs(event.deltaY)) {
          state.setWindow(panWindow(scale, span, event.deltaX / (plan.axis.x1 - plan.axis.x0), limits))
        } else {
          const about = plan.axis.t(Math.max(plan.axis.x0, Math.min(plan.axis.x1, event.clientX - box.left)))
          state.setWindow(zoomWindow(scale, span, about, Math.exp(event.deltaY * 0.0018), limits))
        }
        state.setHover(null)
      }}
    >
      <canvas ref={canvas} style={{ width: size.width, height: size.height }} />
      <p className="caption">
        {plural(plan?.marks.length ?? 0, 'discovery', 'discoveries')} in view, one square each, at its earliest record. {scale.hint}.
        <span className="caption-key">
          <i />
          <i />
          paler squares are minor
        </span>
      </p>
    </div>
  )
}

/** A link between two marks, leaving and arriving level so that it reads as a flow through time. */
function curve(ctx: CanvasRenderingContext2D, x0: number, y0: number, x1: number, y1: number): void {
  const bend = Math.max(18, Math.abs(x1 - x0) * 0.45)
  ctx.beginPath()
  ctx.moveTo(x0, y0)
  ctx.bezierCurveTo(x0 + bend, y0, x1 - bend, y1, x1, y1)
}
