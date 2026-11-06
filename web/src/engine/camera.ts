import { LAYOUT } from '../design.ts'
/**
 * View over the (v, y) plane, where v is the axis position after any folding. Time and height
 * have their own zoom. An ordinary zoom moves both, with time zooming faster, so marks spread
 * apart without running away from each other. Either axis can also be scaled alone.
 */
const Y_ZOOM_EXPONENT = 0.55

export type ZoomAxis = 'both' | 'time' | 'height'

export interface Insets {
  top: number
  bottom: number
  left: number
  right: number
}

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)

export class Camera {
  width = 1
  height = 1
  insets: Insets = { top: LAYOUT.frameTop + LAYOUT.framePad, bottom: LAYOUT.frameBottom + LAYOUT.framePad, left: LAYOUT.margin, right: LAYOUT.margin }
  cu = 0.5
  cy = 0.5
  /** Time zoom. */
  logZoom = 0
  /** Height zoom. */
  logY = 0
  maxLogZoom = Math.log(220)
  maxLogY = Math.log(40)
  /** Set for reduced motion: zooms arrive at once instead of easing. */
  instant = false

  private targetInsets: Insets = this.insets
  private targetLogZoom = 0
  private targetLogY = 0
  /** How quickly zoom catches up with its target. A pinch is direct; a wheel notch eases. */
  private zoomRate = 16
  private anchor: { px: number; py: number; u: number; y: number } | null = null
  private velocity = { x: 0, y: 0 }
  private fly: {
    t: number
    duration: number
    from: [number, number, number, number]
    to: [number, number, number, number]
    bump: number
  } | null = null

  get zoom(): number {
    return Math.exp(this.logZoom)
  }

  get xScale(): number {
    return this.scaleX(this.logZoom)
  }

  get yScale(): number {
    return this.scaleY(this.logY)
  }

  get centerX(): number {
    return this.insets.left + (this.width - this.insets.left - this.insets.right) / 2
  }

  get centerY(): number {
    return this.insets.top + (this.height - this.insets.top - this.insets.bottom) / 2
  }

  private scaleX(logZoom: number): number {
    return Math.exp(logZoom) * Math.max(1, this.width - this.insets.left - this.insets.right)
  }

  private scaleY(logY: number): number {
    return Math.exp(logY) * Math.max(1, this.height - this.insets.top - this.insets.bottom)
  }

  toX(u: number): number {
    return (u - this.cu) * this.xScale + this.centerX
  }

  toY(y: number): number {
    return (y - this.cy) * this.yScale + this.centerY
  }

  fromX(x: number): number {
    return (x - this.centerX) / this.xScale + this.cu
  }

  fromY(y: number): number {
    return (y - this.centerY) / this.yScale + this.cy
  }

  resize(width: number, height: number): void {
    this.width = width
    this.height = height
    this.clamp()
  }

  /** The view eases to new insets, so panels opening slide the timeline aside. */
  setInsets(insets: Insets): void {
    this.targetInsets = insets
  }

  private updateInsets(dt: number): boolean {
    let moving = false
    const k = 1 - Math.exp(-dt * 11)
    for (const side of ['top', 'bottom', 'left', 'right'] as const) {
      const d = this.targetInsets[side] - this.insets[side]
      if (d === 0) continue
      moving = true
      this.insets = { ...this.insets, [side]: Math.abs(d) < 0.2 ? this.targetInsets[side] : this.insets[side] + d * k }
    }
    return moving
  }

  /**
   * Keeps the data's full extent within reach. At zoom 1 both ranges collapse to 0.5,
   * so zooming out always settles exactly on the fitted view.
   */
  private clamp(): void {
    const z = this.zoom
    const halfU = 0.5 / z
    const slack = (1 - 1 / z) * 0.03
    this.cu = clampRange(this.cu, halfU - slack, 1 - halfU + slack)
    const halfY = 0.5 / Math.exp(this.logY)
    this.cy = clampRange(this.cy, halfY, 1 - halfY)
  }

  /** Multiplies the zoom by exp(delta), keeping the world point under (px, py) in place. */
  zoomAt(px: number, py: number, delta: number, axis: ZoomAxis = 'both', direct = false): void {
    this.fly = null
    this.velocity.x = this.velocity.y = 0
    this.zoomRate = direct ? 38 : 16
    if (!this.anchor || this.anchor.px !== px || this.anchor.py !== py) this.anchor = { px, py, u: this.fromX(px), y: this.fromY(py) }
    if (axis !== 'height') this.targetLogZoom = clampRange(this.targetLogZoom + delta, 0, this.maxLogZoom)
    if (axis !== 'time') this.targetLogY = clampRange(this.targetLogY + delta * (axis === 'both' ? Y_ZOOM_EXPONENT : 1), 0, this.maxLogY)
  }

  /** Shows exactly this stretch of the axis, at once, leaving height alone. */
  showTimeRange(v0: number, v1: number): void {
    this.fly = null
    this.anchor = null
    this.velocity.x = this.velocity.y = 0
    this.logZoom = clampRange(Math.log(1 / Math.max(1e-6, Math.abs(v1 - v0))), 0, this.maxLogZoom)
    this.targetLogZoom = this.logZoom
    this.targetLogY = this.logY
    this.cu = (v0 + v1) / 2
    this.clamp()
  }

  panBy(dx: number, dy: number): void {
    this.fly = null
    this.anchor = null
    this.targetLogZoom = this.logZoom
    this.targetLogY = this.logY
    this.cu -= dx / this.xScale
    this.cy -= dy / this.yScale
    this.clamp()
  }

  fling(vx: number, vy: number): void {
    this.velocity.x = vx
    this.velocity.y = vy
  }

  stop(): void {
    this.velocity.x = this.velocity.y = 0
    this.fly = null
    this.anchor = null
    this.targetLogZoom = this.logZoom
    this.targetLogY = this.logY
  }

  /**
   * Eased flight that pulls back when the destination is far, then settles in.
   * Height follows the usual ratio to time unless `logY` says otherwise.
   */
  flyTo(u: number, y: number, logZoom: number, reducedMotion = false, logY?: number): void {
    const z = clampRange(logZoom, 0, this.maxLogZoom)
    const to: [number, number, number, number] = [u, y, z, clampRange(logY ?? z * Y_ZOOM_EXPONENT, 0, this.maxLogY)]
    this.anchor = null
    this.velocity.x = this.velocity.y = 0
    if (reducedMotion) {
      ;[this.cu, this.cy, this.logZoom, this.logY] = to
      this.targetLogZoom = to[2]
      this.targetLogY = to[3]
      this.fly = null
      this.clamp()
      return
    }
    const distance = Math.abs(u - this.cu) * this.zoom
    const bump = Math.min(Math.log1p(distance) * 0.45, Math.max(this.logZoom, to[2]))
    this.fly = {
      t: 0,
      duration: 0.7 + Math.min(0.7, Math.log1p(distance) * 0.18),
      from: [this.cu, this.cy, this.logZoom, this.logY],
      to,
      bump,
    }
  }

  fit(reducedMotion = false): void {
    this.flyTo(0.5, 0.5, 0, reducedMotion, 0)
  }

  /** Advances animation. Returns true while anything is still moving. */
  update(dt: number): boolean {
    const insetsMoving = this.updateInsets(dt)
    if (this.fly) {
      const f = this.fly
      f.t = Math.min(1, f.t + dt / f.duration)
      const e = ease(f.t)
      this.cu = f.from[0] + (f.to[0] - f.from[0]) * e
      this.cy = f.from[1] + (f.to[1] - f.from[1]) * e
      this.logZoom = Math.max(0, f.from[2] + (f.to[2] - f.from[2]) * e - f.bump * Math.sin(Math.PI * e))
      this.logY = Math.max(0, f.from[3] + (f.to[3] - f.from[3]) * e)
      this.targetLogZoom = this.logZoom
      this.targetLogY = this.logY
      this.clamp()
      if (f.t >= 1) this.fly = null
      return true
    }

    let moving = false
    const gap = this.targetLogZoom - this.logZoom
    const gapY = this.targetLogY - this.logY
    if (Math.abs(gap) > 1e-4 || Math.abs(gapY) > 1e-4) {
      const k = this.instant ? 1 : 1 - Math.exp(-dt * this.zoomRate)
      this.logZoom += gap * k
      this.logY += gapY * k
      if (this.anchor) {
        this.cu = this.anchor.u - (this.anchor.px - this.centerX) / this.xScale
        this.cy = this.anchor.y - (this.anchor.py - this.centerY) / this.yScale
      }
      this.clamp()
      moving = true
    } else if (gap !== 0 || gapY !== 0) {
      this.logZoom = this.targetLogZoom
      this.logY = this.targetLogY
      this.anchor = null
      this.clamp()
      moving = true
    } else {
      this.anchor = null
    }

    const speed = Math.hypot(this.velocity.x, this.velocity.y)
    if (speed > 6) {
      this.cu -= (this.velocity.x * dt) / this.xScale
      this.cy -= (this.velocity.y * dt) / this.yScale
      const decay = Math.exp(-dt * 5)
      this.velocity.x *= decay
      this.velocity.y *= decay
      this.clamp()
      moving = true
    } else {
      this.velocity.x = this.velocity.y = 0
    }
    return moving || insetsMoving
  }

  get animating(): boolean {
    return this.fly !== null
  }
}

function clampRange(value: number, a: number, b: number): number {
  if (a > b) return (a + b) / 2
  return Math.min(b, Math.max(a, value))
}
