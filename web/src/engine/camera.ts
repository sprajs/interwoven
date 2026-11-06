/**
 * View over the normalised (u, y) plane. Time zooms faster than the vertical axis,
 * so lanes grow taller as you zoom without nodes running away from each other.
 */
const Y_ZOOM_EXPONENT = 0.55

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
  insets: Insets = { top: 112, bottom: 84, left: 56, right: 56 }
  cu = 0.5
  cy = 0.5
  logZoom = 0
  maxLogZoom = Math.log(220)

  private targetInsets: Insets = this.insets
  private targetLogZoom = 0
  private anchor: { px: number; py: number; u: number; y: number } | null = null
  private velocity = { x: 0, y: 0 }
  private fly: {
    t: number
    duration: number
    from: [number, number, number]
    to: [number, number, number]
    bump: number
  } | null = null

  get zoom(): number {
    return Math.exp(this.logZoom)
  }

  get xScale(): number {
    return this.scaleX(this.logZoom)
  }

  get yScale(): number {
    return this.scaleY(this.logZoom)
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

  private scaleY(logZoom: number): number {
    return Math.exp(logZoom * Y_ZOOM_EXPONENT) * Math.max(1, this.height - this.insets.top - this.insets.bottom)
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
    const halfY = 0.5 / Math.exp(this.logZoom * Y_ZOOM_EXPONENT)
    this.cy = clampRange(this.cy, halfY, 1 - halfY)
  }

  /** Multiplies the zoom by exp(delta), keeping the world point under (px, py) in place. */
  zoomAt(px: number, py: number, delta: number): void {
    this.fly = null
    this.velocity.x = this.velocity.y = 0
    this.anchor ??= { px, py, u: this.fromX(px), y: this.fromY(py) }
    if (this.anchor.px !== px || this.anchor.py !== py) this.anchor = { px, py, u: this.fromX(px), y: this.fromY(py) }
    this.targetLogZoom = clampRange(this.targetLogZoom + delta, 0, this.maxLogZoom)
  }

  panBy(dx: number, dy: number): void {
    this.fly = null
    this.anchor = null
    this.targetLogZoom = this.logZoom
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
  }

  /** Eased flight that pulls back when the destination is far, then settles in. */
  flyTo(u: number, y: number, logZoom: number, reducedMotion = false): void {
    const to: [number, number, number] = [u, y, clampRange(logZoom, 0, this.maxLogZoom)]
    this.anchor = null
    this.velocity.x = this.velocity.y = 0
    if (reducedMotion) {
      ;[this.cu, this.cy, this.logZoom] = to
      this.targetLogZoom = to[2]
      this.fly = null
      this.clamp()
      return
    }
    const distance = Math.abs(u - this.cu) * this.zoom
    const bump = Math.min(Math.log1p(distance) * 0.45, Math.max(this.logZoom, to[2]))
    this.fly = {
      t: 0,
      duration: 0.7 + Math.min(0.7, Math.log1p(distance) * 0.18),
      from: [this.cu, this.cy, this.logZoom],
      to,
      bump,
    }
  }

  fit(reducedMotion = false): void {
    this.flyTo(0.5, 0.5, 0, reducedMotion)
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
      this.targetLogZoom = this.logZoom
      this.clamp()
      if (f.t >= 1) this.fly = null
      return true
    }

    let moving = false
    const gap = this.targetLogZoom - this.logZoom
    if (Math.abs(gap) > 1e-4) {
      this.logZoom += gap * (1 - Math.exp(-dt * 16))
      if (this.anchor) {
        this.cu = this.anchor.u - (this.anchor.px - this.centerX) / this.xScale
        this.cy = this.anchor.y - (this.anchor.py - this.centerY) / this.yScale
      }
      this.clamp()
      moving = true
    } else if (gap !== 0) {
      this.logZoom = this.targetLogZoom
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
