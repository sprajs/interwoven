import { geoArea, geoEqualEarth, geoGraticule, geoInterpolate, geoPath, type GeoProjection } from 'd3-geo'
import type { FeatureCollection, Position } from 'geojson'
import { useEffect, useMemo, useRef, useState } from 'react'
import { feature } from 'topojson-client'
import type { GeometryCollection, Topology } from 'topojson-specification'
import land50m from 'world-atlas/land-50m.json'
import type { Entry } from '../data/model.ts'
import type { LinkLayer, Place, Region } from '../data/types.ts'
import { useCanvas, useSize } from '../lib/canvas.ts'
import { plural } from '../lib/text.ts'
import { useApp, useDimension, useFiltered, useMatches, useModel, useScale } from '../store.ts'
import { alpha, font, INK, INK_2, LAND, LAND_EDGE, NEUTRAL, PAPER, RULE_SOFT } from '../theme.ts'
import './MapView.css'

/** Room left around the globe when it is fitted to the frame. */
const MARGIN = 20
const MAX_ZOOM = 24
/** Past this zoom the 50m coastline looks blocky, so the 10m one is used. */
const FINE_ZOOM = 3.5
/** From this zoom on, sites and towns are named and only links within the frame are drawn. */
const CLOSE_ZOOM = 2.5
/** Where a click on a crowded place far out flies to. */
const CLUSTER_ZOOM = 5
const FLIGHT_MS = 350
/** The golden angle, which spreads a bloom evenly however many dots it holds. */
const GOLDEN = (137.508 * Math.PI) / 180
const TAU = Math.PI * 2
/** Kinds of place that are only known to a country, a region or a sea. */
const VAGUE = new Set(['country', 'region', 'water'])
/** Kinds of place precise enough to be named once the map is close up. */
const NAMED_CLOSE = new Set(['site', 'settlement'])
const ARC_SAMPLES = 24
/** The share of the window, in scale units, in which a discovery counts as just arrived. */
const ARRIVAL = 0.025
/** How near, in pixels, the pointer must be to a dot or ring to pick it. */
const HIT = 7
/** Far out, a click this near a single dot picks it rather than zooming into its crowd. */
const DOT_HIT = 5
/** Dots and rings for discoveries before the window: small, and grey so that pale colour only ever means minor. */
const GHOST_DOT = 2.5
const GHOST_RING = 3
const GHOST = alpha(INK, 0.28)
const LABEL_GAP = 6
/** Nothing is drawn in this strip at the top, where the app's key line sits over the frame. */
const TOP = 6
/** Links whose ends are this near the frame still count as in view when close up. */
const LINK_SLACK = 40

/** Below this zoom, places known only as a country or region are gathered into one ring per world region. */
const WORLD_ZOOM = 2
/** Where a click on a world region's ring flies to: just close enough for its countries to show. */
const REGION_ZOOM = 2.6
/** Past this zoom every ring is named, not only those holding three or more. */
const ALL_RINGS_ZOOM = 4

/**
 * The world regions' rings, each anchored in open water beside its continent so that it is never
 * mistaken for a place on land. The Americas are named on the left, towards the open Pacific.
 */
const REGIONS: { id: Region; name: string; at: [number, number]; left: boolean }[] = [
  { id: 'europe', name: 'Europe', at: [-18, 56], left: false },
  { id: 'africa', name: 'Africa', at: [-8, -8], left: false },
  { id: 'asia', name: 'Asia', at: [88, 2], left: false },
  { id: 'north_america', name: 'North America', at: [-128, 30], left: true },
  { id: 'south_america', name: 'South America', at: [-88, -22], left: true },
  { id: 'oceania', name: 'Oceania', at: [158, -32], left: false },
]

/** Strength of a dot in the window by level, where level = missed by search * 2 + minor. */
const STRENGTH = [1, 0.62, 0.12, 0.12]
/** Faintest first, so that strong dots sit on top. */
const LEVEL_ORDER = [2, 3, 1, 0]
const LEVELS = STRENGTH.length

type Land = FeatureCollection

/** A polygon wound so that d3's spherical rule reads it as the smaller of the two areas its rings bound. */
function rewind(rings: Position[][]): Position[][] {
  return geoArea({ type: 'Polygon', coordinates: rings }) > TAU ? rings.map((ring) => [...ring].reverse()) : rings
}

/**
 * Decode a world-atlas land file. A few 10m polygons are wound the wrong way for d3, which then
 * reads each as the whole globe less an island and fills the sea as land; they are turned round.
 */
function decode(json: unknown): Land {
  const topology = json as Topology<{ land: GeometryCollection }>
  const land = feature(topology, topology.objects.land)
  for (const f of land.features) {
    const g = f.geometry
    if (g.type === 'MultiPolygon') g.coordinates = g.coordinates.map(rewind)
    else if (g.type === 'Polygon') g.coordinates = rewind(g.coordinates)
  }
  return land
}

/** The 50m land, decoded once: it never changes, and decoding it takes a moment. */
let coarseLand: Land | null = null
function coarse(): Land {
  coarseLand ??= decode(land50m)
  return coarseLand
}

/** The 10m land, fetched only once someone zooms in far enough to need it. */
let fineLand: Promise<Land> | null = null
function fine(): Promise<Land> {
  fineLand ??= import('world-atlas/land-10m.json').then((m) => decode(m.default))
  return fineLand
}

/** A ring grows gently with how many discoveries it holds, and stops before a big country shouts. */
function ringRadius(n: number): number {
  return Math.min(11, 4.5 + 1.8 * Math.sqrt(n))
}

/** A world region's ring, a little larger since it gathers a whole continent. */
function regionRadius(n: number): number {
  return Math.min(16, 6 + 1.6 * Math.sqrt(n))
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
  id: string
  name: string
  kind: string
  /** Known only as a country, region or sea: drawn as one ring rather than a bloom. */
  vague: boolean
  /** The place in projected pixels. */
  x: number
  y: number
  /** Indices into `Placed.entries`, in date order. */
  members: Int32Array
  /** Dates of its members, ascending, for counting what is in a window by bisection. */
  ts: Float64Array
  /** Every place this one lies within, so that a region and a country inside it are not both named. */
  ancestors: ReadonlySet<string>
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
  /** Offset within the place's bloom, in units of the dot spacing. Zero at vague places, which have one ring. */
  ox: Float32Array
  oy: Float32Array
  vague: Uint8Array
  minor: Uint8Array
  /** Index into `groups`. */
  group: Int32Array
  groups: Group[]
  /** Index into `regions` for a discovery at a vague place, and -1 otherwise. */
  regionOf: Int8Array
  regions: RegionRing[]
  indexOf: Map<string, number>
}

/** All the vaguely placed discoveries of one world region, gathered for the world view. */
interface RegionRing {
  name: string
  left: boolean
  /** The ring's anchor in open water, in projected pixels. */
  x: number
  y: number
  /** The mean of the region's vague places, where a click on the ring flies to. */
  landX: number
  landY: number
  members: Int32Array
  ts: Float64Array
}

/**
 * Each place on the screen for one window and view. Drawn counts include the grey dots before
 * the window and live ones do not; rings are nudged apart so that neighbouring regions stay distinct.
 */
interface Layout {
  /** Far out, vague places are not drawn one by one but gathered into their world region's ring. */
  world: boolean
  drawn: Int32Array
  live: Int32Array
  cx: Float32Array
  cy: Float32Array
  /** The radius the place's marks fill: its ring, or the outer edge of its bloom. */
  reach: Float32Array
  /** The same for each world region's ring. */
  regions: { drawn: Int32Array; live: Int32Array; cx: Float32Array; cy: Float32Array; reach: Float32Array }
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
    land: new Path2D(path(coarse()) ?? ''),
    box: [x0, y0, x1, y1],
  }
}

/** Group discoveries by place and give each a seat in its place's sunflower, earliest at the centre. */
function placeEntries(filtered: Entry[], projection: GeoProjection, places: Record<string, Place>): Placed {
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
    group: new Int32Array(n),
    groups: [],
    regionOf: new Int8Array(n).fill(-1),
    regions: [],
    indexOf: new Map(entries.map((e, i) => [e.id, i])),
  }
  const members = new Map<string, number[]>()
  entries.forEach((e, i) => {
    const list = members.get(e.at!.place)
    if (list) list.push(i)
    else members.set(e.at!.place, [i])
  })
  for (const [id, list] of members) {
    const at = entries[list[0]!]!.at!
    const vague = VAGUE.has(at.kind)
    // Equal Earth is defined over the whole sphere, so every place projects.
    const [x, y] = projection([at.lon, at.lat])!
    const g = placed.groups.length
    list.forEach((i, seat) => {
      placed.x[i] = x
      placed.y[i] = y
      placed.group[i] = g
      if (vague) return
      placed.ox[i] = Math.sqrt(seat) * Math.cos(seat * GOLDEN)
      placed.oy[i] = Math.sqrt(seat) * Math.sin(seat * GOLDEN)
    })
    const ancestors = new Set<string>()
    // The bound guards against a loop in the gazetteer.
    for (let up = places[id]?.within; up && ancestors.size < 16 && !ancestors.has(up); up = places[up]?.within) ancestors.add(up)
    placed.groups.push({
      id,
      name: places[id]?.name ?? id,
      kind: at.kind,
      vague,
      x,
      y,
      members: Int32Array.from(list),
      ts: Float64Array.from(list, (i) => placed.ts[i]!),
      ancestors,
    })
  }
  REGIONS.forEach((region, r) => {
    const members: number[] = []
    entries.forEach((e, i) => {
      if (!placed.vague[i] || e.at!.region !== region.id) return
      placed.regionOf[i] = r
      members.push(i)
    })
    const places = placed.groups.filter((g) => g.vague && entries[g.members[0]!]!.at!.region === region.id)
    const [x, y] = projection(region.at)!
    placed.regions.push({
      name: region.name,
      left: region.left,
      x,
      y,
      landX: places.length ? places.reduce((sum, g) => sum + g.x, 0) / places.length : x,
      landY: places.length ? places.reduce((sum, g) => sum + g.y, 0) / places.length : y,
      members: Int32Array.from(members),
      ts: Float64Array.from(members, (i) => placed.ts[i]!),
    })
  })
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

/** Dot size and the spacing of blooms, in screen pixels. Dots grow a little once the map is close up. */
function dotSize(k: number): { r: number; spacing: number } {
  const r = k > 3 ? 4.5 : 3.5
  return { r, spacing: 2 * r + 1 }
}

function layoutFrame(placed: Placed, [t0, t1]: [number, number], { k, tx, ty }: Transform): Layout {
  const { groups } = placed
  const n = groups.length
  const m = placed.regions.length
  const out: Layout = {
    world: k < WORLD_ZOOM,
    drawn: new Int32Array(n),
    live: new Int32Array(n),
    cx: new Float32Array(n),
    cy: new Float32Array(n),
    reach: new Float32Array(n),
    regions: { drawn: new Int32Array(m), live: new Int32Array(m), cx: new Float32Array(m), cy: new Float32Array(m), reach: new Float32Array(m) },
  }
  placed.regions.forEach((region, i) => {
    const drawn = after(region.ts, t1)
    const live = drawn - from(region.ts, t0)
    out.regions.drawn[i] = drawn
    out.regions.live[i] = live
    out.regions.cx[i] = tx + k * region.x
    out.regions.cy[i] = ty + k * region.y
    out.regions.reach[i] = live ? regionRadius(live) : drawn ? GHOST_RING : 0
  })
  const { r, spacing } = dotSize(k)
  const rings: number[] = []
  groups.forEach((g, i) => {
    const drawn = after(g.ts, t1)
    const live = drawn - from(g.ts, t0)
    out.drawn[i] = drawn
    out.live[i] = live
    out.cx[i] = tx + k * g.x
    out.cy[i] = ty + k * g.y
    if (!drawn) return
    if (!g.vague) out.reach[i] = spacing * Math.sqrt(drawn - 1) + r
    else if (!out.world) {
      out.reach[i] = live ? ringRadius(live) : GHOST_RING
      rings.push(i)
    }
  })
  // Rings that would overlap are moved apart, the smaller outward from the larger until they just touch.
  rings.sort((a, b) => out.reach[b]! - out.reach[a]! || a - b)
  rings.forEach((j, rank) => {
    for (let m = 0; m < rank; m++) {
      const i = rings[m]!
      const need = out.reach[i]! + out.reach[j]!
      const dx = out.cx[j]! - out.cx[i]!
      const dy = out.cy[j]! - out.cy[i]!
      const d = Math.hypot(dx, dy)
      if (d >= need) continue
      const ux = d > 0.01 ? dx / d : 1
      const uy = d > 0.01 ? dy / d : 0
      out.cx[j] = out.cx[i]! + ux * need
      out.cy[j] = out.cy[i]! + uy * need
    }
  })
  return out
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

/** Whether a circle and a box overlap. */
function touches([x0, y0, x1, y1]: Box, cx: number, cy: number, radius: number): boolean {
  const dx = cx - Math.max(x0, Math.min(x1, cx))
  const dy = cy - Math.max(y0, Math.min(y1, cy))
  return dx * dx + dy * dy < radius * radius
}

/** A mark under the pointer: the discovery it stands for, and the top of the mark in viewport pixels. */
interface Picked {
  index: number
  x: number
  y: number
  /** Distance from the pointer to the mark, zero inside a ring. */
  distance: number
  /** An individual dot, rather than a ring standing for several. */
  dot: boolean
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
  const [detail, setDetail] = useState<Land | null>(null)
  const backdrop = useRef<Backdrop | null>(null)
  const flight = useRef(0)
  const linksOn = layers.size > 0
  const wantsDetail = view.k > FINE_ZOOM

  useEffect(() => {
    if (!wantsDetail || detail) return
    // Until the fine coastline arrives, or if it cannot be fetched, the 50m one serves.
    fine().then(setDetail, () => undefined)
  }, [wantsDetail, detail])
  useEffect(() => () => cancelAnimationFrame(flight.current), [])

  const base = useMemo(() => (size.width && size.height ? basemap(size.width, size.height) : null), [size])
  // The 10m outline is costly to trace, so it is traced only when it will be drawn.
  const fineLandPath = useMemo(
    () => (base && detail && wantsDetail ? new Path2D(geoPath(base.projection)(detail) ?? '') : null),
    [base, detail, wantsDetail],
  )
  const placed = useMemo(() => (base ? placeEntries(filtered, base.projection, model.bundle.places) : null), [filtered, base, model])
  const colors = useMemo(() => {
    if (!placed) return null
    const palette = [...dimension.categories.map((c) => c.color), NEUTRAL]
    const slot = new Map(dimension.categories.map((c, i) => [c.id, i]))
    return { palette, of: Uint8Array.from(placed.entries, (e) => slot.get(dimension.of(e)) ?? palette.length - 1) }
  }, [placed, dimension])
  const us = useMemo(() => (placed ? Float64Array.from(placed.entries, (e) => scale.u(e.t!)) : null), [placed, scale])
  const arcs = useMemo(() => (placed && base && linksOn ? linkArcs(model.links, placed, base.projection) : null), [placed, base, model, linksOn])
  const transform = useMemo(() => (base ? transformOf(view, base.box, size.width, size.height) : null), [base, view, size])
  const layout = useMemo(() => (placed && transform ? layoutFrame(placed, span, transform) : null), [placed, span, transform])

  const canvas = useCanvas(
    size,
    (ctx, { width, height }) => {
      if (!base || !placed || !colors || !us || !transform || !layout) return
      const { k, tx, ty } = transform
      const { r, spacing } = dotSize(k)
      const [t0, t1] = span
      const end = after(placed.ts, t1)
      const { x, y, ox, oy, groups } = placed
      const { cx, cy, reach, drawn, live } = layout
      const vague = placed.vague
      const gOf = placed.group
      const { world, regions } = layout
      // A discovery at a vague place sits at its ring's centre: its world region's far out, or its own,
      // which may have been nudged off the place, close up.
      const inRegion = (i: number) => world && placed.regionOf[i]! >= 0
      const ringX = (i: number) => (inRegion(i) ? regions.cx[placed.regionOf[i]!]! : cx[gOf[i]!]!)
      const ringY = (i: number) => (inRegion(i) ? regions.cy[placed.regionOf[i]!]! : cy[gOf[i]!]!)
      const ringR = (i: number) => (inRegion(i) ? regions.reach[placed.regionOf[i]!]! : reach[gOf[i]!]!)
      const sx = (i: number) => (vague[i] ? ringX(i) : tx + k * x[i]! + spacing * ox[i]!)
      const sy = (i: number) => (vague[i] ? ringY(i) : ty + k * y[i]! + spacing * oy[i]!)
      const missed = (i: number) => matches !== null && !matches.has(placed.entries[i]!.id)
      const focus = hoverId ?? selected
      const close = k >= CLOSE_ZOOM

      ctx.drawImage(paintBackdrop(backdrop, base, fineLandPath, transform, width, height), 0, 0, width, height)
      ctx.save()
      ctx.beginPath()
      ctx.rect(0, TOP, width, height - TOP)
      ctx.clip()

      // Links, under the marks. Close up, only links with both ends in sight are drawn, unless they are the focus's.
      if (arcs && linksOn) {
        const lit = new Path2D()
        const rest = new Path2D()
        const jump = (base.box[2] - base.box[0]) / 2
        const inSight = (px: number, py: number) => px > -LINK_SLACK && py > -LINK_SLACK && px < width + LINK_SLACK && py < height + LINK_SLACK
        for (const arc of arcs) {
          if (!layers.has(arc.layer) || arc.a >= end || arc.b >= end) continue
          const isLit = focus !== null && (arc.from === focus || arc.to === focus)
          const p = arc.points
          const ax = sx(arc.a) - (tx + k * p[0]!)
          const ay = sy(arc.a) - (ty + k * p[1]!)
          const bx = sx(arc.b) - (tx + k * p[2 * ARC_SAMPLES]!)
          const by = sy(arc.b) - (ty + k * p[2 * ARC_SAMPLES + 1]!)
          if (close && !isLit && !(inSight(sx(arc.a), sy(arc.a)) && inSight(sx(arc.b), sy(arc.b)))) continue
          const path = isLit ? lit : rest
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
        ctx.strokeStyle = alpha(INK, focus !== null ? 0.07 : close ? 0.22 : 0.15)
        ctx.stroke(rest)
        ctx.lineWidth = 1.5
        ctx.strokeStyle = alpha(INK, 0.75)
        ctx.stroke(lit)
      }

      // Arrivals: while playing, what has just come into the window lands with a widening halo.
      if (playing) {
        const u0 = scale.u(t0)
        const u1 = scale.u(t1)
        const recent = (u1 - u0) * ARRIVAL
        for (let i = end - 1; i >= 0 && us[i]! >= u1 - recent; i--) {
          if (missed(i)) continue
          const age = recent > 0 ? (u1 - us[i]!) / recent : 1
          const markR = vague[i] ? ringR(i) : r
          ctx.beginPath()
          ctx.arc(sx(i), sy(i), markR + 2 + age * 9, 0, TAU)
          ctx.fillStyle = alpha(colors.palette[colors.of[i]!]!, 0.22 * (1 - age))
          ctx.fill()
        }
      }

      // Dots at precise places: grey before the window, coloured within it, one path per colour and strength.
      const ghosts = new Path2D()
      const buckets: (Path2D | undefined)[] = new Array(colors.palette.length * LEVELS)
      for (let i = 0; i < end; i++) {
        if (vague[i]) continue
        const px = sx(i)
        const py = sy(i)
        if (px < -r || py < -r || px > width + r || py > height + r) continue
        if (placed.ts[i]! < t0) {
          ghosts.moveTo(px + GHOST_DOT, py)
          ghosts.arc(px, py, GHOST_DOT, 0, TAU)
          continue
        }
        const level = (missed(i) ? 2 : 0) + placed.minor[i]!
        const path = (buckets[colors.of[i]! * LEVELS + level] ??= new Path2D())
        path.moveTo(px + r, py)
        path.arc(px, py, r, 0, TAU)
      }
      ctx.fillStyle = GHOST
      ctx.fill(ghosts)
      for (const level of LEVEL_ORDER) {
        colors.palette.forEach((color, c) => {
          const path = buckets[c * LEVELS + level]
          if (!path) return
          ctx.fillStyle = alpha(color, STRENGTH[level]!)
          ctx.fill(path)
        })
      }

      // One ring per vaguely known place, or far out per world region: a small donut of its
      // categories with its count inside. A sea's ring is dashed.
      const tally = new Int32Array(colors.palette.length)
      ctx.font = font(10.5, 600)
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      const ring = (gx: number, gy: number, radius: number, members: Int32Array, ts: Float64Array, n: number, dashed: boolean) => {
        if (gx < -radius || gy < -radius || gx > width + radius || gy > height + radius) return
        ctx.setLineDash(dashed ? [2, 2] : [])
        if (!n) {
          ctx.beginPath()
          ctx.arc(gx, gy, radius, 0, TAU)
          ctx.lineWidth = 1.5
          ctx.strokeStyle = GHOST
          ctx.stroke()
          return
        }
        const first = from(ts, t0)
        let hit = matches === null
        tally.fill(0)
        for (let m = first; m < first + n; m++) {
          const i = members[m]!
          tally[colors.of[i]!]! += 1
          hit ||= !missed(i)
        }
        ctx.beginPath()
        ctx.arc(gx, gy, radius, 0, TAU)
        ctx.fillStyle = alpha(PAPER, 0.85)
        ctx.fill()
        ctx.lineWidth = 2
        let angle = -Math.PI / 2
        tally.forEach((count, c) => {
          if (!count) return
          const sweep = (TAU * count) / n
          ctx.beginPath()
          ctx.arc(gx, gy, radius, angle, angle + sweep)
          ctx.strokeStyle = alpha(colors.palette[c]!, hit ? 1 : 0.12)
          ctx.stroke()
          angle += sweep
        })
        if (n >= 2) {
          ctx.fillStyle = alpha(INK, hit ? 1 : 0.3)
          ctx.fillText(String(n), gx, gy + 0.5)
        }
      }
      if (world) {
        placed.regions.forEach((region, i) => {
          if (regions.drawn[i]) ring(regions.cx[i]!, regions.cy[i]!, regions.reach[i]!, region.members, region.ts, regions.live[i]!, false)
        })
      } else {
        groups.forEach((group, g) => {
          if (group.vague && drawn[g]) ring(cx[g]!, cy[g]!, reach[g]!, group.members, group.ts, live[g]!, group.kind === 'water')
        })
      }
      ctx.setLineDash([])
      ctx.textAlign = 'left'

      for (const id of [selected, hoverId]) {
        const i = id ? placed.indexOf.get(id) : undefined
        if (i === undefined || i >= end) continue
        ctx.beginPath()
        const radius = vague[i] ? ringR(i) : placed.ts[i]! < t0 ? GHOST_DOT : r
        ctx.arc(sx(i), sy(i), radius + 2.5, 0, TAU)
        ctx.strokeStyle = INK
        ctx.lineWidth = id === selected ? 2 : 1.25
        ctx.stroke()
      }

      // Place names, each beside its own mark. Far out only the world regions' rings are named. Closer,
      // rings holding three or more are named first (every ring past ALL_RINGS_ZOOM), then, close up,
      // sites and towns while there is room. Only places with something in the window are named, and
      // ranking by everything drawn, grey dots included, keeps the names steady while time sweeps.
      const marks: number[] = []
      const circles: { x: number; y: number; r: number }[] = []
      const onScreen = (px: number, py: number, pr: number) => px + pr > 0 && py + pr > TOP && px - pr < width && py - pr < height
      groups.forEach((group, g) => {
        if (!drawn[g] || (world && group.vague) || !onScreen(cx[g]!, cy[g]!, reach[g]!)) return
        marks.push(g)
        circles.push({ x: cx[g]!, y: cy[g]!, r: reach[g]! })
      })
      if (world) {
        regions.drawn.forEach((n, i) => {
          if (n) circles.push({ x: regions.cx[i]!, y: regions.cy[i]!, r: regions.reach[i]! })
        })
      }
      const taken: Box[] = []
      ctx.font = font(12.5)
      ctx.textBaseline = 'middle'
      ctx.lineJoin = 'round'
      ctx.lineWidth = 3
      ctx.strokeStyle = PAPER
      ctx.fillStyle = INK_2
      /** Name a mark on the first free side, never touching another name; with `strict` off, other marks may be overlapped. */
      const label = (text: string, gx: number, gy: number, edge: number, leftFirst: boolean, strict: boolean): boolean => {
        const w = ctx.measureText(text).width
        const right: [number, number] = [gx + edge + LABEL_GAP, gy]
        const left: [number, number] = [gx - edge - LABEL_GAP - w, gy]
        const spots = [leftFirst ? left : right, leftFirst ? right : left, [gx - w / 2, gy - edge - LABEL_GAP - 9] as [number, number]]
        for (const [x0, middle] of spots) {
          const box: Box = [x0 - 3, middle - 9, x0 + w + 3, middle + 9]
          if (box[0] < 4 || box[2] > width - 4 || box[1] < TOP || box[3] > height - 4) continue
          if (taken.some((o) => box[0] < o[2] && box[2] > o[0] && box[1] < o[3] && box[3] > o[1])) continue
          if (strict && circles.some((c) => (c.x !== gx || c.y !== gy) && touches(box, c.x, c.y, c.r))) continue
          taken.push(box)
          ctx.strokeText(text, x0, middle)
          ctx.fillText(text, x0, middle)
          return true
        }
        return false
      }
      if (world) {
        placed.regions.forEach((region, i) => {
          const n = regions.live[i]!
          if (!n) return
          const args = [`${region.name} · ${n.toLocaleString('en-GB')} known only by country`, regions.cx[i]!, regions.cy[i]!, regions.reach[i]!, region.left] as const
          if (!label(...args, true)) label(...args, false)
        })
      } else {
        const byWeight = (a: number, b: number) => drawn[b]! - drawn[a]! || a - b
        const named = marks.filter((g) => live[g])
        const namedRings: Group[] = []
        const ringNamed = (g: number) => live[g]! >= 3 || k >= ALL_RINGS_ZOOM || groups[g]!.kind === 'water'
        for (const g of named.filter((g) => groups[g]!.vague && ringNamed(g)).sort(byWeight)) {
          const group = groups[g]!
          if (namedRings.some((o) => o.ancestors.has(group.id) || group.ancestors.has(o.id))) continue
          if (label(group.name, cx[g]!, cy[g]!, reach[g]!, false, true) || label(group.name, cx[g]!, cy[g]!, reach[g]!, false, false)) namedRings.push(group)
        }
        if (close) {
          let room = Math.round(10 * Math.sqrt(k))
          for (const g of named.filter((g) => NAMED_CLOSE.has(groups[g]!.kind)).sort(byWeight)) {
            if (room <= 0) break
            if (label(groups[g]!.name, cx[g]!, cy[g]!, reach[g]!, false, true)) room -= 1
          }
        }
      }
      ctx.restore()
    },
    [base, fineLandPath, placed, colors, us, arcs, transform, layout, span, matches, layers, linksOn, playing, selected, hoverId, scale],
  )

  /** The drawn mark nearest a point on the page, within reach of the pointer. A ring stands for its earliest discovery in the window. */
  const markAt = (clientX: number, clientY: number): Picked | null => {
    if (!placed || !transform || !layout || !frame.current) return null
    const box = frame.current.getBoundingClientRect()
    const px = clientX - box.left
    const py = clientY - box.top
    const { k, tx, ty } = transform
    const { r, spacing } = dotSize(k)
    const end = after(placed.ts, span[1])
    let best: Picked | null = null
    for (let i = 0; i < end; i++) {
      if (placed.vague[i]) continue
      const cx = tx + k * placed.x[i]! + spacing * placed.ox[i]!
      const cy = ty + k * placed.y[i]! + spacing * placed.oy[i]!
      const d = Math.hypot(cx - px, cy - py)
      if (d < (best?.distance ?? HIT)) best = { index: i, x: box.left + cx, y: box.top + cy - r, distance: d, dot: true }
    }
    placed.groups.forEach((group, g) => {
      if (!group.vague || !layout.drawn[g] || layout.world) return
      const cx = layout.cx[g]!
      const cy = layout.cy[g]!
      const d = Math.max(0, Math.hypot(cx - px, cy - py) - layout.reach[g]!)
      if (d >= (best?.distance ?? HIT)) return
      const earliest = layout.live[g] ? from(group.ts, span[0]) : 0
      best = { index: group.members[earliest]!, x: box.left + cx, y: box.top + cy - layout.reach[g]!, distance: d, dot: false }
    })
    return best
  }

  /**
   * Where to fly for a crowd under the pointer: a world region's ring flies to its continent, and a
   * counted ring or a bloom of six or more dots to a close view centred on it.
   */
  const crowdAt = (clientX: number, clientY: number): View | null => {
    if (!placed || !layout || !base || !frame.current) return null
    const box = frame.current.getBoundingClientRect()
    const px = clientX - box.left
    const py = clientY - box.top
    const [x0, y0, x1, y1] = base.box
    const toward = (k: number, x: number, y: number): View => ({ k, fx: (x - x0) / (x1 - x0), fy: (y - y0) / (y1 - y0) })
    let best: View | null = null
    let bestDistance = Infinity
    const consider = (cx: number, cy: number, reach: number, target: () => View) => {
      const d = Math.hypot(cx - px, cy - py)
      if (d > reach + 3 || d >= bestDistance) return
      best = target()
      bestDistance = d
    }
    if (layout.world) {
      placed.regions.forEach((region, i) => {
        if (layout.regions.drawn[i]) consider(layout.regions.cx[i]!, layout.regions.cy[i]!, layout.regions.reach[i]!, () => toward(REGION_ZOOM, region.landX, region.landY))
      })
    }
    placed.groups.forEach((group, g) => {
      if (group.vague ? layout.world || layout.live[g]! < 2 : layout.drawn[g]! < 6) return
      consider(layout.cx[g]!, layout.cy[g]!, layout.reach[g]!, () => toward(CLUSTER_ZOOM, group.x, group.y))
    })
    return best
  }

  /** Ease the view to a target, so that the eye can follow where it went. */
  const flyTo = (target: View) => {
    cancelAnimationFrame(flight.current)
    const start = view
    const begun = performance.now()
    const step = (now: number) => {
      const s = Math.min(1, (now - begun) / FLIGHT_MS)
      const e = 1 - (1 - s) ** 3
      setView({ k: start.k + (target.k - start.k) * e, fx: start.fx + (target.fx - start.fx) * e, fy: start.fy + (target.fy - start.fy) * e })
      if (s < 1) flight.current = requestAnimationFrame(step)
    }
    flight.current = requestAnimationFrame(step)
    useApp.getState().setHover(null)
  }

  const zoomBy = (factor: number, cx = size.width / 2, cy = size.height / 2) => {
    if (!base) return
    cancelAnimationFrame(flight.current)
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
          cancelAnimationFrame(flight.current)
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
          const mark = markAt(event.clientX, event.clientY)
          const id = mark ? placed!.entries[mark.index]!.id : null
          if (id !== (state.hover?.id ?? null)) state.setHover(mark && id ? { id, x: mark.x, y: mark.y } : null)
        }}
        onPointerUp={(event) => {
          const held = drag.current
          drag.current = null
          if (held?.moved) return
          const mark = markAt(event.clientX, event.clientY)
          // Far out, a click on a crowd flies in to it; a click right on one dot still picks that dot.
          if (view.k < CLOSE_ZOOM && !(mark?.dot && mark.distance <= DOT_HIT)) {
            const crowd = crowdAt(event.clientX, event.clientY)
            if (crowd) {
              flyTo(crowd)
              return
            }
          }
          useApp.getState().select(mark ? placed!.entries[mark.index]!.id : null)
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
          <button aria-label="Show the whole world" title="Show the whole world" onClick={() => flyTo(HOME)}>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.3" aria-hidden="true">
              <circle cx="7" cy="7" r="5.5" />
              <path d="M1.5 7h11M7 1.5c-2 2.8-2 8.2 0 11M7 1.5c2 2.8 2 8.2 0 11" />
            </svg>
          </button>
        )}
      </div>
      <p className="caption">
        {plural(inWindow, 'discovery', 'discoveries')} on the map
        {before > 0 && ` · ${plural(before, 'grey dot', 'grey dots')} came before this stretch`}
        {unplaced > 0 && ` · ${unplaced} with no place or date yet`}. A ring is a place known only as a country or region.
        <span className="caption-key">
          <i />
          <i />
          paler dots are minor
        </span>
      </p>
    </>
  )
}

/** The land at the current size and zoom, redrawn only when one of those changes. */
function paintBackdrop(
  cache: React.RefObject<Backdrop | null>,
  base: Basemap,
  fineLand: Path2D | null,
  { k, tx, ty }: Transform,
  width: number,
  height: number,
): HTMLCanvasElement {
  const ratio = window.devicePixelRatio || 1
  const landPath = fineLand ?? base.land
  const key = `${width}x${height}@${ratio} ${k} ${tx} ${ty} ${fineLand ? 'fine' : 'coarse'}`
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
  ctx.fill(landPath)
  ctx.lineWidth = 0.5 / k
  ctx.strokeStyle = LAND_EDGE
  ctx.stroke(landPath)
  ctx.lineWidth = 1 / k
  ctx.strokeStyle = RULE_SOFT
  ctx.stroke(base.sphere)
  cache.current = { canvas, key, base }
  return canvas
}
