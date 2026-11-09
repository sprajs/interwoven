import { useEffect, useLayoutEffect, useRef, useState } from 'react'

export interface Size {
  width: number
  height: number
}

/** The size of an element, kept current as the layout changes. */
export function useSize<T extends HTMLElement>(): [React.RefObject<T | null>, Size] {
  const ref = useRef<T | null>(null)
  const [size, setSize] = useState<Size>({ width: 0, height: 0 })
  useLayoutEffect(() => {
    const element = ref.current
    if (!element) return
    const measure = () => {
      const { width, height } = element.getBoundingClientRect()
      setSize((s) => (s.width === Math.round(width) && s.height === Math.round(height) ? s : { width: Math.round(width), height: Math.round(height) }))
    }
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [])
  return [ref, size]
}

/**
 * Draw on a canvas at the screen's own resolution. `draw` runs again whenever `deps` or the size
 * change, and once more when the fonts have loaded, since text drawn before then uses a fallback.
 */
export function useCanvas(size: Size, draw: (ctx: CanvasRenderingContext2D, size: Size) => void, deps: unknown[]): React.RefObject<HTMLCanvasElement | null> {
  const ref = useRef<HTMLCanvasElement | null>(null)
  const [fonts, setFonts] = useState(0)
  useEffect(() => {
    let live = true
    void document.fonts.ready.then(() => live && setFonts(1))
    return () => {
      live = false
    }
  }, [])
  useEffect(() => {
    const canvas = ref.current
    if (!canvas || !size.width || !size.height) return
    const ratio = window.devicePixelRatio || 1
    if (canvas.width !== Math.round(size.width * ratio) || canvas.height !== Math.round(size.height * ratio)) {
      canvas.width = Math.round(size.width * ratio)
      canvas.height = Math.round(size.height * ratio)
    }
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
    ctx.clearRect(0, 0, size.width, size.height)
    draw(ctx, size)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size.width, size.height, fonts, ...deps])
  return ref
}

/** A rounded rectangle path, for browsers and marks alike. */
export function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number): void {
  ctx.beginPath()
  ctx.roundRect(x, y, w, h, Math.min(r, w / 2, h / 2))
}
