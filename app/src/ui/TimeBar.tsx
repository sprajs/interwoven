import { useEffect, useMemo, useRef } from 'react'
import { roundRect, useCanvas, useSize } from '../lib/canvas.ts'
import { useApp, useFiltered, useLimits, useScale } from '../store.ts'
import { alpha, font, INK, INK_2, INK_3, PAPER } from '../theme.ts'
import { formatSpan, formatYear, log, makeAxis, PRESENT, ticks } from '../time.ts'
import { Menu, MenuHeading, Option } from './Menu.tsx'

const STARTS: { name: string; t: number | null; hint: string }[] = [
  { name: 'All', t: null, hint: 'The first tools, about 200,000 years ago' },
  { name: '10 000 BCE', t: -9999, hint: 'The first farming' },
  { name: '4000 BCE', t: -3999, hint: 'The first cities and writing' },
  { name: '1 CE', t: 1, hint: 'The last two thousand years' },
  { name: '1500', t: 1500, hint: 'Printing, oceanic voyages and modern science' },
  { name: '1800', t: 1800, hint: 'Industry and after' },
  { name: '1900', t: 1900, hint: 'The last century and a quarter' },
]

/** Seconds for the sweep to cross the whole window. */
const SWEEP = 24

/**
 * The whole of time on one strip, with the stretch in view picked out. Drag the stretch to move it,
 * drag an end to resize it, or press play to sweep forward from its start.
 */
export function TimeBar() {
  const chosen = useScale()
  // On a calendar almost all of the data sits in the last sliver of the strip, where it cannot be
  // picked out. The strip is for finding one's way, so it falls back to the logarithm there.
  const scale = chosen.id === 'calendar' ? log : chosen
  const limits = useLimits()
  const span = useApp((s) => s.window)
  const playing = useApp((s) => s.playing)
  const filtered = useFiltered()
  const [frame, size] = useSize<HTMLDivElement>()
  const axis = useMemo(() => makeAxis(scale, limits[0], limits[1], 1, Math.max(2, size.width - 1)), [scale, limits, size.width])

  const bins = useMemo(() => {
    const width = 3
    const counts = new Array<number>(Math.ceil(size.width / width) + 1).fill(0)
    for (const e of filtered) if (e.t !== undefined) counts[Math.max(0, Math.floor(axis.x(e.t) / width))]! += 1
    return { width, counts, peak: Math.max(1, ...counts) }
  }, [filtered, axis, size.width])

  const canvas = useCanvas(
    size,
    (ctx, { width, height }) => {
      const base = height - 20
      const x0 = axis.x(span[0])
      const x1 = axis.x(span[1])
      ctx.fillStyle = PAPER
      ctx.fillRect(x0, 0, x1 - x0, height)
      bins.counts.forEach((count, i) => {
        if (!count) return
        const x = i * bins.width
        const h = Math.max(2, (count / bins.peak) * (base - 8))
        ctx.fillStyle = alpha(INK, x + bins.width > x0 && x < x1 ? 0.62 : 0.26)
        ctx.fillRect(x, base - h, bins.width - 1, h)
      })
      ctx.fillStyle = alpha(INK, 0.2)
      ctx.fillRect(0, base, width, 1)
      ctx.font = font(11.5)
      ctx.textBaseline = 'middle'
      for (const tick of ticks(axis, 120)) {
        ctx.fillStyle = alpha(INK, 0.2)
        ctx.fillRect(Math.round(tick.x), base, 1, 4)
        ctx.fillStyle = INK_3
        const w = ctx.measureText(tick.label).width
        ctx.fillText(tick.label, Math.max(2, Math.min(width - w - 2, tick.x - w / 2)), base + 11)
      }
      // The stretch in view: a fine frame with a grip at each end.
      ctx.strokeStyle = alpha(INK, 0.55)
      ctx.lineWidth = 1
      ctx.strokeRect(x0 + 0.5, 0.5, Math.max(2, x1 - x0 - 1), height - 1)
      for (const x of [x0, x1]) {
        ctx.fillStyle = INK_2
        roundRect(ctx, x - 2.5, height / 2 - 10, 5, 20, 2.5)
        ctx.fill()
      }
    },
    [axis, bins, span],
  )

  // Play: the end of the window sweeps forward from its start to where it was.
  const target = useRef<[number, number] | null>(null)
  useEffect(() => {
    if (!playing) return
    const state = useApp.getState()
    const [from, to] = target.current ?? state.window
    target.current = [from, to]
    const u0 = chosen.u(from)
    const u1 = chosen.u(to)
    const begun = performance.now()
    state.setWindow([from, chosen.t(u0 + (u1 - u0) * 0.002)])
    let raf = 0
    const step = (now: number) => {
      const share = Math.min(1, (now - begun) / (SWEEP * 1000))
      useApp.getState().setWindow([from, chosen.t(u0 + (u1 - u0) * Math.max(0.002, share))])
      if (share >= 1) {
        target.current = null
        useApp.getState().setPlaying(false)
      } else raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [playing, chosen])

  // A long stretch is read in round figures: 1160, not 1159.
  const rounding = span[1] - span[0] > 2000 ? 10 : 1

  const stop = () => {
    const state = useApp.getState()
    if (state.playing && target.current) {
      state.setPlaying(false)
      state.setWindow(target.current)
    }
    target.current = null
  }

  const drag = useRef<{ mode: 'move' | 'start' | 'end'; grabU: number; span: [number, number] } | null>(null)
  const onDown = (event: React.PointerEvent<HTMLDivElement>) => {
    stop()
    const x = event.clientX - event.currentTarget.getBoundingClientRect().left
    const x0 = axis.x(span[0])
    const x1 = axis.x(span[1])
    let current = span
    let mode: 'move' | 'start' | 'end' = 'move'
    if (Math.abs(x - x0) <= 8) mode = 'start'
    else if (Math.abs(x - x1) <= 8) mode = 'end'
    else if (x < x0 || x > x1) {
      // Clicking outside brings the stretch to the pointer, then drags it.
      const half = (scale.u(span[1]) - scale.u(span[0])) / 2
      const centre = Math.max(scale.u(limits[0]) + half, Math.min(scale.u(limits[1]) - half, scale.u(axis.t(x))))
      current = [scale.t(centre - half), scale.t(centre + half)]
      useApp.getState().setWindow(current)
    }
    drag.current = { mode, grabU: scale.u(axis.t(x)), span: current }
    event.currentTarget.setPointerCapture(event.pointerId)
  }
  const onMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const held = drag.current
    const x = event.clientX - event.currentTarget.getBoundingClientRect().left
    if (!held) {
      const near = Math.min(Math.abs(x - axis.x(span[0])), Math.abs(x - axis.x(span[1]))) <= 8
      event.currentTarget.style.cursor = near ? 'ew-resize' : x > axis.x(span[0]) && x < axis.x(span[1]) ? 'grab' : 'pointer'
      return
    }
    const u = scale.u(axis.t(Math.max(axis.x0, Math.min(axis.x1, x))))
    const lo = scale.u(limits[0])
    const hi = scale.u(limits[1])
    const least = (hi - lo) / 400
    const u0 = scale.u(held.span[0])
    const u1 = scale.u(held.span[1])
    if (held.mode === 'move') {
      const shift = Math.max(lo - u0, Math.min(hi - u1, u - held.grabU))
      useApp.getState().setWindow([scale.t(u0 + shift), scale.t(u1 + shift)])
    } else if (held.mode === 'start') useApp.getState().setWindow([scale.t(Math.min(u, u1 - least)), held.span[1]])
    else useApp.getState().setWindow([held.span[0], scale.t(Math.max(u, u0 + least))])
  }

  return (
    <footer className="timebar">
      <div className="timebar-side">
        <button
          className="play"
          aria-label={playing ? 'Pause' : 'Play through time'}
          title={playing ? 'Pause' : 'Play forward through the stretch in view'}
          onClick={() => (playing ? useApp.getState().setPlaying(false) : useApp.getState().setPlaying(true))}
        >
          {playing ? (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
              <rect x="1.5" y="1" width="3" height="10" rx="0.5" />
              <rect x="7.5" y="1" width="3" height="10" rx="0.5" />
            </svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
              <path d="M2.5 1v10l8.5-5z" />
            </svg>
          )}
        </button>
        <div className="window-label">
          {formatYear(span[0], rounding)} – {span[1] >= PRESENT - 1 ? 'today' : formatYear(span[1], rounding)}
          <small>{formatSpan(span[1] - span[0])}</small>
        </div>
      </div>
      <div ref={frame} className="canvas-frame" onPointerDown={onDown} onPointerMove={onMove} onPointerUp={() => (drag.current = null)}>
        <canvas ref={canvas} style={{ width: size.width, height: size.height }} />
      </div>
      <div className="timebar-side">
        <Menu label="From" value={STARTS.find((start) => Math.abs(span[0] - (start.t ?? limits[0])) < 1)?.name ?? formatYear(span[0])} align="right" up>
          <MenuHeading>Show everything from</MenuHeading>
          {STARTS.map((start) => {
            const from = start.t ?? limits[0]
            return (
              <Option
                key={start.name}
                single
                name={start.t === null ? 'The beginning' : start.name}
                hint={start.hint}
                on={Math.abs(span[0] - from) < 1 && span[1] >= PRESENT - 1}
                onChoose={() => {
                  stop()
                  useApp.getState().setWindow([from, PRESENT])
                }}
              />
            )
          })}
        </Menu>
      </div>
    </footer>
  )
}
