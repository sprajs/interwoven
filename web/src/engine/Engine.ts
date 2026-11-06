import { SHAPE_BY_TYPE, walk, type Model } from '../data/model.ts'
import { Camera, type Insets } from './camera.ts'
import { createDataTexture, createProgram, createTarget, deleteTarget, type Program, type Target } from './gl.ts'
import { drawOverlay } from './overlay.ts'
import * as S from './shaders.ts'

export type Mode = 'network' | 'density' | 'steps'

export interface ViewState {
  mode: Mode
  hiddenDomains: ReadonlySet<string>
  hiddenTypes: ReadonlySet<string>
  activeLabels: ReadonlySet<string>
  selected: number | null
  compressed: boolean
}

export interface EngineCallbacks {
  onHover(index: number | null, x: number, y: number): void
  onSelect(index: number | null): void
  onFrame(engine: Engine): void
  onFatal(message: string): void
}

/** Zoom factor at which each level has fully appeared, on the compressed time scale. */
const REVEAL_ZOOM = [0, 0, 1.75, 3.4]
/** Linear time packs the recent past into a sliver, so levels appear later there. */
const LINEAR_REVEAL_FACTOR = 8
const BLOOM_LEVELS = 4
const BG = [0.02, 0.028, 0.051] as const
const MODE_MIX: Record<Mode, { haze: number; nodes: number; edges: number; bloom: number; contours: number; beams: number }> = {
  network: { haze: 0.2, nodes: 1, edges: 1, bloom: 0.7, contours: 0, beams: 0 },
  density: { haze: 0.85, nodes: 0.55, edges: 0.16, bloom: 0.3, contours: 1, beams: 0 },
  steps: { haze: 0.14, nodes: 1, edges: 0.75, bloom: 0.85, contours: 0, beams: 1 },
}

export class Engine {
  readonly camera = new Camera()
  model: Model | null = null
  view: ViewState = {
    mode: 'network',
    hiddenDomains: new Set(),
    hiddenTypes: new Set(),
    activeLabels: new Set(),
    selected: null,
    compressed: true,
  }
  hovered: number | null = null
  pointer: { x: number; y: number } | null = null
  warp = 1
  dpr = 1
  /** Current per-node state: match, dim, boost, force. */
  state = new Float32Array(0)
  reveal = [1, 1, 0, 0]
  mix = { ...MODE_MIX.network }
  /** Emphasised nodes, ordered closest first, so their labels are placed before others. */
  emphasis: number[] = []
  labelAlpha = new Float32Array(0)
  uLinear = new Float32Array(0)
  uCompressed = new Float32Array(0)
  frameMs = 0
  drawCalls = 0

  private gl!: WebGL2RenderingContext
  private programs!: Record<'node' | 'edge' | 'density' | 'rect' | 'haze' | 'down' | 'up' | 'composite', Program>
  private quad!: WebGLBuffer
  private nodeVao!: WebGLVertexArrayObject
  private fsVao!: WebGLVertexArrayObject
  private rectVao!: WebGLVertexArrayObject
  private rectBuffer!: WebGLBuffer
  private rectData = new Float32Array(9 * 400)
  private edgeVao: WebGLVertexArrayObject | null = null
  private edgeVertCount = 0
  private texA: WebGLTexture | null = null
  private texB: WebGLTexture | null = null
  private texState: WebGLTexture | null = null
  private texHeight = 1
  private floatTargets = false
  private scene: Target | null = null
  private densityTarget: Target | null = null
  private bloomChain: Target[] = []
  private targetState = new Float32Array(0)
  private stateUpload = new Float32Array(0)
  private stateDirty = true
  private raf = 0
  private lastTime = 0
  private reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches
  private drag: { id: number; x: number; y: number; t: number; vx: number; vy: number; moved: number } | null = null
  private pinch = new Map<number, { x: number; y: number }>()
  private pinchDistance = 0
  private readonly overlayCtx: CanvasRenderingContext2D
  private readonly observer: ResizeObserver
  private readonly callbacks: EngineCallbacks
  private readonly canvas: HTMLCanvasElement
  readonly overlay: HTMLCanvasElement
  private readonly hazeNorm = { kernel: 40, gain: 1 }

  constructor(canvas: HTMLCanvasElement, overlay: HTMLCanvasElement, callbacks: EngineCallbacks) {
    this.canvas = canvas
    this.overlay = overlay
    this.callbacks = callbacks
    this.overlayCtx = overlay.getContext('2d')!
    this.initGL()

    canvas.addEventListener('webglcontextlost', this.onContextLost)
    canvas.addEventListener('webglcontextrestored', this.onContextRestored)
    overlay.addEventListener('wheel', this.onWheel, { passive: false })
    overlay.addEventListener('pointerdown', this.onPointerDown)
    overlay.addEventListener('pointermove', this.onPointerMove)
    overlay.addEventListener('pointerup', this.onPointerUp)
    overlay.addEventListener('pointercancel', this.onPointerUp)
    overlay.addEventListener('pointerleave', this.onPointerLeave)
    overlay.addEventListener('dblclick', this.onDoubleClick)

    this.observer = new ResizeObserver(() => this.resize())
    this.observer.observe(canvas.parentElement!)
    this.resize()
  }

  dispose(): void {
    cancelAnimationFrame(this.raf)
    this.raf = 0
    this.observer.disconnect()
    this.canvas.removeEventListener('webglcontextlost', this.onContextLost)
    this.canvas.removeEventListener('webglcontextrestored', this.onContextRestored)
    this.overlay.removeEventListener('wheel', this.onWheel)
    this.overlay.removeEventListener('pointerdown', this.onPointerDown)
    this.overlay.removeEventListener('pointermove', this.onPointerMove)
    this.overlay.removeEventListener('pointerup', this.onPointerUp)
    this.overlay.removeEventListener('pointercancel', this.onPointerUp)
    this.overlay.removeEventListener('pointerleave', this.onPointerLeave)
    this.overlay.removeEventListener('dblclick', this.onDoubleClick)
  }

  // ---------------------------------------------------------------- setup

  private initGL(): void {
    const gl = this.canvas.getContext('webgl2', { alpha: false, antialias: false, powerPreference: 'high-performance' })
    if (!gl) {
      this.callbacks.onFatal('This app needs WebGL 2, which this browser or device does not provide.')
      return
    }
    this.gl = gl
    this.floatTargets = !!gl.getExtension('EXT_color_buffer_float')
    this.programs = {
      node: createProgram(gl, S.NODE_VS, S.NODE_FS),
      edge: createProgram(gl, S.EDGE_VS, S.EDGE_FS),
      density: createProgram(gl, S.DENSITY_VS, S.DENSITY_FS),
      rect: createProgram(gl, S.RECT_VS, S.RECT_FS),
      haze: createProgram(gl, S.HAZE_VS, S.HAZE_FS),
      down: createProgram(gl, S.BLOOM_DOWN_VS, S.BLOOM_DOWN_FS),
      up: createProgram(gl, S.BLOOM_UP_VS, S.BLOOM_UP_FS),
      composite: createProgram(gl, S.COMPOSITE_VS, S.COMPOSITE_FS),
    }
    this.quad = gl.createBuffer()!
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)

    this.nodeVao = gl.createVertexArray()!
    gl.bindVertexArray(this.nodeVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)

    this.fsVao = gl.createVertexArray()!
    gl.bindVertexArray(this.fsVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)

    this.rectVao = gl.createVertexArray()!
    gl.bindVertexArray(this.rectVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)
    this.rectBuffer = gl.createBuffer()!
    gl.bindBuffer(gl.ARRAY_BUFFER, this.rectBuffer)
    gl.bufferData(gl.ARRAY_BUFFER, this.rectData.byteLength, gl.DYNAMIC_DRAW)
    const stride = 9 * 4
    gl.enableVertexAttribArray(1)
    gl.vertexAttribPointer(1, 4, gl.FLOAT, false, stride, 0)
    gl.vertexAttribDivisor(1, 1)
    gl.enableVertexAttribArray(2)
    gl.vertexAttribPointer(2, 4, gl.FLOAT, false, stride, 16)
    gl.vertexAttribDivisor(2, 1)
    gl.enableVertexAttribArray(3)
    gl.vertexAttribPointer(3, 1, gl.FLOAT, false, stride, 32)
    gl.vertexAttribDivisor(3, 1)
    gl.bindVertexArray(null)
    gl.disable(gl.DEPTH_TEST)
  }

  private createTargets(): void {
    const gl = this.gl
    deleteTarget(gl, this.scene)
    deleteTarget(gl, this.densityTarget)
    this.bloomChain.forEach((t) => deleteTarget(gl, t))
    this.bloomChain = []
    const w = Math.max(1, this.canvas.width)
    const h = Math.max(1, this.canvas.height)
    const internal = this.floatTargets ? gl.RGBA16F : gl.RGBA8
    const type = this.floatTargets ? gl.HALF_FLOAT : gl.UNSIGNED_BYTE
    const make = (tw: number, th: number) => createTarget(gl, Math.max(1, tw), Math.max(1, th), internal, gl.RGBA, type)
    this.scene = make(w, h)
    this.densityTarget = make(Math.ceil(w / 3), Math.ceil(h / 3))
    for (let i = 1; i <= BLOOM_LEVELS; i++) this.bloomChain.push(make(w >> i, h >> i))
  }

  private uploadModel(): void {
    const gl = this.gl
    const model = this.model
    if (!model || !gl) return
    const n = Math.max(1, model.n)
    const height = Math.ceil(n / S.TEX_WIDTH)
    this.texHeight = height
    const a = new Float32Array(S.TEX_WIDTH * height * 4)
    const b = new Float32Array(S.TEX_WIDTH * height * 4)
    model.nodes.forEach((node, i) => {
      const lane = model.lanes[model.domainIndex[i]!]!
      a.set([node.year, model.y[i]!, model.radius[i]!, SHAPE_BY_TYPE.get(node.type) ?? 0], i * 4)
      b.set([lane.rgb[0], lane.rgb[1], lane.rgb[2], node.level], i * 4)
    })
    if (this.texA) gl.deleteTexture(this.texA)
    if (this.texB) gl.deleteTexture(this.texB)
    if (this.texState) gl.deleteTexture(this.texState)
    this.texA = createDataTexture(gl, S.TEX_WIDTH, height, a)
    this.texB = createDataTexture(gl, S.TEX_WIDTH, height, b)
    this.texState = createDataTexture(gl, S.TEX_WIDTH, height, new Float32Array(S.TEX_WIDTH * height * 4))
    this.stateDirty = true

    const edges = model.edges
    const segments = edges.length < 6000 ? 36 : edges.length < 40000 ? 18 : 9
    const verts = new Float32Array((segments + 1) * 4)
    for (let i = 0; i <= segments; i++) verts.set([i / segments, -1, i / segments, 1], i * 4)
    this.edgeVertCount = (segments + 1) * 2
    const ids = new Uint32Array(edges.length * 2)
    const soft = new Float32Array(edges.length)
    edges.forEach((e, i) => {
      ids[i * 2] = e.source
      ids[i * 2 + 1] = e.target
      soft[i] = e.soft ? 1 : 0
    })
    if (this.edgeVao) gl.deleteVertexArray(this.edgeVao)
    this.edgeVao = gl.createVertexArray()!
    gl.bindVertexArray(this.edgeVao)
    const vb = gl.createBuffer()!
    gl.bindBuffer(gl.ARRAY_BUFFER, vb)
    gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)
    const ib = gl.createBuffer()!
    gl.bindBuffer(gl.ARRAY_BUFFER, ib)
    gl.bufferData(gl.ARRAY_BUFFER, ids, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(1)
    gl.vertexAttribIPointer(1, 2, gl.UNSIGNED_INT, 0, 0)
    gl.vertexAttribDivisor(1, 1)
    const sb = gl.createBuffer()!
    gl.bindBuffer(gl.ARRAY_BUFFER, sb)
    gl.bufferData(gl.ARRAY_BUFFER, soft, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(2)
    gl.vertexAttribPointer(2, 1, gl.FLOAT, false, 0, 0)
    gl.vertexAttribDivisor(2, 1)
    gl.bindVertexArray(null)
  }

  // ---------------------------------------------------------------- data and view

  setModel(model: Model): void {
    this.model = model
    this.state = new Float32Array(model.n * 4)
    this.targetState = new Float32Array(model.n * 4)
    this.labelAlpha = new Float32Array(model.n)
    this.uLinear = Float32Array.from(model.nodes, (node) => model.time.linear(node.year))
    this.uCompressed = Float32Array.from(model.nodes, (node) => model.time.compressed(node.year))
    // Keep total haze energy comparable between small and huge datasets.
    this.hazeNorm.kernel = 44 * Math.pow(290 / Math.max(290, model.n), 0.18)
    this.hazeNorm.gain = Math.pow(290 / Math.max(290, model.n), 0.62)
    this.uploadModel()
    this.computeTargets()
    this.state.set(this.targetState)
    this.stateDirty = true
    this.invalidate()
  }

  setView(next: Partial<ViewState>): void {
    const prev = this.view
    this.view = { ...prev, ...next }
    if (next.compressed !== undefined && next.compressed !== prev.compressed) {
      this.camera.maxLogZoom = Math.log(next.compressed ? 220 : 1500)
      this.camera.fit(this.reducedMotion)
    }
    this.computeTargets()
    this.invalidate()
  }

  setInsets(insets: Insets): void {
    this.camera.setInsets(insets)
    this.invalidate()
  }

  passesFilters(i: number): boolean {
    const model = this.model!
    const node = model.nodes[i]!
    const { hiddenDomains, hiddenTypes, activeLabels } = this.view
    if (hiddenDomains.has(node.domain) || hiddenTypes.has(node.type)) return false
    if (activeLabels.size > 0 && !node.labels.some((l) => activeLabels.has(l))) return false
    return true
  }

  /** Works out the state each node should animate toward from filters, mode and focus. */
  private computeTargets(): void {
    const model = this.model
    if (!model) return
    const { mode, selected } = this.view
    const target = this.targetState
    const focus = selected ?? this.hovered
    const isHover = selected === null && this.hovered !== null
    const stepMode = mode === 'steps'
    const stepSet = stepMode ? new Set(model.stepChanges) : null

    let hops: Map<number, number> | null = null
    this.emphasis = []
    if (focus !== null) {
      const maxHops = isHover ? 2 : 32
      const up = walk(focus, model.parents, isHover ? 1 : maxHops)
      const down = walk(focus, model.children, maxHops)
      hops = up
      for (const [i, h] of down) hops.set(i, Math.min(h, hops.get(i) ?? Infinity))
      this.emphasis = [...hops.keys()].sort((a, b) => hops!.get(a)! - hops!.get(b)!)
    }

    for (let i = 0; i < model.n; i++) {
      const o = i * 4
      const match = this.passesFilters(i) ? 1 : 0
      let dim = 0
      let boost = 0
      let force = 0
      if (hops) {
        const h = hops.get(i)
        if (h === undefined) {
          dim = isHover ? 0.68 : 0.94
        } else {
          boost = h === 0 ? 1 : h === 1 ? 0.72 : h === 2 ? 0.34 : 0.14
          if (isHover) boost *= 0.8
          force = h <= (isHover ? 1 : 2) ? 1 : 0
        }
      } else if (stepSet) {
        if (stepSet.has(i)) {
          boost = 0.4
          force = 1
        } else {
          dim = 0.72
        }
      }
      target[o] = match
      target[o + 1] = dim
      target[o + 2] = boost
      target[o + 3] = force
    }
  }

  private animateState(dt: number): boolean {
    const n = this.state.length
    const k = this.reducedMotion ? 1 : 1 - Math.exp(-dt * 10)
    let changed = false
    const cur = this.state
    const tgt = this.targetState
    for (let i = 0; i < n; i++) {
      const d = tgt[i]! - cur[i]!
      if (d === 0) continue
      changed = true
      cur[i] = Math.abs(d) < 0.002 ? tgt[i]! : cur[i]! + d * k
    }
    if (changed) this.stateDirty = true
    return changed
  }

  private animateMix(dt: number): boolean {
    const goal = MODE_MIX[this.view.mode]
    const k = this.reducedMotion ? 1 : 1 - Math.exp(-dt * 6)
    let changed = false
    const mix = this.mix as Record<string, number>
    for (const key of Object.keys(goal) as (keyof typeof goal)[]) {
      const d = goal[key] - mix[key]!
      if (d === 0) continue
      changed = true
      mix[key] = Math.abs(d) < 0.002 ? goal[key] : mix[key]! + d * k
    }
    const warpGoal = this.view.compressed ? 1 : 0
    const dw = warpGoal - this.warp
    if (dw !== 0) {
      changed = true
      this.warp = Math.abs(dw) < 0.001 ? warpGoal : this.warp + dw * (this.reducedMotion ? 1 : 1 - Math.exp(-dt * 5))
    }
    return changed
  }

  // ---------------------------------------------------------------- geometry

  nodeU(i: number): number {
    const w = this.warp
    return this.uLinear[i]! * (1 - w) + this.uCompressed[i]! * w
  }

  /** Reveal strength 0..1 per level at the current zoom. */
  private computeReveal(): void {
    const factor = LINEAR_REVEAL_FACTOR + (1 - LINEAR_REVEAL_FACTOR) * this.warp
    const lz = this.camera.logZoom
    for (let level = 0; level < 4; level++) {
      const threshold = REVEAL_ZOOM[level]!
      if (threshold === 0) {
        this.reveal[level] = 1
        continue
      }
      const at = Math.log(threshold * factor)
      const t = Math.min(1, Math.max(0, (lz - (at - 0.42)) / 0.42))
      this.reveal[level] = t * t * (3 - 2 * t)
    }
  }

  /** How many of the four levels are currently showing, for the depth indicator. */
  revealZoomFor(level: number): number {
    const factor = LINEAR_REVEAL_FACTOR + (1 - LINEAR_REVEAL_FACTOR) * this.warp
    return (REVEAL_ZOOM[level] ?? 0) * factor
  }

  nodeVisibility(i: number): number {
    const level = this.model!.nodes[i]!.level
    const o = i * 4
    return this.state[o]! * Math.max(this.reveal[level] ?? 1, this.state[o + 3]!)
  }

  pick(x: number, y: number): number | null {
    const model = this.model
    if (!model) return null
    const cam = this.camera
    const xs = cam.xScale
    const ys = cam.yScale
    const cx = cam.centerX
    const cy = cam.centerY
    let best: number | null = null
    let bestScore = Infinity
    for (let i = 0; i < model.n; i++) {
      if (this.state[i * 4]! < 0.5 || this.state[i * 4 + 1]! > 0.8) continue
      const px = (this.nodeU(i) - cam.cu) * xs + cx
      const py = (model.y[i]! - cam.cy) * ys + cy
      const dx = px - x
      const dy = py - y
      const r = model.radius[i]! + 7
      const d2 = dx * dx + dy * dy
      if (d2 > r * r) continue
      const score = d2 / (r * r) - (3 - model.nodes[i]!.level) * 0.05
      if (score < bestScore) {
        bestScore = score
        best = i
      }
    }
    return best
  }

  // ---------------------------------------------------------------- navigation

  flyToNode(i: number): void {
    const model = this.model
    if (!model) return
    const level = model.nodes[i]!.level
    const needed = this.revealZoomFor(level)
    const lz = Math.max(this.camera.logZoom, needed > 0 ? Math.log(needed * 1.25) : 0, 0.6)
    this.camera.flyTo(this.nodeU(i), model.y[i]!, lz, this.reducedMotion)
    this.invalidate()
  }

  /** Fits a span of years centred in the view. */
  flyToYears(start: number, end: number): void {
    const model = this.model
    if (!model) return
    const a = model.time.u(start, this.warp)
    const b = model.time.u(end, this.warp)
    const zoom = 1 / Math.max(1e-5, b - a)
    this.camera.flyTo((a + b) / 2, this.camera.cy, Math.log(Math.max(1, zoom)), this.reducedMotion)
    this.invalidate()
  }

  fit(): void {
    this.camera.fit(this.reducedMotion)
    this.invalidate()
  }

  zoomBy(factor: number): void {
    this.camera.zoomAt(this.camera.centerX, this.camera.centerY, Math.log(factor))
    this.invalidate()
  }

  /** Moves the view so `u` is centred, for the overview strip. */
  panToU(u: number): void {
    const cam = this.camera
    cam.panBy((cam.cu - u) * cam.xScale, 0)
    this.invalidate()
  }

  invalidate(): void {
    if (!this.raf) {
      this.lastTime = 0
      this.raf = requestAnimationFrame(this.frame)
    }
  }

  // ---------------------------------------------------------------- input

  private localPoint(e: { clientX: number; clientY: number }): { x: number; y: number } {
    const rect = this.overlay.getBoundingClientRect()
    return { x: e.clientX - rect.left, y: e.clientY - rect.top }
  }

  private onWheel = (e: WheelEvent): void => {
    e.preventDefault()
    const { x, y } = this.localPoint(e)
    const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 100 : 1
    const dy = e.deltaY * unit
    const dx = e.deltaX * unit
    // Pinch arrives as ctrl+wheel. Trackpad scrolling has fine, often two-axis deltas;
    // a notched mouse wheel has large, single-axis ones and should zoom.
    const isPinch = e.ctrlKey || e.metaKey
    const isMouseWheel = !isPinch && dx === 0 && Math.abs(dy) >= 50 && Number.isInteger(dy)
    if (isPinch) this.camera.zoomAt(x, y, -dy * 0.012)
    else if (isMouseWheel) this.camera.zoomAt(x, y, -dy * 0.0024)
    else if (e.shiftKey) this.camera.panBy(-dy - dx, 0)
    else this.camera.panBy(-dx, -dy)
    this.setHover(null, 0, 0)
    this.invalidate()
  }

  private onPointerDown = (e: PointerEvent): void => {
    const p = this.localPoint(e)
    this.pinch.set(e.pointerId, p)
    this.overlay.setPointerCapture(e.pointerId)
    this.camera.stop()
    if (this.pinch.size === 2) {
      const [a, b] = [...this.pinch.values()]
      this.pinchDistance = Math.hypot(a!.x - b!.x, a!.y - b!.y)
      this.drag = null
      return
    }
    this.drag = { id: e.pointerId, x: p.x, y: p.y, t: e.timeStamp, vx: 0, vy: 0, moved: 0 }
    this.overlay.style.cursor = 'grabbing'
  }

  private onPointerMove = (e: PointerEvent): void => {
    const p = this.localPoint(e)
    this.pointer = p
    if (this.pinch.has(e.pointerId)) this.pinch.set(e.pointerId, p)

    if (this.pinch.size === 2) {
      const [a, b] = [...this.pinch.values()]
      const distance = Math.hypot(a!.x - b!.x, a!.y - b!.y)
      if (this.pinchDistance > 0) {
        this.camera.zoomAt((a!.x + b!.x) / 2, (a!.y + b!.y) / 2, Math.log(distance / this.pinchDistance))
      }
      this.pinchDistance = distance
      this.invalidate()
      return
    }

    if (this.drag && this.drag.id === e.pointerId) {
      const d = this.drag
      const dx = p.x - d.x
      const dy = p.y - d.y
      const dt = Math.max(1, e.timeStamp - d.t) / 1000
      d.vx = d.vx * 0.7 + (dx / dt) * 0.3
      d.vy = d.vy * 0.7 + (dy / dt) * 0.3
      d.x = p.x
      d.y = p.y
      d.t = e.timeStamp
      d.moved += Math.abs(dx) + Math.abs(dy)
      if (d.moved > 3) {
        this.camera.panBy(dx, dy)
        this.setHover(null, 0, 0)
      }
      this.invalidate()
      return
    }

    if (e.pointerType === 'touch') return
    const hit = this.pick(p.x, p.y)
    this.setHover(hit, p.x, p.y)
    this.overlay.style.cursor = hit === null ? 'grab' : 'pointer'
    if (this.view.mode === 'density') this.invalidate()
  }

  private onPointerUp = (e: PointerEvent): void => {
    const wasPinching = this.pinch.size >= 2
    this.pinch.delete(e.pointerId)
    if (this.pinch.size < 2) this.pinchDistance = 0
    this.overlay.style.cursor = 'grab'
    const d = this.drag
    if (!d || d.id !== e.pointerId || wasPinching) return
    this.drag = null
    if (d.moved <= 3) {
      const p = this.localPoint(e)
      const hit = this.pick(p.x, p.y)
      // Touch has no hover, so a tap needs its own hit test; empty space clears selection.
      this.callbacks.onSelect(hit)
    } else if (!this.reducedMotion && e.timeStamp - d.t < 80) {
      this.camera.fling(d.vx, d.vy)
      this.invalidate()
    }
  }

  private onPointerLeave = (): void => {
    this.pointer = null
    this.setHover(null, 0, 0)
    this.invalidate()
  }

  private onDoubleClick = (e: MouseEvent): void => {
    const { x, y } = this.localPoint(e)
    this.camera.zoomAt(x, y, Math.log(2))
    this.invalidate()
  }

  private setHover(index: number | null, x: number, y: number): void {
    if (index === this.hovered) return
    this.hovered = index
    this.callbacks.onHover(index, x, y)
    this.computeTargets()
    this.invalidate()
  }

  // ---------------------------------------------------------------- frame

  resize(): void {
    const parent = this.canvas.parentElement
    if (!parent || !this.gl) return
    const width = parent.clientWidth
    const height = parent.clientHeight
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    if (this.camera.width === width && this.camera.height === height && this.dpr === dpr && this.scene) return
    this.dpr = dpr
    for (const c of [this.canvas, this.overlay]) {
      c.width = Math.max(1, Math.round(width * dpr))
      c.height = Math.max(1, Math.round(height * dpr))
      c.style.width = `${width}px`
      c.style.height = `${height}px`
    }
    this.camera.resize(width, height)
    this.createTargets()
    this.invalidate()
  }

  private frame = (time: number): void => {
    this.raf = 0
    const dt = this.lastTime ? Math.min(0.05, (time - this.lastTime) / 1000) : 1 / 60
    this.lastTime = time
    const start = performance.now()

    const cameraMoving = this.camera.update(dt)
    const stateMoving = this.animateState(dt)
    const mixMoving = this.animateMix(dt)
    const flowing = !this.reducedMotion && (this.view.selected !== null || this.hovered !== null)
    this.computeReveal()

    if (this.model && this.gl && !this.gl.isContextLost()) {
      this.render(time)
      this.drawCalls = drawOverlay(this, this.overlayCtx, dt)
      this.callbacks.onFrame(this)
    }
    this.frameMs = performance.now() - start

    const labelsMoving = this.labelsAnimating
    if (cameraMoving || stateMoving || mixMoving || flowing || labelsMoving) {
      this.raf = requestAnimationFrame(this.frame)
    } else {
      this.lastTime = 0
    }
  }

  /** Set by the overlay while any label is still fading. */
  labelsAnimating = false

  private setWorldUniforms(p: Program, width: number, height: number): void {
    const gl = this.gl
    const cam = this.camera
    const dpr = this.dpr
    const model = this.model!
    gl.uniform2f(p.u.uRes!, width, height)
    gl.uniform2f(p.u.uCam!, cam.cu, cam.cy)
    gl.uniform2f(p.u.uScale!, cam.xScale * dpr, cam.yScale * dpr)
    gl.uniform2f(p.u.uCenter!, cam.centerX * dpr, cam.centerY * dpr)
    gl.uniform4f(p.u.uTimeScale!, model.time.min, model.time.now, model.time.tau, model.time.logSpan)
    gl.uniform1f(p.u.uWarp!, this.warp)
    if (p.u.uDpr) gl.uniform1f(p.u.uDpr, dpr)
    if (p.u.uReveal) gl.uniform4f(p.u.uReveal, this.reveal[0]!, this.reveal[1]!, this.reveal[2]!, this.reveal[3]!)
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, this.texA)
    if (p.u.uNodeA) gl.uniform1i(p.u.uNodeA, 0)
    gl.activeTexture(gl.TEXTURE1)
    gl.bindTexture(gl.TEXTURE_2D, this.texB)
    if (p.u.uNodeB) gl.uniform1i(p.u.uNodeB, 1)
    gl.activeTexture(gl.TEXTURE2)
    gl.bindTexture(gl.TEXTURE_2D, this.texState)
    if (p.u.uState) gl.uniform1i(p.u.uState, 2)
    gl.activeTexture(gl.TEXTURE0)
  }

  private uploadState(): void {
    if (!this.stateDirty) return
    this.stateDirty = false
    const gl = this.gl
    const model = this.model!
    if (model.n === 0) return
    gl.activeTexture(gl.TEXTURE2)
    gl.bindTexture(gl.TEXTURE_2D, this.texState)
    const rows = this.texHeight
    const size = S.TEX_WIDTH * rows * 4
    if (this.stateUpload.length !== size) this.stateUpload = new Float32Array(size)
    this.stateUpload.set(this.state)
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, S.TEX_WIDTH, rows, gl.RGBA, gl.FLOAT, this.stateUpload)
    gl.activeTexture(gl.TEXTURE0)
  }

  private render(time: number): void {
    const gl = this.gl
    const model = this.model!
    const cam = this.camera
    const W = this.canvas.width
    const H = this.canvas.height
    const dpr = this.dpr
    const P = this.programs
    const mix = this.mix

    this.uploadState()

    // Density field, drawn from every node regardless of zoom. In the network view it
    // appears as a faint haze hinting at what zooming in will reveal.
    const showHaze = mix.haze > 0.005 && model.n > 0
    if (showHaze) {
      const t = this.densityTarget!
      gl.bindFramebuffer(gl.FRAMEBUFFER, t.fbo)
      gl.viewport(0, 0, t.width, t.height)
      gl.clearColor(0, 0, 0, 0)
      gl.clear(gl.COLOR_BUFFER_BIT)
      gl.enable(gl.BLEND)
      gl.blendFunc(gl.ONE, gl.ONE)
      gl.useProgram(P.density.handle)
      this.setWorldUniforms(P.density, W, H)
      const kernel = this.hazeNorm.kernel * dpr * Math.pow(cam.zoom, 0.38)
      gl.uniform1f(P.density.u.uKernel!, kernel)
      gl.bindVertexArray(this.nodeVao)
      gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, model.n)
    }

    gl.bindFramebuffer(gl.FRAMEBUFFER, this.scene!.fbo)
    gl.viewport(0, 0, W, H)
    gl.clearColor(BG[0], BG[1], BG[2], 1)
    gl.clear(gl.COLOR_BUFFER_BIT)
    gl.enable(gl.BLEND)

    this.drawBackdrop(W, H)

    if (showHaze) {
      gl.blendFunc(gl.ONE, gl.ONE)
      gl.useProgram(P.haze.handle)
      gl.activeTexture(gl.TEXTURE0)
      gl.bindTexture(gl.TEXTURE_2D, this.densityTarget!.tex)
      gl.uniform1i(P.haze.u.uTex!, 0)
      const gain = this.hazeNorm.gain * Math.pow(cam.zoom, 0.25 + 0.35 * mix.contours) * (0.5 - 0.08 * mix.contours)
      gl.uniform1f(P.haze.u.uGain!, gain)
      gl.uniform1f(P.haze.u.uIntensity!, mix.haze)
      if (P.haze.u.uContours) gl.uniform1f(P.haze.u.uContours, mix.contours)
      gl.bindVertexArray(this.fsVao)
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
    }

    if (this.edgeVao && model.edges.length) {
      gl.blendFunc(gl.ONE, gl.ONE)
      gl.useProgram(P.edge.handle)
      this.setWorldUniforms(P.edge, W, H)
      const base = Math.min(0.42, Math.max(0.05, 0.42 * Math.sqrt(450 / model.edges.length)))
      gl.uniform1f(P.edge.u.uEdgeAlpha!, base * mix.edges)
      gl.uniform1f(P.edge.u.uTimeS!, this.reducedMotion ? 0 : time / 1000)
      gl.bindVertexArray(this.edgeVao)
      gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, this.edgeVertCount, model.edges.length)
    }

    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)
    gl.useProgram(P.node.handle)
    this.setWorldUniforms(P.node, W, H)
    gl.uniform1f(P.node.u.uNodeAlpha!, mix.nodes)
    gl.uniform1i(P.node.u.uHover!, this.hovered ?? -1)
    gl.uniform1i(P.node.u.uSelected!, this.view.selected ?? -1)
    gl.bindVertexArray(this.nodeVao)
    gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, model.n)

    this.drawBloom()

    gl.bindFramebuffer(gl.FRAMEBUFFER, null)
    gl.viewport(0, 0, W, H)
    gl.disable(gl.BLEND)
    gl.useProgram(P.composite.handle)
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, this.scene!.tex)
    gl.uniform1i(P.composite.u.uScene!, 0)
    gl.activeTexture(gl.TEXTURE1)
    gl.bindTexture(gl.TEXTURE_2D, this.bloomChain[0]!.tex)
    gl.uniform1i(P.composite.u.uBloom!, 1)
    gl.uniform1f(P.composite.u.uBloomAmount!, mix.bloom)
    gl.bindVertexArray(this.fsVao)
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
    gl.activeTexture(gl.TEXTURE0)
    gl.bindVertexArray(null)
  }

  private drawBackdrop(W: number, H: number): void {
    const gl = this.gl
    const model = this.model!
    const cam = this.camera
    const dpr = this.dpr
    const time = model.time
    const data = this.rectData
    let count = 0
    const push = (x0: number, y0: number, x1: number, y1: number, r: number, g: number, b: number, a: number, kind = 0) => {
      if (count >= 400) return
      data.set([x0 * dpr, y0 * dpr, x1 * dpr, y1 * dpr, r, g, b, a, kind], count * 9)
      count++
    }
    const toX = (year: number) => cam.toX(time.u(year, this.warp))

    model.epochs.forEach((epoch, i) => {
      if (i % 2 === 0) return
      const x0 = Math.max(0, toX(epoch.start))
      const x1 = Math.min(cam.width, toX(epoch.end))
      if (x1 > x0) push(x0, 0, x1, cam.height, 0.5, 0.6, 0.85, 0.022)
    })

    for (const lane of model.lanes) {
      const y = cam.toY(lane.y0 - 0.006)
      if (lane.index > 0 && y > cam.insets.top - 40 && y < cam.height) {
        push(0, y - 0.5 / dpr, cam.width, y + 0.5 / dpr, 0.55, 0.65, 0.85, 0.055)
      }
    }

    if (this.mix.beams > 0.01) {
      for (const i of model.stepChanges) {
        if (!this.passesFilters(i)) continue
        const lane = model.lanes[model.domainIndex[i]!]!
        const x = cam.toX(this.nodeU(i))
        if (x < -40 || x > cam.width + 40) continue
        push(x - 26, cam.insets.top - 10, x + 26, cam.height, lane.rgb[0], lane.rgb[1], lane.rgb[2], 0.09 * this.mix.beams, 1)
      }
    }

    if (count === 0) return
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)
    gl.useProgram(this.programs.rect.handle)
    gl.uniform2f(this.programs.rect.u.uRes!, W, H)
    gl.bindVertexArray(this.rectVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, this.rectBuffer)
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, data.subarray(0, count * 9))
    gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, count)
  }

  private drawBloom(): void {
    const gl = this.gl
    const { down, up } = this.programs
    const chain = this.bloomChain
    gl.disable(gl.BLEND)
    gl.bindVertexArray(this.fsVao)
    gl.useProgram(down.handle)
    gl.activeTexture(gl.TEXTURE0)
    gl.uniform1i(down.u.uTex!, 0)
    let source = this.scene!
    chain.forEach((target, i) => {
      gl.bindFramebuffer(gl.FRAMEBUFFER, target.fbo)
      gl.viewport(0, 0, target.width, target.height)
      gl.bindTexture(gl.TEXTURE_2D, source.tex)
      gl.uniform2f(down.u.uTexel!, 1 / source.width, 1 / source.height)
      gl.uniform1f(down.u.uThreshold!, i === 0 ? 0.62 : 0)
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
      source = target
    })
    gl.enable(gl.BLEND)
    gl.blendFunc(gl.ONE, gl.ONE)
    gl.useProgram(up.handle)
    gl.uniform1i(up.u.uTex!, 0)
    for (let i = chain.length - 1; i > 0; i--) {
      const from = chain[i]!
      const to = chain[i - 1]!
      gl.bindFramebuffer(gl.FRAMEBUFFER, to.fbo)
      gl.viewport(0, 0, to.width, to.height)
      gl.bindTexture(gl.TEXTURE_2D, from.tex)
      gl.uniform2f(up.u.uTexel!, 0.5 / from.width, 0.5 / from.height)
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
    }
  }

  // ---------------------------------------------------------------- context loss

  private onContextLost = (e: Event): void => {
    e.preventDefault()
    cancelAnimationFrame(this.raf)
    this.raf = 0
  }

  private onContextRestored = (): void => {
    this.scene = null
    this.densityTarget = null
    this.bloomChain = []
    this.texA = this.texB = this.texState = null
    this.edgeVao = null
    this.initGL()
    this.createTargets()
    this.uploadModel()
    this.invalidate()
  }
}
