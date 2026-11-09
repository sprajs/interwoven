import { Menu, MenuHeading, Option } from '../ui/Menu.tsx'
import { Fragment, useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { Entry } from '../data/model.ts'
import type { Bundle } from '../data/types.ts'
import type { Category } from '../dims.ts'
import { useCanvas, useSize } from '../lib/canvas.ts'
import { plural } from '../lib/text.ts'
import { useApp, useDimension, useFiltered, useLimits, useMatches, useModel, useScale } from '../store.ts'
import { alpha, font, INK, INK_2, INK_3, RULE, RULE_SOFT } from '../theme.ts'
import { formatSpan, formatYear, makeAxis, panWindow, PRESENT, ticks, zoomWindow, type Axis } from '../time.ts'
import './Trends.css'

type Measure = 'count' | 'century' | 'person'
type Population = NonNullable<Bundle['population']>
/** Points of a time series, as [year, value], in year order. */
type Series = [number, number][]

const MEASURES: { id: Measure; name: string; needsPopulation: boolean }[] = [
  { id: 'count', name: 'Count', needsPopulation: false },
  { id: 'century', name: 'Per century', needsPopulation: false },
  { id: 'person', name: 'Per person', needsPopulation: true },
]

const MEASURE_HINTS: Record<Measure, string> = {
  count: 'How many discoveries fall in each bar',
  century: 'The count divided by the years the bar covers',
  person: 'The count divided by the person-years lived in that time',
}

const TITLES: Record<Measure, string> = {
  count: 'Number of discoveries',
  century: 'Discoveries per century',
  person: 'Discoveries per billion person-years lived',
}

/** The unit over the y axis, so a value can be read without the title. */
const UNITS: Record<Measure, string> = {
  count: 'discoveries',
  century: 'per century',
  person: 'per billion person-years',
}

/** Room for the y labels; the population chart's ("100 million") are the widest. */
const PAD_LEFT = 84
const PAD_RIGHT = 20
/** The page margin, as `--gutter` in styles.css. */
const GUTTER = 20
/** Room at the right for naming the regional population lines at their ends. */
const PAD_RIGHT_NAMED = 116
/** The width each bin aims for on screen, gap included. */
const BIN = 23
const BAR_GAP = 3
const SEGMENT_GAP = 1.5
/** Bars sit a little back from full strength, so they do not outweigh everything else in the app. */
const BAR_ALPHA = 0.86
/**
 * A rate is given only where it rests on this many discoveries. With fewer, one discovery in a short
 * stretch or over a small population makes the tallest bar on the chart from the least evidence.
 */
const MIN_FOR_RATE = 3
/** Spacing between names at the ends of lines. */
const NAME_GAP = 15
/** Names further than this from their line's end are dropped rather than left to float. */
const NAME_DRIFT = 10
/** Room above the plot for the unit label. */
const TOP = 34
/** Between the rows of the small multiples, and the room each gives its name. */
const ROW_GAP = 8
const ROW_HEAD = 20
const RULER = 30
const GAP = 16
/** The population chart, title included. */
const POPULATION = 130
const POPULATION_HEAD = 24
/** Clear paper under the charts for the caption. */
const FOOT = 42
const PER_BILLION = 1e9

interface Bin {
  t0: number
  t1: number
  /** The moment at the bin's centre on screen. */
  mid: number
  x0: number
  x1: number
  /** Discoveries in each of the plan's categories. */
  counts: number[]
  total: number
  /** World person-years lived during the bin, or null before the estimates begin. */
  lived: number | null
  /** Person-years lived in each category's own region; filled only for the regional small multiples. */
  livedIn: (number | null)[]
}

/** One region's own small bar chart, on its own scale. */
interface Row {
  category: Category
  top: number
  plotTop: number
  bottom: number
  /** The value at the top of the row's scale, where its one gridline sits. */
  peak: number
}

interface PopulationLine {
  name: string
  color: string
  /** Samples across the axis; null where there is no estimate. */
  points: ({ x: number; y: number } | null)[]
}

interface PopulationChart {
  title: string
  top: number
  plotTop: number
  bottom: number
  lines: PopulationLine[]
  grid: { value: number; y: number }[]
}

interface Plan {
  axis: Axis
  u0: number
  du: number
  bins: Bin[]
  categories: Category[]
  /** One row per region, each divided by its own population, because such rates cannot be stacked. */
  rows: Row[] | null
  /** Each bin's value for each category in the chosen measure; null where it cannot be worked out. */
  values: (number | null)[][]
  /** Each bin's value for everything in it, in the chosen measure against the whole world. */
  headline: (number | null)[]
  /** Whether bars on one or two discoveries are outlined rather than given as rates. */
  guarded: boolean
  /** Whether any outlined bar is in view. */
  outlined: boolean
  grid: number[]
  yMax: number
  top: number
  baseline: number
  population: PopulationChart | null
  counted: number
  /** Discoveries in view that the chart cannot show: those with no place, in the regional rows. */
  unplaced: number
}

/**
 * Count discoveries in equal steps of the time scale, so that every bar is the same width on screen,
 * and turn the counts into the chosen measure.
 */
function layout(entries: Entry[], axis: Axis, all: Category[], of: (e: Entry) => string, measure: Measure, regional: boolean, population: Population | null, height: number): Plan {
  const multiples = regional && measure === 'person' && population !== null
  // Regional rates need a population for the region, which "no place yet" does not have.
  const categories = multiples ? all.filter((c) => population.person_years[c.id]) : all
  const indexOf = new Map(categories.map((c, i) => [c.id, i]))
  const n = Math.max(1, Math.round((axis.x1 - axis.x0) / BIN))
  const { scale } = axis
  const u0 = scale.u(axis.t0)
  const du = (scale.u(axis.t1) - u0) / n
  const width = (axis.x1 - axis.x0) / n
  const world = population?.person_years.world
  const bins: Bin[] = Array.from({ length: n }, (_, i) => {
    const t0 = i === 0 ? axis.t0 : scale.t(u0 + i * du)
    const t1 = i === n - 1 ? axis.t1 : scale.t(u0 + (i + 1) * du)
    return {
      t0,
      t1,
      mid: scale.t(u0 + (i + 0.5) * du),
      x0: axis.x0 + i * width,
      x1: axis.x0 + (i + 1) * width,
      counts: categories.map(() => 0),
      total: 0,
      lived: world ? livedBetween(world, t0, t1) : null,
      livedIn: multiples ? categories.map((c) => livedBetween(population.person_years[c.id]!, t0, t1)) : [],
    }
  })

  let counted = 0
  let unplaced = 0
  for (const e of entries) {
    const k = indexOf.get(of(e))
    if (k === undefined) {
      unplaced += 1
      continue
    }
    const bin = bins[binIndex(scale.u(e.t!), u0, du, n)]!
    bin.counts[k]! += 1
    bin.total += 1
    counted += 1
  }

  const factor = (bin: Bin): number | null => {
    if (measure === 'count') return 1
    if (measure === 'century') return 100 / (bin.t1 - bin.t0)
    return bin.lived && bin.lived > 0 ? PER_BILLION / bin.lived : null
  }
  const values = bins.map((bin) =>
    bin.counts.map((count, k) => {
      if (multiples) {
        const lived = bin.livedIn[k]
        return lived && lived > 0 ? (count * PER_BILLION) / lived : null
      }
      const f = factor(bin)
      return f === null ? null : count * f
    }),
  )
  const headline = bins.map((bin) => {
    const f = factor(bin)
    return f === null ? null : bin.total * f
  })

  const guarded = measure !== 'count'
  const weak = (count: number) => guarded && count > 0 && count < MIN_FOR_RATE
  const outlined = bins.some((bin, i) => (multiples ? bin.counts.some((c, k) => weak(c) && values[i]![k] !== null) : weak(bin.total) && headline[i] !== null))
  // Outlined bars do not set the scale; plain counts are all equally sure.
  const peak = multiples ? 0 : guarded ? sturdyPeak(bins.map((bin, i) => ({ count: bin.total, value: headline[i] ?? null }))) : Math.max(0, ...headline.map((v) => v ?? 0))
  const grid = niceTicks(peak, measure === 'count')
  const popBottom = height - FOOT
  const popTop = population ? popBottom - POPULATION : popBottom
  const baseline = popTop - RULER - (population ? GAP : 0)

  let rows: Row[] | null = null
  if (multiples) {
    // The rows share the height of the main chart equally.
    const h = (baseline - TOP - (categories.length - 1) * ROW_GAP) / Math.max(1, categories.length)
    rows = categories.map((category, k) => {
      const top = TOP + k * (h + ROW_GAP)
      return {
        category,
        top,
        plotTop: top + ROW_HEAD,
        bottom: top + h,
        peak: sturdyPeak(bins.map((bin, i) => ({ count: bin.counts[k]!, value: values[i]![k] ?? null }))),
      }
    })
  }

  return {
    axis,
    u0,
    du,
    bins,
    categories,
    rows,
    values,
    headline,
    guarded,
    outlined,
    grid,
    yMax: grid[grid.length - 1] ?? 1,
    top: TOP,
    baseline,
    population: population ? populationChart(population, axis, regional ? all : null, popTop, popBottom) : null,
    counted,
    unplaced,
  }
}

/** World population as one line, or each region's as its own, on a logarithmic axis. */
function populationChart(population: Population, axis: Axis, regions: Category[] | null, top: number, bottom: number): PopulationChart {
  const plotTop = top + POPULATION_HEAD
  const sources = regions
    ? regions.flatMap((c) => {
        const series = population.series[c.id]
        return series ? [{ name: c.name, color: c.color, series }] : []
      })
    : population.series.world
      ? [{ name: 'World', color: INK, series: population.series.world }]
      : []
  const xs: number[] = []
  for (let x = axis.x0; x < axis.x1; x += 2) xs.push(x)
  xs.push(axis.x1)
  let lo = Infinity
  let hi = 0
  const sampled = sources.map((source) =>
    xs.map((x) => {
      const people = populationAt(source.series, axis.t(x))
      if (people === null || people <= 0) return null
      lo = Math.min(lo, people)
      hi = Math.max(hi, people)
      return { x, people }
    }),
  )
  const [d0, d1] = hi > 0 ? logDomain(lo, hi) : [1e6, 1e7]
  const y = (people: number) => bottom - ((Math.log(people) - Math.log(d0)) / (Math.log(d1) - Math.log(d0))) * (bottom - plotTop)
  return {
    title: regions ? 'Population by region' : 'World population',
    top,
    plotTop,
    bottom,
    lines: sources.map((source, i) => ({
      name: source.name,
      color: source.color,
      points: sampled[i]!.map((p) => (p ? { x: p.x, y: y(p.people) } : null)),
    })),
    grid: logTicks(d0, d1).map((value) => ({ value, y: y(value) })),
  }
}

/** One line saying how many discoveries are counted and how much time one bar covers. */
function describe(plan: Plan, measure: Measure, searching: boolean): string {
  const first = plan.bins[0]!
  const last = plan.bins[plan.bins.length - 1]!
  const a = formatSpan(first.t1 - first.t0)
  const b = formatSpan(last.t1 - last.t0)
  const calendar = plan.axis.scale.id === 'calendar'
  // Only the calendar scale has one length of bar; on the others the length changes across the axis.
  const covers = calendar || a === b ? `about ${a}` : `from about ${a} at the left to ${b} at the right`
  let text = `${plural(plan.counted, 'discovery', 'discoveries')}${searching ? ' matching the search' : ''} in view. Bars are equal widths on screen; on this scale each covers ${covers}.`
  if (measure === 'count' && !calendar) text += ' Bars cover different lengths of time, so compare them per century or per person.'
  if (plan.rows) text += ' Each region is divided by its own population and has its own scale.'
  // Keep "one or two" in step with MIN_FOR_RATE.
  if (plan.outlined) text += ' Outlined bars hold one or two discoveries: too few for a rate.'
  if (plan.rows && plan.unplaced) text += ` Left out: ${plural(plan.unplaced, 'discovery', 'discoveries')} with no place yet.`
  return text
}

/** What the lit bin is made of, for the line under the title: a count per category, or each region's own rate. */
function breakdown(plan: Plan, index: number): { category: Category; text: string }[] {
  const bin = plan.bins[index]
  if (!bin) return []
  return plan.categories.flatMap((category, k) => {
    const count = bin.counts[k] ?? 0
    if (!plan.rows) return count ? [{ category, text: group(count) }] : []
    const rate = plan.values[index]?.[k] ?? null
    const text = count === 0 ? '0' : rate === null ? 'no estimate' : count < MIN_FOR_RATE ? 'too few' : formatValue(rate)
    return [{ category, text }]
  })
}

export function Trends() {
  const model = useModel()
  const scale = useScale()
  const limits = useLimits()
  const dimension = useDimension()
  const filtered = useFiltered()
  const matches = useMatches()
  const span = useApp((s) => s.window)
  const hidden = useApp((s) => s.hidden)
  const population = model.bundle.population
  const [chosen, setMeasure] = useState<Measure>(population ? 'person' : 'count')
  const measure: Measure = chosen === 'person' && !population ? 'count' : chosen
  const [tip, setTip] = useState<{ bin: number; frame: Box } | null>(null)
  const [frame, size] = useSize<HTMLDivElement>()
  const regional = dimension.id === 'region'

  const plan = useMemo(() => {
    if (!size.width || !size.height) return null
    const axis = makeAxis(scale, span[0], span[1], PAD_LEFT, size.width - (regional ? PAD_RIGHT_NAMED : PAD_RIGHT))
    const categories = dimension.categories.filter((c) => !hidden.has(`${dimension.id}:${c.id}`))
    const entries = filtered.filter((e) => e.t !== undefined && e.t >= axis.t0 && e.t <= axis.t1 && (!matches || matches.has(e.id)))
    return layout(entries, axis, categories, dimension.of, measure, regional, population, size.height)
  }, [size, scale, span, dimension, filtered, matches, hidden, measure, regional, population])

  const empty = plan !== null && plan.counted === 0
  const hoverBin = tip?.bin ?? null

  const canvas = useCanvas(
    size,
    (ctx, { width }) => {
      if (!plan || empty) return
      const { axis, bins, baseline, top } = plan

      ctx.font = font(11.5)
      ctx.fillStyle = INK_3
      ctx.textBaseline = 'middle'
      ctx.textAlign = 'left'
      ctx.fillText(UNITS[measure], GUTTER, top - 18)

      // The bin under the pointer, carried down through every chart.
      const lit = hoverBin === null ? undefined : bins[hoverBin]
      if (lit) {
        ctx.fillStyle = alpha(INK, 0.07)
        ctx.fillRect(lit.x0, top - 8, lit.x1 - lit.x0, (plan.population?.bottom ?? baseline) - top + 8)
      }

      if (plan.rows) drawRows(ctx, plan, plan.rows, hoverBin)
      else drawStacks(ctx, plan, hoverBin)

      ctx.fillStyle = RULE
      ctx.fillRect(axis.x0, Math.round(baseline), axis.x1 - axis.x0, 1)

      // The date ruler, shared by every chart.
      ctx.font = font(12.5)
      ctx.textAlign = 'left'
      for (const tick of ticks(axis, 84)) {
        ctx.fillStyle = RULE
        ctx.fillRect(Math.round(tick.x), Math.round(baseline), 1, 7)
        ctx.fillStyle = INK_2
        const w = ctx.measureText(tick.label).width
        ctx.fillText(tick.label, Math.min(tick.x + 5, width - w - 4), baseline + RULER / 2)
      }

      if (plan.population) drawPopulation(ctx, plan.population, axis)
    },
    [plan, empty, hoverBin, measure],
  )

  const drag = useRef<{ x: number; moved: boolean; span: [number, number] } | null>(null)
  const binAt = (clientX: number): number | null => {
    if (!plan || empty || !frame.current) return null
    const x = clientX - frame.current.getBoundingClientRect().left
    if (x < plan.axis.x0 || x >= plan.axis.x1) return null
    return Math.min(plan.bins.length - 1, Math.floor(((x - plan.axis.x0) / (plan.axis.x1 - plan.axis.x0)) * plan.bins.length))
  }

  /** Zoom to a bin with one bin of context either side. */
  const drillInto = (i: number) => {
    if (!plan) return
    const lo = scale.u(limits[0])
    const hi = scale.u(limits[1])
    const n0 = Math.max(lo, plan.u0 + (i - 1) * plan.du)
    const n1 = Math.min(hi, plan.u0 + (i + 2) * plan.du)
    if (n1 - n0 < (hi - lo) / 4000) return
    setTip(null)
    useApp.getState().setWindow([scale.t(n0), scale.t(n1)])
  }

  const tipBin = tip && plan && !empty ? plan.bins[tip.bin] : undefined
  const parts = tip && plan && tipBin ? breakdown(plan, tip.bin) : null
  const searching = matches !== null
  return (
    <div className="trends">
      <header className="trends-head">
        <div>
          <h2>{TITLES[measure]}</h2>
          {/* While a bin is lit, its make-up takes the note's place; the note keeps its room so nothing moves. */}
          <div className="trends-note">
            <p style={parts ? { visibility: 'hidden' } : undefined}>{plan && !empty ? describe(plan, measure, searching) : ' '}</p>
            {parts && (
              <p className="trends-breakdown">
                {parts.length === 0
                  ? 'No discoveries in this stretch.'
                  : parts.map((part, i) => (
                      <Fragment key={part.category.id}>
                        {i > 0 && ' · '}
                        <span>
                          <i className="swatch" style={{ background: part.category.color }} />
                          {part.category.name} {part.text}
                        </span>
                      </Fragment>
                    ))}
              </p>
            )}
          </div>
        </div>
        <Menu label="Measure" value={MEASURES.find((m) => m.id === measure)!.name} align="right">
          <MenuHeading>What each bar counts</MenuHeading>
          {MEASURES.filter((m) => population || !m.needsPopulation).map((m) => (
            <Option key={m.id} single name={m.name} hint={MEASURE_HINTS[m.id]} on={measure === m.id} onChoose={() => setMeasure(m.id)} />
          ))}
        </Menu>
      </header>
      <div
        ref={frame}
        className="canvas-frame"
        style={{ cursor: tip ? 'zoom-in' : 'grab' }}
        onPointerDown={(event) => {
          drag.current = { x: event.clientX, moved: false, span }
          event.currentTarget.setPointerCapture(event.pointerId)
        }}
        onPointerMove={(event) => {
          const held = drag.current
          if (held && plan) {
            const dx = event.clientX - held.x
            if (Math.abs(dx) > 3) held.moved = true
            if (held.moved) {
              setTip(null)
              useApp.getState().setWindow(panWindow(scale, held.span, -dx / (plan.axis.x1 - plan.axis.x0), limits))
              return
            }
          }
          const bin = binAt(event.clientX)
          if (bin === null) return setTip(null)
          const { left, top, right } = event.currentTarget.getBoundingClientRect()
          // The card is anchored to the bin, not the pointer, so it only moves when the bin changes.
          setTip((held) => (held?.bin === bin ? held : { bin, frame: { left, top, right } }))
        }}
        onPointerUp={(event) => {
          const held = drag.current
          drag.current = null
          if (held?.moved) return
          const bin = binAt(event.clientX)
          if (bin !== null) drillInto(bin)
        }}
        onPointerLeave={() => setTip(null)}
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
          setTip(null)
        }}
      >
        <canvas ref={canvas} style={{ width: size.width, height: size.height }} />
        {empty && <p className="notice trends-empty">No discoveries are recorded in this stretch of time.</p>}
      </div>
      {tip && plan && tipBin && <BinCard plan={plan} index={tip.bin} frame={tip.frame} measure={measure} population={population} />}
      <p className="caption">These charts show how far the research has reached, not how much was discovered.</p>
    </div>
  )
}

/** Gridlines across the main chart, each with its value at the left. */
function drawGrid(ctx: CanvasRenderingContext2D, axis: Axis, values: number[], yOf: (v: number) => number): void {
  ctx.font = font(12)
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'right'
  for (const value of values) {
    const y = Math.round(yOf(value))
    if (value > 0) {
      ctx.fillStyle = RULE_SOFT
      ctx.fillRect(axis.x0, y, axis.x1 - axis.x0, 1)
    }
    ctx.fillStyle = INK_3
    // Gridlines sit on round values already, so they are labelled exactly.
    ctx.fillText(value >= 100 ? group(value) : String(value), axis.x0 - 10, y)
  }
  ctx.textAlign = 'left'
}

/**
 * Stacked bars: categories in their fixed order from the bottom, with paper between them. A bar on
 * one or two discoveries is only outlined, since its rate means little.
 */
function drawStacks(ctx: CanvasRenderingContext2D, plan: Plan, lit: number | null): void {
  const { baseline, top } = plan
  const yOf = (v: number) => baseline - (v / plan.yMax) * (baseline - top)
  drawGrid(ctx, plan.axis, plan.grid, yOf)
  plan.bins.forEach((bin, i) => {
    const total = plan.headline[i]
    if (!total) return
    const x = bin.x0 + BAR_GAP / 2
    const w = bin.x1 - bin.x0 - BAR_GAP
    if (plan.guarded && bin.total < MIN_FOR_RATE) {
      outlineBar(ctx, x, w, yOf(Math.min(total, plan.yMax)), baseline, total > plan.yMax)
      return
    }
    const strength = i === lit ? 1 : BAR_ALPHA
    // Clip the whole stack to a shape rounded at the top, so only the topmost segment shows the curve.
    ctx.save()
    ctx.beginPath()
    ctx.roundRect(x, yOf(total), w, baseline - yOf(total), [2, 2, 0, 0])
    ctx.clip()
    let below = 0
    plan.categories.forEach((category, k) => {
      const value = plan.values[i]![k]
      if (!value) return
      const y0 = yOf(below)
      const y1 = yOf(below + value)
      // A segment too thin to survive the gap is drawn without it, so that it does not vanish.
      const floor = below > 0 && y0 - y1 > SEGMENT_GAP + 1 ? y0 - SEGMENT_GAP : y0
      ctx.fillStyle = alpha(category.color, strength)
      ctx.fillRect(x, y1, w, floor - y1)
      below += value
    })
    ctx.restore()
  })
}

/**
 * Small multiples: one row per region, each a bar chart of that region's discoveries per billion of
 * its own person-years, on its own scale with one gridline at its peak.
 */
function drawRows(ctx: CanvasRenderingContext2D, plan: Plan, rows: Row[], lit: number | null): void {
  const { axis } = plan
  rows.forEach((row, k) => {
    const yOf = (v: number) => row.bottom - (v / row.peak) * (row.bottom - row.plotTop)
    // Each row's baseline is a soft rule that also parts it from the row below; the last is the chart's own baseline.
    if (k < rows.length - 1) {
      ctx.fillStyle = RULE_SOFT
      ctx.fillRect(axis.x0, Math.round(row.bottom), axis.x1 - axis.x0, 1)
    }
    ctx.fillStyle = row.category.color
    ctx.fillRect(axis.x0, row.top + 3, 8, 8)
    ctx.font = font(12.5, 600)
    ctx.fillStyle = INK_2
    ctx.textBaseline = 'middle'
    ctx.textAlign = 'left'
    ctx.fillText(row.category.name, axis.x0 + 14, row.top + 7.5)
    if (row.peak > 0) {
      const y = Math.round(row.plotTop)
      ctx.fillStyle = RULE_SOFT
      ctx.fillRect(axis.x0, y, axis.x1 - axis.x0, 1)
      ctx.font = font(12)
      ctx.fillStyle = INK_3
      ctx.textAlign = 'right'
      ctx.fillText(formatValue(row.peak), axis.x0 - 10, y)
      ctx.textAlign = 'left'
    }

    plan.bins.forEach((bin, i) => {
      const value = plan.values[i]![k]
      const count = bin.counts[k]!
      if (!count || value === null || value === undefined || row.peak <= 0) return
      const x = bin.x0 + BAR_GAP / 2
      const w = bin.x1 - bin.x0 - BAR_GAP
      if (count < MIN_FOR_RATE) {
        outlineBar(ctx, x, w, yOf(Math.min(value, row.peak)), row.bottom, value > row.peak)
        return
      }
      ctx.fillStyle = alpha(row.category.color, i === lit ? 1 : BAR_ALPHA)
      ctx.beginPath()
      ctx.roundRect(x, yOf(value), w, row.bottom - yOf(value), [2, 2, 0, 0])
      ctx.fill()
    })
  })
}

/** A bar on one or two discoveries: an outline only, left open at the top where it runs off the scale. */
function outlineBar(ctx: CanvasRenderingContext2D, x: number, w: number, top: number, bottom: number, clamped: boolean): void {
  const left = Math.round(x) + 0.5
  const right = Math.round(x + w) - 0.5
  const floor = Math.round(bottom)
  const ceiling = Math.round(Math.min(top, bottom - 3)) + 0.5
  ctx.strokeStyle = alpha(INK, 0.4)
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(left, floor)
  ctx.lineTo(left, ceiling)
  if (clamped) ctx.moveTo(right, ceiling)
  else ctx.lineTo(right, ceiling)
  ctx.lineTo(right, floor)
  ctx.stroke()
}

function drawPopulation(ctx: CanvasRenderingContext2D, chart: PopulationChart, axis: Axis): void {
  ctx.font = font(12.5, 600)
  ctx.fillStyle = INK_2
  ctx.textAlign = 'left'
  ctx.fillText(chart.title, GUTTER, chart.top + 8)

  ctx.font = font(12)
  ctx.textAlign = 'right'
  for (const line of chart.grid) {
    const y = Math.round(line.y)
    ctx.fillStyle = RULE_SOFT
    ctx.fillRect(axis.x0, y, axis.x1 - axis.x0, 1)
    ctx.fillStyle = INK_3
    ctx.fillText(formatPeople(line.value), axis.x0 - 10, y)
  }
  ctx.textAlign = 'left'

  // A light line: this chart is context for the one above, not the subject.
  ctx.lineWidth = 1.5
  ctx.lineJoin = 'round'
  for (const line of chart.lines) {
    ctx.strokeStyle = line.color === INK ? alpha(INK, 0.8) : line.color
    ctx.beginPath()
    let pen = false
    for (const p of line.points) {
      if (!p) {
        pen = false
        continue
      }
      if (pen) ctx.lineTo(p.x, p.y)
      else ctx.moveTo(p.x, p.y)
      pen = true
    }
    ctx.stroke()
  }

  // The regional lines are named at their right ends; one world line needs no name beside its title.
  if (chart.lines.length < 2) return
  const ends = chart.lines.flatMap((line) => {
    const end = line.points[line.points.length - 1]
    return end ? [{ name: line.name, color: line.color, y: end.y }] : []
  })
  ends.sort((a, b) => a.y - b.y)
  const ys = spread(
    ends.map((end) => end.y),
    NAME_GAP,
    chart.plotTop,
    chart.bottom,
  )
  ctx.font = font(12.5)
  ctx.textBaseline = 'middle'
  ends.forEach((end, i) => {
    const y = ys[i]!
    // A name pushed far from its line would read as belonging to another; the rows above name the regions anyway.
    if (Math.abs(y - end.y) > NAME_DRIFT) return
    ctx.fillStyle = end.color
    ctx.beginPath()
    ctx.arc(axis.x1 + 11, y, 3, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = INK_2
    ctx.fillText(end.name, axis.x1 + 18, y)
  })
}

/** The frame's edges on the page, in viewport pixels. */
interface Box {
  left: number
  top: number
  right: number
}

/**
 * A small card for the lit bin: its period, its value, and how many discoveries and people stand
 * behind it. It sits above the plot, centred on the bin, so it never covers a bar.
 */
function BinCard({ plan, index, frame, measure, population }: { plan: Plan; index: number; frame: Box; measure: Measure; population: Population | null }) {
  const ref = useRef<HTMLDivElement | null>(null)
  const [position, setPosition] = useState<{ left: number; top: number } | null>(null)

  useLayoutEffect(() => {
    const bin = plan.bins[index]
    if (!ref.current || !bin) return
    const box = ref.current.getBoundingClientRect()
    const centre = frame.left + (bin.x0 + bin.x1) / 2
    const left = Math.max(frame.left + 4, Math.min(frame.right - 4 - box.width, centre - box.width / 2))
    setPosition({ left, top: frame.top + plan.top - 6 - box.height })
  }, [frame, index, plan, measure])

  const bin = plan.bins[index]!
  const value = plan.headline[index] ?? null
  const world = population?.series.world ? populationAt(population.series.world, bin.mid) : null
  const people = world === null ? null : `world population about ${formatPeople(world)}`
  const footing = measure === 'count' ? (people && people[0]!.toUpperCase() + people.slice(1)) : [plural(bin.total, 'discovery', 'discoveries'), people].filter(Boolean).join(' · ')

  return (
    <div ref={ref} className="tooltip trends-card" role="tooltip" style={position ?? { left: 0, top: 0, visibility: 'hidden' }}>
      <h4>{formatPeriod(bin.t0, bin.t1)}</h4>
      <p className="trends-value">
        {value === null ? (
          'No population estimate this early'
        ) : measure === 'count' ? (
          <>
            <strong>{group(value)}</strong> {value === 1 ? 'discovery' : 'discoveries'}
          </>
        ) : (
          <>
            <strong>{formatValue(value)}</strong> {measure === 'century' ? 'per century' : `per billion person-years${plan.rows ? ' worldwide' : ''}`}
          </>
        )}
      </p>
      {footing && <p className="meta">{footing}</p>}
    </div>
  )
}

/**
 * The value at the top of a scale: the highest among bins resting on enough discoveries to give a
 * rate, or the highest of all when none does, so that a sparse chart still has a scale.
 */
function sturdyPeak(bins: { count: number; value: number | null }[]): number {
  const sturdy = bins.filter((b) => b.count >= MIN_FOR_RATE)
  return Math.max(0, ...(sturdy.length ? sturdy : bins).map((b) => b.value ?? 0))
}

/** Which of `n` equal steps from `u0` a position falls in; the window's end belongs to the last. */
function binIndex(u: number, u0: number, du: number, n: number): number {
  return Math.max(0, Math.min(n - 1, Math.floor((u - u0) / du)))
}

/** Linear interpolation in a series; null outside it. */
function interpolate(series: Series, x: number): number | null {
  const first = series[0]
  const last = series[series.length - 1]
  if (!first || !last || x < first[0] || x > last[0]) return null
  let lo = 0
  let hi = series.length - 1
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1
    if (series[mid]![0] <= x) lo = mid
    else hi = mid
  }
  const a = series[lo]!
  const b = series[hi]!
  return b[0] === a[0] ? a[1] : a[1] + ((x - a[0]) / (b[0] - a[0])) * (b[1] - a[1])
}

/** People alive at a moment. The estimates stop a few years short of today, so the last one holds after it. */
function populationAt(series: Series, t: number): number | null {
  const last = series[series.length - 1]
  return last && t > last[0] ? last[1] : interpolate(series, t)
}

/** Person-years lived up to a moment, carried on at the final rate after the estimates stop, as the time scale does. */
function livedUntil(series: Series, t: number): number | null {
  const last = series[series.length - 1]
  const before = series[series.length - 2]
  if (last && before && t > last[0]) return last[1] + ((t - last[0]) * (last[1] - before[1])) / (last[0] - before[0])
  return interpolate(series, t)
}

/** Person-years lived between two moments, or null when the first comes before the estimates. */
function livedBetween(series: Series, t0: number, t1: number): number | null {
  const a = livedUntil(series, t0)
  const b = livedUntil(series, t1)
  return a === null || b === null ? null : b - a
}

/**
 * Round gridline values from zero up to at least `peak`: the finest steps of 1, 2, 2.5 or 5 that
 * need no more than five lines, which also gives at least three. Counts never get fractional steps.
 */
function niceTicks(peak: number, whole: boolean): number[] {
  const top = peak > 0 && Number.isFinite(peak) ? peak : 1
  let power = 10 ** (Math.floor(Math.log10(top)) - 1)
  for (;;) {
    for (const m of [1, 2, 2.5, 5]) {
      const step = m * power
      if (whole && (step < 1 || !Number.isInteger(step))) continue
      const count = Math.ceil(top / step - 1e-9)
      if (count <= 5) return Array.from({ length: count + 1 }, (_, i) => Number((i * step).toPrecision(12)))
    }
    power *= 10
  }
}

/** A logarithmic population domain with a little room around the data, never narrower than a factor of six. */
function logDomain(lo: number, hi: number): [number, number] {
  let a = lo / 1.15
  let b = hi * 1.15
  if (b / a < 6) {
    const centre = Math.sqrt(a * b)
    a = centre / Math.sqrt(6)
    b = centre * Math.sqrt(6)
  }
  return [a, b]
}

/**
 * Three or four round values for a logarithmic axis. Coarse ladders are tried first: powers of ten,
 * thinned when there are too many, then finer steps within each decade for narrow windows.
 */
function logTicks(lo: number, hi: number): number[] {
  const ladders = [[1], [1, 3], [1, 2, 5], [1, 1.5, 2, 3, 5, 7]]
  let found: number[] = []
  for (const ladder of ladders) {
    const values: number[] = []
    for (let power = Math.floor(Math.log10(lo)); 10 ** power <= hi; power++) {
      for (const m of ladder) {
        const v = m * 10 ** power
        if (v >= lo && v <= hi) values.push(v)
      }
    }
    const every = Math.ceil(values.length / 4)
    found = values.filter((_, i) => i % every === 0)
    if (found.length >= 3) return found
  }
  return found
}

/** Push sorted positions apart to at least `gap`, keeping them within [lo, hi] where they fit. */
function spread(ys: number[], gap: number, lo: number, hi: number): number[] {
  const out = [...ys]
  for (let i = 0; i < out.length; i++) out[i] = Math.max(out[i]!, i > 0 ? out[i - 1]! + gap : lo)
  for (let i = out.length - 1; i >= 0; i--) out[i] = Math.min(out[i]!, i < out.length - 1 ? out[i + 1]! - gap : hi)
  return out
}

/** Whole numbers with the same narrow-space grouping as the years: 1850, 12 400. */
function group(n: number): string {
  const whole = Math.round(n)
  return whole < 10000 ? String(whole) : String(whole).replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

/** A value to two or three significant figures: 0.042, 3.5, 12.4, 380. */
function formatValue(v: number): string {
  if (v === 0) return '0'
  if (v >= 100) return group(v)
  return String(Number(v.toPrecision(v >= 10 ? 3 : 2)))
}

/** A head count in words: "100 million", "1.5 billion". */
function formatPeople(n: number): string {
  for (const [size, name] of [
    [1e9, 'billion'],
    [1e6, 'million'],
    [1e3, 'thousand'],
  ] as const) {
    if (n >= size) return `${Number((n / size).toPrecision(3))} ${name}`
  }
  return group(n)
}

/** A bin's period, with its ends rounded to well under its own length. */
function formatPeriod(t0: number, t1: number): string {
  const years = t1 - t0
  const round = years >= 10000 ? 1000 : years >= 1000 ? 100 : years >= 100 ? 10 : 1
  const a = formatYear(t0, round)
  const b = t1 >= PRESENT - 1 ? 'today' : formatYear(t1, round)
  return a === b ? a : `${a} – ${b}`
}
