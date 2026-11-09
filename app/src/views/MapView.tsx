import { geoEqualEarth, geoGraticule, geoInterpolate, geoPath, type GeoProjection } from 'd3-geo'
import type { FeatureCollection } from 'geojson'
import { useMemo, useRef, useState } from 'react'
import { feature } from 'topojson-client'
import type { GeometryCollection, Topology } from 'topojson-specification'
import land50m from 'world-atlas/land-50m.json'
import type { Entry } from '../data/model.ts'
import type { LinkLayer } from '../data/types.ts'
import { useCanvas, useSize } from '../lib/canvas.ts'
import { useApp, useDimension, useFiltered, useMatches, useModel, useScale } from '../store.ts'
import { alpha, font, INK, INK_2, LAND, LAND_EDGE, NEUTRAL, PAPER, RULE_SOFT } from '../theme.ts'
import './MapView.css'

/** Room left around the globe when it is fitted to the frame. */
const MARGIN = 20
const MAX_ZOOM = 40
/** The golden angle, which spreads a bloom evenly however many dots it holds. */
const GOLDEN = (137.508 * Math.PI) / 180
const TAU = Math.PI * 2
/** Kinds of place that are only known to a country, a region or a sea. */
const VAGUE = new Set(['country', 'region', 'water'])
const ARC_SAMPLES = 24
/** The share of the window, in scale units, in which a discovery counts as just arrived. */
const ARRIVAL = 0.025
/** How near, in pixels, the pointer must be to a dot to pick it. */
const HIT = 7

/**
 * Dot strength by level, where level = dimmed * 4 + ghost * 2 + minor. Minor discoveries are
 * lighter, the past before the window is a faint ghost, and search misses all but vanish.
 */
const STRENGTH = [1, 0.5, 0.22, 0.11, 0.12, 0.12, 0.05, 0.05]
/** Faintest first, so that strong dots sit on top. */
const LEVEL_ORDER = [6, 7, 3, 4, 5, 2, 1, 0]
const LEVELS = STRENGTH.length

/** The land, decoded once: it never changes, and decoding the 50m outline takes a moment. */
let landShape: FeatureCollection | null = null
function land(): FeatureCollection {
  const topology = land50m as unknown as Topology<{ land: GeometryCollection }>
  landShape ??= feature(topology, topology.objects.land)
  return landShape
}

/** [x0, y0, x1, y1] */
type Box = [number, number, number, number]

/** The world fitted to the frame, with its outlines ready to fill. */
interface Basemap {
  projection: GeoProjection
  sphere: Path2D
  graticule: Path2D
  land: Path2D
  /** The globe's extent in projected pixels. */
  box: Box
}

/** The map's own zoom: a scale, and the point of the globe at the frame's centre as a share of its extent. */
interface View {
  k: number
  fx: number
  fy: number
}

/** A view as a canvas transform: screen = t + k * projected. */
interface Transform {
  k: number
  tx: number
  ty: number
}

const HOME: View = { k: 1, fx: 0.5, fy: 0.5 }

/** Discoveries sharing one place, in date order. */
interface Group {
  name: string
  /** The place in projected pixels. */
  x: number
  y: number
  /** Dates of its members, ascending, for counting what is in a window by bisection. */
  ts: Float64Array
}

/**
 * Every discovery with a date and a place, in date order, so that "everything up to t1" is a
 * prefix of the arrays. Positions are worked out once per projection; drawing only scales them.
 */
interface Placed {
  entries: Entry[]
  ts: Float64Array
  /** The place in projected pixels. */
  x: Float32Array
  y: Float32Array
  /** Offset within the place's bloom, in units of the dot spacing. */
  ox: Float32Array
  oy: Float32Array
  vague: Uint8Array
  minor: Uint8Array
  groups: Group[]
  indexOf: Map<string, number>
}

/** A link as a great circle between two places, in projected pixels. */
interface Arc {
  from: string
  to: string
  layer: LinkLayer
  a: number
  b: number
  points: Float32Array
}

/** A cached picture of the land at one size and zoom, so that sweeping through time redraws only the dots. */
interface Backdrop {
  canvas: HTMLCanvasElement
  key: string
  base: Basemap
}

/** Fit the whole globe to the frame and trace its outlines once, since they only change with the frame's size. */
function basemap(width: number, height: number): Basemap {
  const projection = geoEqualEarth().fitExtent(
    [
      [MARGIN, MARGIN],
      [width - MARGIN, height - MARGIN],
    ],
    { type: 'Sphere' },
  )
  const path = geoPath(projection)
  const [[x0, y0], [x1, y1]] = path.bounds({ type: 'Sphere' })
  return {
    projection,
    sphere: new Path2D(path({ type: 'Sphere' }) ?? ''),
    graticule: new Path2D(path(geoGraticule().step([30, 30])()) ?? ''),
    land: new Path2D(path(land()) ?? ''),
    box: [x0, y0, x1, y1],
  }
}

/** Group discoveries by place and give each a seat in its place's sunflower, earliest at the centre. */
function placeEntries(filtered: Entry[], projection: GeoProjection, placeName: (id: string) => string): Placed {
  const entries = filtered.filter((e) => e.t !== undefined && e.at).sort((a, b) => a.t! - b.t!)
  const n = entries.length
  const placed: Placed = {
    entries,
    ts: Float64Array.from(entries, (e) => e.t!),
    x: new Float32Array(n),
    y: new Float32Array(n),
    ox: new Float32Array(n),
    oy: new Float32Array(n),
    vague: Uint8Array.from(entries, (e) => (VAGUE.has(e.at!.kind) ? 1 : 0)),
    minor: Uint8Array.from(entries, (e) => (e.tier > 1 ? 1 : 0)),
    groups: [],
    indexOf: new Map(entries.map((e, i) => [e.id, i])),
  }
  const members = new Map<string, number[]>()
  entries.forEach((e, i) => {
    const list = members.get(e.at!.place)
    if (list) list.push(i)
    else members.set(e.at!.place, [i])
  })
  for (const [place, list] of members) {
    const at = entries[list[0]!]!.at!
    // Equal Earth is defined over the whole sphere, so every place projects.
    const [x, y] = projection([at.lon, at.lat])!
    list.forEach((i, seat) => {
      placed.x[i] = x
      placed.y[i] = y
      placed.ox[i] = Math.sqrt(seat) * Math.cos(seat * GOLDEN)
      placed.oy[i] = Math.sqrt(seat) * Math.sin(seat * GOLDEN)
    })
    placed.groups.push({ name: placeName(place), x, y, ts: Float64Array.from(list, (i) => placed.ts[i]!) })
  }
  return placed
}

/** Each established link between two placed discoveries, traced along the great circle between their places. */
function linkArcs(links: { from: string; to: string; layer: LinkLayer }[], placed: Placed, projection: GeoProjection): Arc[] {
  const arcs: Arc[] = []
  for (const link of links) {
    const a = placed.indexOf.get(link.from)
    const b = placed.indexOf.get(link.to)
    if (a === undefined || b === undefined) continue
    const pa = placed.entries[a]!.at!
    const pb = placed.entries[b]!.at!
    const along = geoInterpolate([pa.lon, pa.lat], [pb.lon, pb.lat])
    const points = new Float32Array(2 * (ARC_SAMPLES + 1))
    for (let j = 0; j <= ARC_SAMPLES; j++) {
      const [x, y] = projection(along(j / ARC_SAMPLES))!
      points[2 * j] = x
      points[2 * j + 1] = y
    }
    arcs.push({ from: link.from, to: link.to, layer: link.layer, a, b, points })
  }
  return arcs
}

/** First index whose date is after t. */
function after(ts: Float64Array, t: number): number {
  let lo = 0
  let hi = ts.length
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (ts[mid]! <= t) lo = mid + 1
    else hi = mid
  }
  return lo
}

/** First index whose date is t or later. */
function from(ts: Float64Array, t: number): number {
  let lo = 0
  let hi = ts.length
  while (lo < hi) {
    const mid = (lo + hi) >> 1
    if (ts[mid]! < t) lo = mid + 1
    else hi = mid
  }
  return lo
}

/** Where the view puts the projected map on the screen. */
function transformOf(view: View, [x0, y0, x1, y1]: Box, width: number, height: number): Transform {
  return { k: view.k, tx: width / 2 - view.k * (x0 + view.fx * (x1 - x0)), ty: height / 2 - view.k * (y0 + view.fy * (y1 - y0)) }
}

/** The view for a transform, kept so that the frame's centre always lies on the globe. */
function viewOf({ k, tx, ty }: Transform, [x0, y0, x1, y1]: Box, width: number, height: number): View {
  const clamp = (v: number) => Math.max(0, Math.min(1, v))
  return { k, fx: clamp(((width / 2 - tx) / k - x0) / (x1 - x0)), fy: clamp(((height / 2 - ty) / k - y0) / (y1 - y0)) }
}

/** Zoom about a point on the screen, keeping that point still. Zooming all the way out goes home. */
function zoomAbout(view: View, factor: number, cx: number, cy: number, box: Box, width: number, height: number): View {
  const k = Math.max(1, Math.min(MAX_ZOOM, view.k * factor))
  if (k === 1) return HOME
  const t = transformOf(view, box, width, height)
  return viewOf({ k, tx: cx - (k * (cx - t.tx)) / t.k, ty: cy - (k * (cy - t.ty)) / t.k }, box, width, height)
}

/** Dot size and the spacing of blooms, in screen pixels. Dots grow a little once the map is close up. */
function dotSize(k: number): { r: number; spacing: number } {
  const r = k > 3 ? 4.5 : 3.5
  return { r, spacing: 2 * r + 1 }
}

/** A count with its noun, in the interface's number style. */
function plural(n: number, one: string, many: string): string {
  return `${n.toLocaleString('en-GB')} ${n === 1 ? one : many}`
}

export function MapView() {
  const model = useModel()
  const scale = useScale()
  const dimension = useDimension()
  const filtered = useFiltered()
  const matches = useMatches()
  const span = useApp((s) => s.window)
  const layers = useApp((s) => s.layers)
  const playing = useApp((s) => s.playing)
  const selected = useApp((s) => s.selected)
  const hoverId = useApp((s) => s.hover?.id ?? null)
  const [frame, size] = useSize<HTMLDivElement>()
  const [view, setView] = useState<View>(HOME)
  const backdrop = useRef<Backdrop | null>(null)
  const linksOn = layers.size > 0

  const base = useMemo(() => (size.width && size.height ? basemap(size.width, size.height) : null), [size])
  const placed = useMemo(
    () => (base ? placeEntries(filtered, base.projection, (id) => model.bundle.places[id]?.name ?? id) : null),
    [filtered, base, model],
  )
  const colors = useMemo(() => {
    if (!placed) return null
    const palette = [...dimension.categories.map((c) => c.color), NEUTRAL]
    const slot = new Map(dimension.categories.map((c, i) => [c.id, i]))
    return { palette, of: Uint8Array.from(placed.entries, (e) => slot.get(dimension.of(e)) ?? palette.length - 1) }
  }, [placed, dimension])
  const us = useMemo(() => (placed ? Float64Array.from(placed.entries, (e) => scale.u(e.t!)) : null), [placed, scale])
  const arcs = useMemo(() => (placed && base && linksOn ? linkArcs(model.links, placed, base.projection) : null), [placed, base, model, linksOn])
  const transform = useMemo(() => (base ? transformOf(view, base.box, size.width, size.height) : null), [base, view, size])

  const canvas = useCanvas(
    size,
    (ctx, { width, height }) => {
      if (!base || !placed || !colors || !us || !transform) return
      const { k, tx, ty } = transform
      const { r, spacing } = dotSize(k)
      const ghostR = r * 0.8
      const [t0, t1] = span
      const end = after(placed.ts, t1)
      const { x, y, ox, oy } = placed
      const sx = (i: number) => tx + k * x[i]! + spacing * ox[i]!
      const sy = (i: number) => ty + k * y[i]! + spacing * oy[i]!
      const focus = hoverId ?? selected

      ctx.drawImage(paintBackdrop(backdrop, base, transform, width, height), 0, 0, width, height)

      // Links, under the dots.
      if (arcs && linksOn) {
        const lit = new Path2D()
        const rest = new Path2D()
        const jump = (base.box[2] - base.box[0]) / 2
        for (const arc of arcs) {
          if (!layers.has(arc.layer) || arc.a >= end || arc.b >= end) continue
          const path = focus !== null && (arc.from === focus || arc.to === focus) ? lit : rest
          const ax = spacing * ox[arc.a]!
          const ay = spacing * oy[arc.a]!
          const bx = spacing * ox[arc.b]!
          const by = spacing * oy[arc.b]!
          const p = arc.points
          for (let j = 0; j <= ARC_SAMPLES; j++) {
            const s = j / ARC_SAMPLES
            const px = tx + k * p[2 * j]! + ax + (bx - ax) * s
            const py = ty + k * p[2 * j + 1]! + ay + (by - ay) * s
            // A great circle that crosses the edge of the map breaks there rather than streaking across it.
            if (j === 0 || Math.abs(p[2 * j]! - p[2 * j - 2]!) > jump) path.moveTo(px, py)
            else path.lineTo(px, py)
          }
        }
        ctx.lineWidth = 1
        ctx.strokeStyle = alpha(INK, focus !== null ? 0.07 : 0.22)
        ctx.stroke(rest)
        ctx.lineWidth = 1.5
        ctx.strokeStyle = alpha(INK, 0.75)
        ctx.stroke(lit)
      }

      // Arrivals: while playing, what has just come into the window lands with a widening halo.
      if (playing) {
        const u0 = scale.u(t0)
        const u1 = scale.u(t1)
        const reach = (u1 - u0) * ARRIVAL
        for (let i = end - 1; i >= 0 && us[i]! >= u1 - reach; i--) {
          if (matches && !matches.has(placed.entries[i]!.id)) continue
          const age = reach > 0 ? (u1 - us[i]!) / reach : 1
          ctx.beginPath()
          ctx.arc(sx(i), sy(i), r + 2 + age * 9, 0, TAU)
          ctx.fillStyle = alpha(colors.palette[colors.of[i]!]!, 0.22 * (1 - age))
          ctx.fill()
        }
      }

      // Dots, gathered into one path per colour, strength and shape so that thousands cost a few fills.
      const buckets: (Path2D | undefined)[] = new Array(colors.palette.length * LEVELS * 2)
      for (let i = 0; i < end; i++) {
        const px = sx(i)
        const py = sy(i)
        if (px < -r || py < -r || px > width + r || py > height + r) continue
        const ghost = placed.ts[i]! < t0
        const dimmed = matches !== null && !matches.has(placed.entries[i]!.id)
        const level = (dimmed ? 4 : 0) + (ghost ? 2 : 0) + placed.minor[i]!
        const ring = placed.vague[i]!
        const key = (colors.of[i]! * LEVELS + level) * 2 + ring
        const path = (buckets[key] ??= new Path2D())
        const radius = (ghost ? ghostR : r) - (ring ? 0.75 : 0)
        path.moveTo(px + radius, py)
        path.arc(px, py, radius, 0, TAU)
      }
      ctx.lineWidth = 1.5
      for (const level of LEVEL_ORDER) {
        const strength = STRENGTH[level]!
        colors.palette.forEach((color, c) => {
          const disc = buckets[(c * LEVELS + level) * 2]
          if (disc) {
            ctx.fillStyle = alpha(color, strength)
            ctx.fill(disc)
          }
          const ring = buckets[(c * LEVELS + level) * 2 + 1]
          if (ring) {
            // A paper centre keeps a ring readable where it sits on land; faint rings stay see-through.
            if (strength >= 0.5) {
              ctx.fillStyle = PAPER
              ctx.fill(ring)
            }
            ctx.strokeStyle = alpha(color, strength)
            ctx.stroke(ring)
          }
        })
      }
      for (const id of [selected, hoverId]) {
        const i = id ? placed.indexOf.get(id) : undefined
        if (i === undefined || i >= end) continue
        ctx.beginPath()
        ctx.arc(sx(i), sy(i), (placed.ts[i]! < t0 ? ghostR : r) + 2.5, 0, TAU)
        ctx.strokeStyle = INK
        ctx.lineWidth = id === selected ? 2 : 1.25
        ctx.stroke()
      }

      // Names of the busiest places, as many as fit without crowding.
      const ranked: { group: Group; count: number }[] = []
      for (const group of placed.groups) {
        const count = after(group.ts, t1) - from(group.ts, t0)
        if (count > 0) ranked.push({ group, count })
      }
      ranked.sort((a, b) => b.count - a.count)
      const limit = Math.round(10 * Math.sqrt(k))
      const taken: Box[] = []
      ctx.font = font(12.5)
      ctx.textBaseline = 'middle'
      ctx.lineJoin = 'round'
      ctx.lineWidth = 3
      ctx.strokeStyle = PAPER
      ctx.fillStyle = INK_2
      for (const { group } of ranked) {
        if (taken.length >= limit) break
        const gx = tx + k * group.x
        const gy = ty + k * group.y
        if (gx < 0 || gy < 0 || gx > width || gy > height) continue
        const bloom = spacing * Math.sqrt(after(group.ts, t1) - 1) + r
        const w = ctx.measureText(group.name).width
        for (const left of [gx + bloom + 4, gx - bloom - 4 - w]) {
          const box: Box = [left - 3, gy - 9, left + w + 3, gy + 9]
          if (box[0] < 4 || box[2] > width - 4 || box[1] < 4 || box[3] > height - 4) continue
          if (taken.some((o) => box[0] < o[2] && box[2] > o[0] && box[1] < o[3] && box[3] > o[1])) continue
          taken.push(box)
          ctx.strokeText(group.name, left, gy)
          ctx.fillText(group.name, left, gy)
          break
        }
      }
    },
    [base, placed, colors, us, arcs, transform, span, matches, layers, linksOn, playing, selected, hoverId, scale],
  )

  /** The drawn dot nearest a point on the page, within reach of the pointer. */
  const dotAt = (clientX: number, clientY: number): { index: number; x: number; y: number } | null => {
    if (!placed || !transform || !frame.current) return null
    const box = frame.current.getBoundingClientRect()
    const px = clientX - box.left
    const py = clientY - box.top
    const { k, tx, ty } = transform
    const { spacing } = dotSize(k)
    const end = after(placed.ts, span[1])
    let best: { index: number; x: number; y: number } | null = null
    let bestDistance = HIT * HIT
    for (let i = 0; i < end; i++) {
      const dx = tx + k * placed.x[i]! + spacing * placed.ox[i]! - px
      const dy = ty + k * placed.y[i]! + spacing * placed.oy[i]! - py
      const d = dx * dx + dy * dy
      if (d < bestDistance) {
        bestDistance = d
        best = { index: i, x: box.left + px + dx, y: box.top + py + dy }
      }
    }
    return best
  }

  const zoomBy = (factor: number, cx = size.width / 2, cy = size.height / 2) => {
    if (!base) return
    setView((v) => zoomAbout(v, factor, cx, cy, base.box, size.width, size.height))
    useApp.getState().setHover(null)
  }

  const drag = useRef<{ x: number; y: number; moved: boolean; view: View } | null>(null)
  const zoomed = view.k > 1 || view.fx !== HOME.fx || view.fy !== HOME.fy
  const inWindow = placed ? after(placed.ts, span[1]) - from(placed.ts, span[0]) : 0
  const before = placed ? from(placed.ts, span[0]) : 0
  const unplaced = placed ? filtered.length - placed.entries.length : 0

  return (
    <>
      <div
        ref={frame}
        className="canvas-frame"
        style={{ cursor: hoverId ? 'pointer' : 'grab' }}
        onPointerDown={(event) => {
          drag.current = { x: event.clientX, y: event.clientY, moved: false, view }
          event.currentTarget.setPointerCapture(event.pointerId)
        }}
        onPointerMove={(event) => {
          const state = useApp.getState()
          const held = drag.current
          if (held && base) {
            const dx = event.clientX - held.x
            const dy = event.clientY - held.y
            if (Math.hypot(dx, dy) > 3) held.moved = true
            if (held.moved) {
              if (state.hover) state.setHover(null)
              const t = transformOf(held.view, base.box, size.width, size.height)
              setView(viewOf({ k: t.k, tx: t.tx + dx, ty: t.ty + dy }, base.box, size.width, size.height))
              return
            }
          }
          const dot = dotAt(event.clientX, event.clientY)
          const id = dot ? placed!.entries[dot.index]!.id : null
          if (id !== (state.hover?.id ?? null)) state.setHover(dot && id ? { id, x: dot.x, y: dot.y - dotSize(view.k).r } : null)
        }}
        onPointerUp={(event) => {
          const held = drag.current
          drag.current = null
          if (held?.moved) return
          const dot = dotAt(event.clientX, event.clientY)
          useApp.getState().select(dot ? placed!.entries[dot.index]!.id : null)
        }}
        onPointerLeave={() => useApp.getState().setHover(null)}
        onDoubleClick={(event) => {
          const box = event.currentTarget.getBoundingClientRect()
          zoomBy(2, event.clientX - box.left, event.clientY - box.top)
        }}
        onWheel={(event) => {
          const box = event.currentTarget.getBoundingClientRect()
          zoomBy(Math.exp(-event.deltaY * 0.0018), event.clientX - box.left, event.clientY - box.top)
        }}
      >
        <canvas ref={canvas} style={{ width: size.width, height: size.height }} />
      </div>
      <div className="zoom-buttons">
        <button aria-label="Zoom in" title="Zoom in" onClick={() => zoomBy(2)}>
          +
        </button>
        <button aria-label="Zoom out" title="Zoom out" onClick={() => zoomBy(0.5)}>
          −
        </button>
        {zoomed && (
          <button aria-label="Show the whole world" title="Show the whole world" onClick={() => setView(HOME)}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.3" aria-hidden="true">
              <circle cx="7" cy="7" r="5.5" />
              <path d="M1.5 7h11M7 1.5c-2 2.8-2 8.2 0 11M7 1.5c2 2.8 2 8.2 0 11" />
            </svg>
          </button>
        )}
      </div>
      <div className="float map-panel">
        <h4>In view</h4>
        <p>{plural(inWindow, 'discovery', 'discoveries')} placed in this stretch of time</p>
        {before > 0 && <p>{plural(before, 'earlier one', 'earlier ones')}, shown faintly</p>}
        {unplaced > 0 && <p>{plural(unplaced, 'more has', 'more have')} no place or date yet, so cannot be shown</p>}
        <div className="map-key">
          <span>
            <i className="map-glyph" />
            site or town
          </span>
          <span>
            <i className="map-glyph vague" />
            country or region only
          </span>
        </div>
      </div>
      <p className="caption">One dot per discovery, at its most precise known place. Coordinates are from memory and not yet checked.</p>
    </>
  )
}

/** The land at the current size and zoom, redrawn only when one of those changes. */
function paintBackdrop(cache: React.RefObject<Backdrop | null>, base: Basemap, { k, tx, ty }: Transform, width: number, height: number): HTMLCanvasElement {
  const ratio = window.devicePixelRatio || 1
  const key = `${width}x${height}@${ratio} ${k} ${tx} ${ty}`
  const held = cache.current
  if (held && held.key === key && held.base === base) return held.canvas
  const canvas = held?.canvas ?? document.createElement('canvas')
  // Setting the size also clears the canvas.
  canvas.width = Math.round(width * ratio)
  canvas.height = Math.round(height * ratio)
  const ctx = canvas.getContext('2d')!
  ctx.setTransform(ratio * k, 0, 0, ratio * k, ratio * tx, ratio * ty)
  // Line widths are in projected pixels, so divide by the zoom to keep hairlines hairlines.
  ctx.lineWidth = 1 / k
  ctx.strokeStyle = alpha(INK, 0.045)
  ctx.stroke(base.graticule)
  ctx.fillStyle = LAND
  ctx.fill(base.land)
  ctx.lineWidth = 0.5 / k
  ctx.strokeStyle = LAND_EDGE
  ctx.stroke(base.land)
  ctx.lineWidth = 1 / k
  ctx.strokeStyle = RULE_SOFT
  ctx.stroke(base.sphere)
  cache.current = { canvas, key, base }
  return canvas
}
