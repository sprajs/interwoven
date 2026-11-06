import { rowOrder, rowPositions, type RowOrder, type Story } from '../data/derive.ts'
import { documentedSpan } from '../data/lifecycle.ts'
import { nodeMarkStyle, walk, type Model } from '../data/model.ts'
import { hexUnit, INK, LAYOUT, PAPER as PAPER_HEX, RULE_ALPHA, UNIT } from '../design.ts'
import { Camera, type Insets, type ZoomAxis } from './camera.ts'
import { blendFolds, foldAroundYears, foldFromWindows, FoldMap, MAX_FOLD_POINTS, unfoldPleat, type Pleat } from './folds.ts'
import { createDataTexture, createProgram, type Program } from './gl.ts'
import { drawOverlay } from './overlay.ts'
import * as S from './shaders.ts'
import { LUT_SIZE, pickTicks } from './time.ts'
import { WheelClassifier, wheelNotches } from './wheel.ts'

export type Mode = 'threads' | 'story' | 'reach' | 'density'

export interface ViewState {
  mode: Mode
  hiddenKinds: ReadonlySet<string>
  activeLabels: ReadonlySet<string>
  selected: number | null
  compressed: boolean
  rowOrder: RowOrder
  /** The thread being followed, in the story view. */
  story: Story | null
  /** Entries matching what is typed in the search box, if anything is. */
  searchHits: ReadonlySet<number> | null
  /** A label being pointed at, shown as a preview without choosing it. */
  previewLabel: string | null
}

export interface EngineCallbacks {
  onHover(index: number | null, x: number, y: number): void
  onSelect(index: number | null): void
  /** A second click on an entry: follow its thread. */
  onFollow(index: number): void
  onFrame(engine: Engine): void
  /** The number of periods opened by hand changed. */
  onFolds(count: number): void
  onFatal(message: string): void
}

export const PAPER = hexUnit(PAPER_HEX)
const RULE_COLOR = hexUnit(INK.primary)
const HATCH_COLOR = hexUnit(INK.muted)
const PLEAT_TONE_ALPHA = 0.04
const PLEAT_FOLD_ALPHA = 0.13
const HATCH_ALPHA = 0.62
const MAX_RECTS = 1400
const HATCH_SPACING = UNIT / 2 + 0.5
const RATE_BINS = 512
const RATE_SMOOTHING = 7
const FOLD_SECONDS = 0.62
/** Periods that can be open at once. More than this stops being a comparison. */
const MAX_OPEN_PERIODS = 3
const MODE_MIX: Record<Mode, { hatching: number; nodes: number; edges: number; rules: number; weave: number; elbow: number }> = {
  threads: { hatching: 0, nodes: 1, edges: 0.85, rules: 1, weave: 0, elbow: 0 },
  story: { hatching: 0, nodes: 1, edges: 1, rules: 1, weave: 0, elbow: 1 },
  reach: { hatching: 0, nodes: 1, edges: 0.85, rules: 0.6, weave: 1, elbow: 0 },
  density: { hatching: 1, nodes: 0.75, edges: 0.1, rules: 0.5, weave: 0, elbow: 0 },
}

const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)

export class Engine {
  readonly camera = new Camera()
  model: Model | null = null
  view: ViewState = {
    mode: 'threads',
    hiddenKinds: new Set(),
    activeLabels: new Set(),
    selected: null,
    compressed: true,
    rowOrder: 'thread',
    story: null,
    searchHits: null,
    previewLabel: null,
  }
  hovered: number | null = null
  pointer: { x: number; y: number } | null = null
  warp = 1
  dpr = 1
  /** Where each entry currently sits, easing toward the layout the view asks for. */
  yNow = new Float32Array(0)
  /** A period being marked out on the ruler, in screen pixels. */
  bracket: { x0: number; x1: number } | null = null
  /** The current fold of the sheet. */
  foldNow = FoldMap.identity()
  /** Which part of the page the pointer is over. */
  pointerZone: 'ruler' | 'gutter' | 'chart' | null = null
  /** Current per-node state: match, faded, emphasised, forced visible. */
  state = new Float32Array(0)
  mix = { ...MODE_MIX.threads }
  /** Periods opened by hand, in years. */
  openPeriods: [number, number][] = []
  /** Emphasised nodes, closest first, so their text is placed before anything else. */
  emphasis: number[] = []
  labelAlpha = new Float32Array(0)
  uLinear = new Float32Array(0)
  uCompressed = new Float32Array(0)
  /** The ruler's cells in view, from the left: each runs from its year to the next cell's. */
  ticks: { year: number; x: number; odd: boolean }[] = []
  /** The boxes on the page, so that a name can be pointed at as well as its mark. */
  boxes: { i: number; x0: number; y0: number; x1: number; y1: number }[] = []
  frameMs = 0
  /** Set by the overlay while any text is still fading. */
  labelsAnimating = false

  private gl!: WebGL2RenderingContext
  private programs!: Record<'node' | 'edge' | 'span' | 'rect' | 'warp', Program>
  private quadVao!: WebGLVertexArrayObject
  private rectVao!: WebGLVertexArrayObject
  private rectBuffer!: WebGLBuffer
  private rectData = new Float32Array(8 * MAX_RECTS)
  private spanVao: WebGLVertexArrayObject | null = null
  private spanCount = 0
  private edgeVao: WebGLVertexArrayObject | null = null
  private edgeVertCount = 0
  private warpVao: WebGLVertexArrayObject | null = null
  private warpCount = 0
  private aData = new Float32Array(0)
  private aDirty = false
  private yGoal = new Float32Array(0)
  private rowsCache = new Map<RowOrder, { rows: Int32Array; y: Float32Array }>()
  private foldFrom = FoldMap.identity()
  private foldTo = FoldMap.identity()
  private foldT = 1
  private foldData = new Float32Array(MAX_FOLD_POINTS * 2)
  private foldCount = 0
  private wheelKind = new WheelClassifier()
  private lastTap = { index: -1, time: 0 }
  private pinchSpan = { x: 0, y: 0 }
  private texA: WebGLTexture | null = null
  private texB: WebGLTexture | null = null
  private texState: WebGLTexture | null = null
  private texLut: WebGLTexture | null = null
  private texHeight = 1
  private targetState = new Float32Array(0)
  private tickKey = ''
  private axisTicks: { year: number; v: number; odd: boolean }[] = []
  private rate = new Float32Array(RATE_BINS)
  private rateMax = 1
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

    this.camera.instant = this.reducedMotion
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
    gl.getExtension('EXT_color_buffer_float')
    this.programs = {
      node: createProgram(gl, S.NODE_VS, S.NODE_FS),
      edge: createProgram(gl, S.EDGE_VS, S.EDGE_FS),
      span: createProgram(gl, S.SPAN_VS, S.SPAN_FS),
      rect: createProgram(gl, S.RECT_VS, S.RECT_FS),
      warp: createProgram(gl, S.WARP_VS, S.WARP_FS),
    }
    const quad = gl.createBuffer()!
    gl.bindBuffer(gl.ARRAY_BUFFER, quad)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)

    this.quadVao = gl.createVertexArray()!
    gl.bindVertexArray(this.quadVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, quad)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)

    this.rectVao = gl.createVertexArray()!
    gl.bindVertexArray(this.rectVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, quad)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)
    this.rectBuffer = gl.createBuffer()!
    gl.bindBuffer(gl.ARRAY_BUFFER, this.rectBuffer)
    gl.bufferData(gl.ARRAY_BUFFER, this.rectData.byteLength, gl.DYNAMIC_DRAW)
    gl.enableVertexAttribArray(1)
    gl.vertexAttribPointer(1, 4, gl.FLOAT, false, 32, 0)
    gl.vertexAttribDivisor(1, 1)
    gl.enableVertexAttribArray(2)
    gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 32, 16)
    gl.vertexAttribDivisor(2, 1)
    gl.bindVertexArray(null)
    gl.disable(gl.DEPTH_TEST)
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
      a.set([node.year, this.yNow[i] ?? model.y[i]!, model.radius[i]!, nodeMarkStyle(node)], i * 4)
      b.set([model.ink[i * 3]!, model.ink[i * 3 + 1]!, model.ink[i * 3 + 2]!, node.level], i * 4)
    })
    this.aData = a
    if (this.texA) gl.deleteTexture(this.texA)
    if (this.texB) gl.deleteTexture(this.texB)
    if (this.texState) gl.deleteTexture(this.texState)
    this.texA = createDataTexture(gl, S.TEX_WIDTH, height, a)
    this.texB = createDataTexture(gl, S.TEX_WIDTH, height, b)
    this.texState = createDataTexture(gl, S.TEX_WIDTH, height, new Float32Array(S.TEX_WIDTH * height * 4))
    this.stateDirty = true

    const lut = new Float32Array(LUT_SIZE * 4)
    model.time.lut.forEach((u, i) => (lut[i * 4] = u))
    if (this.texLut) gl.deleteTexture(this.texLut)
    this.texLut = createDataTexture(gl, LUT_SIZE, 1, lut)

    const edges = model.edges
    const segments = edges.length < 6000 ? 48 : edges.length < 40000 ? 20 : 9
    const verts = new Float32Array((segments + 1) * 4)
    for (let i = 0; i <= segments; i++) verts.set([i / segments, -1, i / segments, 1], i * 4)
    this.edgeVertCount = (segments + 1) * 2
    const ids = new Uint32Array(edges.length * 2)
    const tentative = new Float32Array(edges.length)
    edges.forEach((e, i) => {
      ids[i * 2] = e.source
      ids[i * 2 + 1] = e.target
      tentative[i] = e.tentative ? 1 : 0
    })
    if (this.edgeVao) gl.deleteVertexArray(this.edgeVao)
    this.edgeVao = gl.createVertexArray()!
    gl.bindVertexArray(this.edgeVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, ids, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(1)
    gl.vertexAttribIPointer(1, 2, gl.UNSIGNED_INT, 0, 0)
    gl.vertexAttribDivisor(1, 1)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, tentative, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(2)
    gl.vertexAttribPointer(2, 1, gl.FLOAT, false, 0, 0)
    gl.vertexAttribDivisor(2, 1)

    // Date ranges are drawn as spans. Exact years have none.
    const ranged = model.nodes.flatMap((node, i) => (node.start !== undefined && node.end !== undefined && node.end > node.start ? [{ i, start: node.start, end: node.end }] : []))
    this.spanCount = ranged.length
    const ranges = new Float32Array(ranged.length * 2)
    const rangeIds = new Uint32Array(ranged.length)
    ranged.forEach(({ i, start, end }, k) => {
      ranges[k * 2] = start
      ranges[k * 2 + 1] = end
      rangeIds[k] = i
    })
    if (this.spanVao) gl.deleteVertexArray(this.spanVao)
    this.spanVao = gl.createVertexArray()!
    gl.bindVertexArray(this.spanVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, ranges, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(1)
    gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 0, 0)
    gl.vertexAttribDivisor(1, 1)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, rangeIds, gl.STATIC_DRAW)
    gl.enableVertexAttribArray(2)
    gl.vertexAttribIPointer(2, 1, gl.UNSIGNED_INT, 0, 0)
    gl.vertexAttribDivisor(2, 1)
    gl.bindVertexArray(null)
    this.uploadWarp()
  }

  /** Builds the rules of the reach view: one or more stretches per entry. */
  private uploadWarp(): void {
    const gl = this.gl
    const model = this.model
    if (!model || !gl) return
    const reach = model.reach
    const ranges: number[] = []
    const ids: number[] = []
    const styles: number[] = []
    const add = (id: number, a: number, b: number, style: number) => {
      if (b <= a) return
      ranges.push(a, b)
      ids.push(id)
      styles.push(style)
    }
    for (let i = 0; i < model.n; i++) {
      const y = model.nodes[i]!.year
      const direct = Math.max(y, reach.direct[i]!)
      const firm = Math.max(direct, reach.firm[i]!)
      const any = Math.max(firm, reach.any[i]!)
      add(i, y, direct, 0)
      add(i, direct, firm, 1)
      add(i, firm, any, 2)
      const span = documentedSpan(model.life.get(model.nodes[i]!.id))
      if (span) add(i, span.start, span.end, 3)
    }
    this.warpCount = ids.length
    if (this.warpVao) gl.deleteVertexArray(this.warpVao)
    this.warpVao = gl.createVertexArray()!
    gl.bindVertexArray(this.warpVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)
    gl.enableVertexAttribArray(0)
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(ranges), gl.STATIC_DRAW)
    gl.enableVertexAttribArray(1)
    gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 0, 0)
    gl.vertexAttribDivisor(1, 1)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, new Uint32Array(ids), gl.STATIC_DRAW)
    gl.enableVertexAttribArray(2)
    gl.vertexAttribIPointer(2, 1, gl.UNSIGNED_INT, 0, 0)
    gl.vertexAttribDivisor(2, 1)
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer())
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(styles), gl.STATIC_DRAW)
    gl.enableVertexAttribArray(3)
    gl.vertexAttribPointer(3, 1, gl.FLOAT, false, 0, 0)
    gl.vertexAttribDivisor(3, 1)
    gl.bindVertexArray(null)
  }

  /** Rows for an order, worked out the first time they are needed. */
  rowsFor(order: RowOrder): { rows: Int32Array; y: Float32Array } {
    let cached = this.rowsCache.get(order)
    if (!cached) {
      const model = this.model!
      const rows = rowOrder(model.nodes, model.children, model.parents, model.reach, order)
      cached = { rows, y: rowPositions(rows) }
      this.rowsCache.set(order, cached)
    }
    return cached
  }

  // ---------------------------------------------------------------- data and view

  setModel(model: Model): void {
    this.model = model
    this.state = new Float32Array(model.n * 4)
    this.targetState = new Float32Array(model.n * 4)
    this.labelAlpha = new Float32Array(model.n)
    this.uLinear = Float32Array.from(model.nodes, (node) => model.time.linear(node.year))
    this.uCompressed = Float32Array.from(model.nodes, (node) => model.time.compressed(node.year))
    this.rowsCache.clear()
    this.yNow = Float32Array.from(model.y)
    this.yGoal = Float32Array.from(model.y)
    this.uploadModel()
    this.computeTargets()
    this.state.set(this.targetState)
    this.stateDirty = true
    this.invalidate()
  }

  setView(next: Partial<ViewState>): void {
    const prev = this.view
    this.view = { ...prev, ...next }
    const view = this.view
    if (view.compressed !== prev.compressed) {
      this.camera.maxLogZoom = Math.log(view.compressed ? 220 : 1500)
      this.camera.fit(this.reducedMotion)
    }
    const modeChanged = view.mode !== prev.mode
    const storyChanged = view.story !== prev.story
    if (modeChanged || storyChanged || view.rowOrder !== prev.rowOrder) this.updateLayoutGoal()
    if (modeChanged || storyChanged || view.compressed !== prev.compressed) this.rebuildFold()
    // The rows and the folded story each have their own framing, so the page settles on it.
    const leavingLayout = modeChanged && (prev.mode === 'reach' || prev.mode === 'story')
    const enteringLayout = modeChanged && view.mode === 'reach'
    if (storyChanged && view.story) this.frameStory()
    else if (enteringLayout || leavingLayout || storyChanged) this.camera.fit(this.reducedMotion)
    this.computeTargets()
    this.invalidate()
  }

  private updateLayoutGoal(): void {
    const model = this.model
    if (!model) return
    const { mode, story, rowOrder: order } = this.view
    if (mode === 'reach') this.yGoal.set(this.rowsFor(order).y)
    else this.yGoal.set(model.y)
    if (mode === 'story' && story) story.members.forEach((i, k) => (this.yGoal[i] = story.y[k]!))
  }

  /** Opens the story's sheet so that each entry has room for its title. */
  private frameStory(): void {
    const story = this.view.story
    if (!story) return
    const cam = this.camera
    const usable = Math.max(1, cam.height - cam.insets.top - cam.insets.bottom)
    const rowGap = story.y.length > 1 ? story.y[1]! - story.y[0]! : 0.1
    const logY = Math.log(Math.max(1, 19 / (rowGap * usable)))
    const firstY = story.y[0] ?? 0.5
    cam.flyTo(0.5, logY > 0 ? firstY + 0.5 / Math.exp(logY) - 0.04 : 0.5, 0, this.reducedMotion, logY)
  }

  setInsets(insets: Insets): void {
    this.camera.setInsets(insets)
    this.invalidate()
  }

  passesFilters(i: number): boolean {
    const node = this.model!.nodes[i]!
    const { hiddenKinds, activeLabels } = this.view
    if (hiddenKinds.has(node.kind)) return false
    if (activeLabels.size > 0 && !node.labels.some((l) => activeLabels.has(l))) return false
    return true
  }

  // ---------------------------------------------------------------- folding the sheet

  /** Display position of an axis position, through the current fold. */
  toV(u: number): number {
    return this.foldNow.isIdentity ? u : this.foldNow.map(u)
  }

  /** Axis position at a screen x. */
  uAtX(x: number): number {
    return this.foldNow.invert(this.camera.fromX(x))
  }

  yearToX(year: number): number {
    return this.camera.toX(this.toV(this.model!.time.u(year, this.warp)))
  }

  xToYear(x: number): number {
    return this.model!.time.year(Math.min(1, Math.max(0, this.uAtX(x))), this.warp)
  }

  /** The stories view only lays a thread out once one is chosen. Until then it is the chart. */
  private get followingStory(): boolean {
    return this.view.mode === 'story' && this.view.story !== null
  }

  private get targetWarp(): number {
    return this.view.compressed && !this.followingStory ? 1 : 0
  }

  /** Works out the sheet's fold from the view and any opened periods, then eases to it. */
  private rebuildFold(): void {
    const model = this.model
    if (!model) return
    const { story } = this.view
    let map: FoldMap
    if (this.followingStory) {
      // A story is read to one scale: real years, with empty stretches folded away.
      map = foldAroundYears(story!.members.map((i) => model.nodes[i]!.year), { u: (year) => model.time.linear(year) }).map
    } else {
      const warp = this.targetWarp
      map = foldFromWindows(this.openPeriods.map(([a, b]) => [model.time.u(a, warp), model.time.u(b, warp)]))
    }
    this.foldFrom = this.foldNow
    this.foldTo = map
    // Reduced motion takes one step to arrive: the animation below finishes on its first frame.
    this.foldT = 0
    if (this.reducedMotion) {
      this.foldFrom = map
      this.foldT = 0.999
    }
    this.applyFold(this.foldFrom)
    this.invalidate()
  }

  private applyFold(map: FoldMap): void {
    this.foldNow = map
    if (map.isIdentity) {
      this.foldCount = 0
      return
    }
    this.foldCount = map.us.length
    for (let k = 0; k < map.us.length; k++) {
      this.foldData[k * 2] = map.us[k]!
      this.foldData[k * 2 + 1] = map.vs[k]!
    }
  }

  private animateFold(dt: number): boolean {
    if (this.foldT >= 1) return false
    this.foldT = Math.min(1, this.foldT + dt / FOLD_SECONDS)
    const blended = blendFolds(this.foldFrom, this.foldTo, easeInOut(this.foldT))
    // Blending a blend could run past what the shader holds, so it jumps instead.
    this.applyFold(blended.us.length > MAX_FOLD_POINTS ? this.foldTo : blended)
    return true
  }

  /** Whether an axis position lies inside a pleat. */
  inPleat(u: number): boolean {
    const pleats = this.foldTo.pleats
    for (let k = 0; k < pleats.length; k++) if (u > pleats[k]!.u0 && u < pleats[k]!.u1) return true
    return false
  }

  /** Opens a period of years. Everything else pleats, and the sheet fits to the page. */
  openPeriod(a: number, b: number): void {
    const model = this.model
    if (!model) return
    const start = Math.max(model.time.min, Math.min(a, b))
    const end = Math.min(model.time.now, Math.max(a, b))
    if (end <= start) return
    this.openPeriods = [...this.openPeriods, [start, end] as [number, number]].slice(-MAX_OPEN_PERIODS)
    this.openPeriods.sort((x, y) => x[0] - y[0])
    // Overlapping periods read as one.
    const merged: [number, number][] = []
    for (const p of this.openPeriods) {
      const last = merged[merged.length - 1]
      if (last && p[0] <= last[1]) last[1] = Math.max(last[1], p[1])
      else merged.push([p[0], p[1]])
    }
    this.openPeriods = merged
    this.callbacks.onFolds(merged.length)
    this.rebuildFold()
    this.camera.fit(this.reducedMotion)
    this.invalidate()
  }

  unfoldAll(): void {
    if (this.openPeriods.length === 0) return
    this.openPeriods = []
    this.callbacks.onFolds(0)
    this.rebuildFold()
    this.invalidate()
  }

  /** Where the sheet is folded. */
  get pleats(): readonly Pleat[] {
    return this.foldTo.pleats
  }

  /** The pleat under a screen x, if there is one. */
  pleatAtX(x: number): Pleat | null {
    const u = this.uAtX(x)
    return this.foldTo.pleats.find((p) => u >= p.u0 && u <= p.u1) ?? null
  }

  /** Unfolds one pleat by joining the opened periods either side of it. */
  private unfold(pleat: Pleat): void {
    const model = this.model!
    if (this.followingStory || this.openPeriods.length === 0) return
    const warp = this.targetWarp
    const windows = this.openPeriods.map(([a, b]): [number, number] => [model.time.u(a, warp), model.time.u(b, warp)])
    const next = unfoldPleat(windows, pleat)
    // A pleat at the very edge joins its window to the end of the axis.
    const full = next.length === 1 && next[0]![0] <= 1e-6 && next[0]![1] >= 1 - 1e-6
    this.openPeriods = full ? [] : next.map(([a, b]): [number, number] => [model.time.year(a, warp), model.time.year(b, warp)])
    this.callbacks.onFolds(this.openPeriods.length)
    this.rebuildFold()
    this.invalidate()
  }

  private animateLayout(dt: number): boolean {
    const n = this.yNow.length
    const k = this.reducedMotion ? 1 : 1 - Math.exp(-dt * 6.5)
    let changed = false
    const y = this.yNow
    const goal = this.yGoal
    const a = this.aData
    for (let i = 0; i < n; i++) {
      const d = goal[i]! - y[i]!
      if (d === 0) continue
      changed = true
      y[i] = Math.abs(d) < 0.0004 ? goal[i]! : y[i]! + d * k
      a[i * 4 + 1] = y[i]!
    }
    if (changed) this.aDirty = true
    return changed
  }

  /** Works out the state each node should ease toward from filters, mode and focus. */
  private computeTargets(): void {
    const model = this.model
    if (!model) return
    this.computeRate()
    const { mode, selected, story, searchHits, previewLabel } = this.view
    const target = this.targetState
    const inStory = mode === 'story' && story !== null
    const members = inStory ? new Set(story!.members) : null
    const focus = inStory ? null : selected ?? this.hovered
    const isHover = selected === null && this.hovered !== null

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
      let faded = 0
      let boost = 0
      if (hops) {
        const h = hops.get(i)
        if (h === undefined) {
          faded = isHover ? 0.32 : 1
        } else {
          boost = h <= 1 ? 1 : h === 2 ? 0.8 : 0.6
          if (isHover) boost *= 0.85
        }
      }
      if (searchHits) {
        if (searchHits.has(i)) {
          boost = Math.max(boost, 0.8)
        } else {
          faded = Math.max(faded, 0.86)
        }
      }
      if (previewLabel !== null) {
        if (model.nodes[i]!.labels.includes(previewLabel)) {
          boost = Math.max(boost, 0.7)
        } else {
          faded = Math.max(faded, 0.86)
        }
      }
      if (members) {
        // A followed thread is lifted off the page. Everything else stays as a trace of what
        // it came from, too faint to read or to pick.
        if (members.has(i)) {
          faded = 0
          boost = i === selected ? 0.6 : 0.2
        } else {
          target[o] = match * 0.07
          target[o + 1] = 1
          target[o + 2] = 0
          continue
        }
      }
      target[o] = match
      target[o + 1] = faded
      target[o + 2] = boost
    }
  }

  /**
   * Entries per year through history, for the density view. Counts are smoothed in log
   * time, then divided by how many years each step covers, so recent and ancient periods
   * compare fairly however the axis is stretched.
   */
  private computeRate(): void {
    const model = this.model!
    const time = model.time
    const counts = new Float32Array(RATE_BINS)
    model.nodes.forEach((node, i) => {
      if (!this.passesFilters(i)) return
      counts[Math.min(RATE_BINS - 1, Math.round(time.logPosition(node.year) * (RATE_BINS - 1)))]! += 1
    })
    const rate = new Float32Array(RATE_BINS)
    let max = 1e-9
    for (let b = 0; b < RATE_BINS; b++) {
      let sum = 0
      for (let k = -RATE_SMOOTHING * 3; k <= RATE_SMOOTHING * 3; k++) {
        const c = counts[b + k]
        if (c) sum += c * Math.exp(-(k * k) / (2 * RATE_SMOOTHING * RATE_SMOOTHING))
      }
      const position = b / (RATE_BINS - 1)
      const yearsBefore = time.tau * (Math.exp(position * time.logSpan) - 1)
      // Years spanned by one bin at this distance from the present.
      const span = ((time.tau + yearsBefore) * time.logSpan) / (RATE_BINS - 1)
      const r = sum / span
      rate[b] = r
      if (r > max) max = r
    }
    this.rate = rate
    this.rateMax = max
  }

  /** Height of the density silhouette at a year, 0 to 1. A square root keeps quiet eras visible. */
  private rateAt(year: number): number {
    const f = this.model!.time.logPosition(year) * (RATE_BINS - 1)
    const i = Math.min(RATE_BINS - 2, Math.floor(f))
    const r = this.rate[i]! + (this.rate[i + 1]! - this.rate[i]!) * (f - i)
    return Math.sqrt(r / this.rateMax)
  }

  private animateState(dt: number): boolean {
    const n = this.state.length
    const k = this.reducedMotion ? 1 : 1 - Math.exp(-dt * 11)
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
    const goal = MODE_MIX[this.view.mode === 'story' && !this.followingStory ? 'threads' : this.view.mode]
    const k = this.reducedMotion ? 1 : 1 - Math.exp(-dt * 7)
    let changed = false
    const mix = this.mix as Record<string, number>
    for (const key of Object.keys(goal) as (keyof typeof goal)[]) {
      const d = goal[key] - mix[key]!
      if (d === 0) continue
      changed = true
      mix[key] = Math.abs(d) < 0.002 ? goal[key] : mix[key]! + d * k
    }
    const warpGoal = this.targetWarp
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

  /** An entry's position across the sheet, through any folds. */
  nodeV(i: number): number {
    return this.toV(this.nodeU(i))
  }

  pick(x: number, y: number): number | null {
    const model = this.model
    if (!model) return null
    // A box on top wins: what you can read is what you are pointing at.
    for (let k = this.boxes.length - 1; k >= 0; k--) {
      const box = this.boxes[k]!
      if (x >= box.x0 && x <= box.x1 && y >= box.y0 && y <= box.y1) return box.i
    }
    const cam = this.camera
    const xs = cam.xScale
    const ys = cam.yScale
    const cx = cam.centerX
    const cy = cam.centerY
    let best: number | null = null
    let bestScore = Infinity
    for (let i = 0; i < model.n; i++) {
      if (this.state[i * 4]! < 0.5 || this.state[i * 4 + 1]! > 0.9) continue
      const px = (this.nodeV(i) - cam.cu) * xs + cx
      const py = (this.yNow[i]! - cam.cy) * ys + cy
      const dx = px - x
      const dy = py - y
      const r = model.radius[i]! + 8
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
    const lz = Math.max(this.camera.logZoom, 0.8)
    const v = this.foldTo.map(this.nodeU(i))
    this.camera.flyTo(v, this.yGoal[i]!, lz, this.reducedMotion, Math.max(this.camera.logY, lz * 0.55))
    this.invalidate()
  }

  /** Fits a span of years in the view. */
  flyToYears(start: number, end: number): void {
    const model = this.model
    if (!model) return
    const a = this.foldTo.map(model.time.u(start, this.targetWarp))
    const b = this.foldTo.map(model.time.u(end, this.targetWarp))
    const zoom = 1 / Math.max(1e-5, b - a)
    this.camera.flyTo((a + b) / 2, this.camera.cy, Math.log(Math.max(1, zoom)), this.reducedMotion, this.camera.logY)
    this.invalidate()
  }

  /** Fits everything in the page and unfolds the sheet. */
  fit(): void {
    this.unfoldAll()
    this.camera.fit(this.reducedMotion)
    this.invalidate()
  }

  zoomBy(factor: number, axis: ZoomAxis = 'both'): void {
    this.camera.zoomAt(this.camera.centerX, this.camera.centerY, Math.log(factor), axis)
    this.invalidate()
  }

  panByKeys(dx: number, dy: number): void {
    this.camera.panBy(dx, dy)
    this.invalidate()
  }

  /** Moves the view so `u` is centred, for the overview strip. */
  panToU(u: number): void {
    const cam = this.camera
    cam.panBy((cam.cu - this.toV(u)) * cam.xScale, 0)
    this.invalidate()
  }

  /** Fits the view to a stretch of the axis, for the overview strip's handles. */
  showU(u0: number, u1: number): void {
    this.camera.showTimeRange(this.toV(Math.min(u0, u1)), this.toV(Math.max(u0, u1)))
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

  /** The ruler zooms time, the left margin zooms height, and the chart zooms both. */
  private zoneAt(x: number, y: number): 'ruler' | 'gutter' | 'chart' | null {
    const frame = this.frameBounds()
    if (y >= frame.top - LAYOUT.ruler && y <= frame.top + UNIT) return 'ruler'
    if (y < frame.top || y > frame.bottom) return null
    if (x < Math.min(this.camera.insets.left - 8, 40)) return 'gutter'
    return 'chart'
  }

  private onWheel = (e: WheelEvent): void => {
    e.preventDefault()
    const { x, y } = this.localPoint(e)
    const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 100 : 1
    const dy = e.deltaY * unit
    const dx = e.deltaX * unit
    const device = this.wheelKind.classify(e as WheelEvent & { wheelDeltaY?: number })
    const zone = this.zoneAt(x, y)
    // Option limits any zoom to time, Shift to height. So does where the pointer is.
    const axis: ZoomAxis = e.altKey || zone === 'ruler' ? 'time' : zone === 'gutter' || (e.shiftKey && device === 'pinch') ? 'height' : 'both'
    if (device === 'pinch') {
      this.camera.zoomAt(x, y, -dy * 0.012, axis, true)
    } else if (device === 'mouse' && !e.shiftKey) {
      this.camera.zoomAt(x, y, -wheelNotches(e as WheelEvent & { wheelDeltaY?: number }) * 0.26, axis)
    } else if (e.shiftKey) {
      this.camera.panBy(-dy - dx, 0)
    } else if (axis !== 'both') {
      // Scrolling over the ruler or margin scales that axis, keeping sideways scroll for panning.
      this.camera.zoomAt(x, y, -dy * 0.006, axis, true)
      if (dx !== 0) this.camera.panBy(-dx, 0)
    } else {
      this.camera.panBy(-dx, -dy)
    }
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
      this.pinchSpan = { x: Math.abs(a!.x - b!.x), y: Math.abs(a!.y - b!.y) }
      this.drag = null
      this.bracket = null
      return
    }
    if (this.zoneAt(p.x, p.y) === 'ruler' && !this.followingStory) {
      this.bracket = { x0: p.x, x1: p.x }
      this.invalidate()
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
        // A sideways pinch stretches time, an upright one stretches height, and a diagonal
        // one does both, as if the sheet were held between the two fingers.
        const spanX = Math.abs(a!.x - b!.x)
        const spanY = Math.abs(a!.y - b!.y)
        const midX = (a!.x + b!.x) / 2
        const midY = (a!.y + b!.y) / 2
        const tilt = Math.min(spanX, spanY) / Math.max(1, Math.max(spanX, spanY))
        if (tilt > 0.5) this.camera.zoomAt(midX, midY, Math.log(distance / this.pinchDistance), 'both', true)
        else if (spanX > spanY) this.camera.zoomAt(midX, midY, Math.log(Math.max(1, spanX) / Math.max(1, this.pinchSpan.x)), 'time', true)
        else this.camera.zoomAt(midX, midY, Math.log(Math.max(1, spanY) / Math.max(1, this.pinchSpan.y)), 'height', true)
        this.pinchSpan = { x: spanX, y: spanY }
      }
      this.pinchDistance = distance
      this.invalidate()
      return
    }

    if (this.bracket) {
      this.bracket = { x0: this.bracket.x0, x1: p.x }
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
    const zone = this.zoneAt(p.x, p.y)
    const zoneChanged = zone !== this.pointerZone
    this.pointerZone = zone
    if (zone === 'ruler') {
      this.setHover(null, 0, 0)
      this.overlay.style.cursor = this.followingStory ? 'default' : this.pleatAtX(p.x) ? 'pointer' : 'col-resize'
      this.invalidate()
      return
    }
    const hit = zone === 'chart' ? this.pick(p.x, p.y) : null
    this.setHover(hit, p.x, p.y)
    this.overlay.style.cursor = hit !== null ? 'pointer' : zone === 'gutter' ? 'ns-resize' : 'grab'
    if (this.view.mode === 'density' || zoneChanged) this.invalidate()
  }

  private onPointerUp = (e: PointerEvent): void => {
    const wasPinching = this.pinch.size >= 2
    this.pinch.delete(e.pointerId)
    if (this.pinch.size < 2) this.pinchDistance = 0
    this.overlay.style.cursor = 'grab'
    if (this.bracket) {
      const { x0, x1 } = this.bracket
      this.bracket = null
      if (Math.abs(x1 - x0) >= 8) {
        this.openPeriod(this.xToYear(Math.min(x0, x1)), this.xToYear(Math.max(x0, x1)))
      } else {
        const pleat = this.pleatAtX(x0)
        if (pleat) this.unfold(pleat)
      }
      this.invalidate()
      return
    }
    const d = this.drag
    if (!d || d.id !== e.pointerId || wasPinching) return
    this.drag = null
    if (d.moved <= 3) {
      const p = this.localPoint(e)
      // Touch has no hover, so a tap needs its own hit test. Empty space clears selection.
      const hit = this.pick(p.x, p.y)
      // Two taps on one entry follow its thread.
      if (hit !== null && hit === this.lastTap.index && e.timeStamp - this.lastTap.time < 420) {
        this.lastTap = { index: -1, time: 0 }
        this.callbacks.onFollow(hit)
      } else {
        this.lastTap = { index: hit ?? -1, time: e.timeStamp }
        this.callbacks.onSelect(hit)
      }
    } else if (!this.reducedMotion && e.timeStamp - d.t < 80) {
      this.camera.fling(d.vx, d.vy)
      this.invalidate()
    }
  }

  private onPointerLeave = (): void => {
    this.pointer = null
    this.pointerZone = null
    this.setHover(null, 0, 0)
    this.invalidate()
  }

  private onDoubleClick = (e: MouseEvent): void => {
    const { x, y } = this.localPoint(e)
    const zone = this.zoneAt(x, y)
    if (zone === 'ruler') return
    if (this.pick(x, y) !== null) return
    this.camera.zoomAt(x, y, e.altKey ? -Math.log(2) : Math.log(2))
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
    if (this.camera.width === width && this.camera.height === height && this.dpr === dpr) return
    this.dpr = dpr
    for (const c of [this.canvas, this.overlay]) {
      c.width = Math.max(1, Math.round(width * dpr))
      c.height = Math.max(1, Math.round(height * dpr))
      c.style.width = `${width}px`
      c.style.height = `${height}px`
    }
    this.camera.resize(width, height)
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
    const layoutMoving = this.animateLayout(dt)
    const foldMoving = this.animateFold(dt)

    if (this.model && this.gl && !this.gl.isContextLost()) {
      this.computeTicks()
      this.render()
      drawOverlay(this, this.overlayCtx, dt)
      this.callbacks.onFrame(this)
    }
    this.frameMs = performance.now() - start

    if (cameraMoving || stateMoving || mixMoving || layoutMoving || foldMoving || this.labelsAnimating) {
      this.raf = requestAnimationFrame(this.frame)
    } else {
      this.lastTime = 0
    }
  }

  /**
   * Finds the ruler's cells across the whole axis, measured on the sheet rather than the screen.
   * Each cell's year and shade then stay put as the page pans, and change only with the zoom.
   */
  private computeTicks(): void {
    const cam = this.camera
    const time = this.model!.time
    const scale = cam.xScale
    const key = `${scale.toFixed(1)}|${this.warp.toFixed(3)}|${this.foldNow.us.join()}|${this.foldNow.vs.join()}|${cam.width}`
    if (key !== this.tickKey) {
      this.tickKey = key
      // A folded stretch cannot hold a readable cell. Its own note says how much it hides.
      const reject = this.foldTo.pleats.length ? (x: number) => this.inPleat(this.foldNow.invert(x / scale)) : undefined
      const toX = (year: number) => this.toV(time.u(year, this.warp)) * scale
      const thisYear = new Date().getFullYear()
      this.axisTicks = pickTicks(toX, time.min, thisYear, cam.width < 700 ? 58 : 66, reject).map((t, k) => ({ year: t.year, v: t.x / scale, odd: k % 2 === 1 }))
    }
    const all = this.axisTicks
    this.ticks.length = 0
    const left = cam.fromX(0)
    const right = cam.fromX(cam.width)
    for (let k = 0; k < all.length; k++) {
      const next = all[k + 1]?.v ?? Infinity
      if (next < left || all[k]!.v > right) continue
      this.ticks.push({ year: all[k]!.year, x: cam.toX(all[k]!.v), odd: all[k]!.odd })
    }
  }

  /** Where the axis ends on screen, which closes the last of the ruler's cells. */
  axisEndX(): number {
    return this.camera.toX(this.toV(1))
  }

  private setWorldUniforms(p: Program): void {
    const gl = this.gl
    const cam = this.camera
    const dpr = this.dpr
    const model = this.model!
    gl.uniform2f(p.u.uRes!, this.canvas.width, this.canvas.height)
    gl.uniform2f(p.u.uCam!, cam.cu, cam.cy)
    gl.uniform2f(p.u.uScale!, cam.xScale * dpr, cam.yScale * dpr)
    gl.uniform2f(p.u.uCenter!, cam.centerX * dpr, cam.centerY * dpr)
    gl.uniform4f(p.u.uTimeScale!, model.time.min, model.time.now, model.time.tau, model.time.logSpan)
    gl.uniform1f(p.u.uWarp!, this.warp)
    gl.uniform2fv(p.u.uFold!, this.foldData)
    gl.uniform1i(p.u.uFoldCount!, this.foldCount)
    if (p.u.uDpr) gl.uniform1f(p.u.uDpr, dpr)
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, this.texA)
    if (p.u.uNodeA) gl.uniform1i(p.u.uNodeA, 0)
    gl.activeTexture(gl.TEXTURE1)
    gl.bindTexture(gl.TEXTURE_2D, this.texB)
    if (p.u.uNodeB) gl.uniform1i(p.u.uNodeB, 1)
    gl.activeTexture(gl.TEXTURE2)
    gl.bindTexture(gl.TEXTURE_2D, this.texState)
    if (p.u.uState) gl.uniform1i(p.u.uState, 2)
    gl.activeTexture(gl.TEXTURE3)
    gl.bindTexture(gl.TEXTURE_2D, this.texLut)
    if (p.u.uTimeLut) gl.uniform1i(p.u.uTimeLut, 3)
    gl.activeTexture(gl.TEXTURE0)
  }

  private uploadState(): void {
    if (!this.stateDirty) return
    this.stateDirty = false
    const gl = this.gl
    const model = this.model!
    if (model.n === 0) return
    const rows = this.texHeight
    const size = S.TEX_WIDTH * rows * 4
    if (this.stateUpload.length !== size) this.stateUpload = new Float32Array(size)
    this.stateUpload.set(this.state)
    gl.activeTexture(gl.TEXTURE2)
    gl.bindTexture(gl.TEXTURE_2D, this.texState)
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, S.TEX_WIDTH, rows, gl.RGBA, gl.FLOAT, this.stateUpload)
    gl.activeTexture(gl.TEXTURE0)
  }

  private render(): void {
    const gl = this.gl
    const model = this.model!
    const W = this.canvas.width
    const H = this.canvas.height
    const P = this.programs
    const mix = this.mix

    this.uploadState()
    if (this.aDirty) {
      this.aDirty = false
      gl.activeTexture(gl.TEXTURE0)
      gl.bindTexture(gl.TEXTURE_2D, this.texA)
      gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, S.TEX_WIDTH, this.texHeight, gl.RGBA, gl.FLOAT, this.aData)
    }

    gl.bindFramebuffer(gl.FRAMEBUFFER, null)
    gl.viewport(0, 0, W, H)

    gl.disable(gl.SCISSOR_TEST)
    gl.clearColor(PAPER[0], PAPER[1], PAPER[2], 1)
    gl.clear(gl.COLOR_BUFFER_BIT)
    gl.enable(gl.BLEND)

    // Ink stays inside the frame, leaving clean margins as on a printed plate.
    const frame = this.frameBounds()
    gl.enable(gl.SCISSOR_TEST)
    gl.scissor(0, Math.round(H - frame.bottom * this.dpr), W, Math.round((frame.bottom - frame.top) * this.dpr))

    this.drawRules(W, H)

    // Everything inked multiplies onto the page.
    gl.blendFunc(gl.DST_COLOR, gl.ZERO)

    // The reach view's rules.
    const weave = mix.weave
    if (weave > 0.01 && this.warpVao && this.warpCount) {
      gl.useProgram(P.warp.handle)
      this.setWorldUniforms(P.warp)
      gl.uniform1f(P.warp.u.uWarpAlpha!, weave)
      gl.bindVertexArray(this.warpVao)
      gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, this.warpCount)
    }
    const rowPx = model.n > 1 ? cam_rowPx(this.camera, model.n) : 0

    if (this.edgeVao && model.edges.length) {
      gl.useProgram(P.edge.handle)
      this.setWorldUniforms(P.edge)
      gl.uniform1f(P.edge.u.uWeave!, weave)
      gl.uniform1f(P.edge.u.uElbow!, mix.elbow)
      gl.uniform1f(P.edge.u.uEdgeAlpha!, mix.edges * (model.edges.length > 2000 ? 0.3 : 1))
      // A finer line as the page fills, so dense passages stay open.
      gl.uniform1f(P.edge.u.uStrokeScale!, Math.max(0.5, Math.min(1, Math.pow(400 / model.edges.length, 0.28))))
      gl.bindVertexArray(this.edgeVao)
      gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, this.edgeVertCount, model.edges.length)
    }

    if (this.spanVao && this.spanCount) {
      gl.useProgram(P.span.handle)
      this.setWorldUniforms(P.span)
      gl.bindVertexArray(this.spanVao)
      gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, this.spanCount)
    }

    // Marks sit on top with their own paper-coloured centres, so open ones stay open.
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)
    gl.useProgram(P.node.handle)
    this.setWorldUniforms(P.node)
    gl.uniform1f(P.node.u.uNodeAlpha!, mix.nodes)
    // A one-sided date's tail shows once rows are far enough apart for it to read as one.
    gl.uniform1f(P.node.u.uTail!, Math.min(1, Math.max(0, (model.rowStep * this.camera.yScale - 13) / 5)) * (1 - weave))
    gl.uniform1i(P.node.u.uHover!, this.hovered ?? -1)
    gl.uniform1i(P.node.u.uSelected!, this.view.selected ?? -1)
    gl.uniform3f(P.node.u.uPaper!, PAPER[0], PAPER[1], PAPER[2])
    // Rows are tight at a distance, so marks keep within their row.
    gl.uniform1f(P.node.u.uMarkCap!, 100 + (Math.max(1.5, rowPx * 0.55) - 100) * weave)
    gl.bindVertexArray(this.quadVao)
    gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, model.n)
    gl.bindVertexArray(null)
    gl.disable(gl.SCISSOR_TEST)
  }

  /** The area of the page that holds the chart, under the ruler, in CSS pixels. */
  frameBounds(): { top: number; bottom: number } {
    const cam = this.camera
    return { top: cam.insets.top - LAYOUT.framePad, bottom: cam.height - cam.insets.bottom + LAYOUT.framePad }
  }

  /** Time as bands of tone behind the chart, and in the density view the hatched silhouette of activity. */
  private drawRules(W: number, H: number): void {
    const gl = this.gl
    const cam = this.camera
    const dpr = this.dpr
    const data = this.rectData
    const model = this.model!
    let count = 0
    const { top, bottom } = this.frameBounds()
    const end = this.axisEndX()
    for (let k = 0; k < this.ticks.length && count < MAX_RECTS; k++) {
      const tick = this.ticks[k]!
      if (!tick.odd) continue
      const x0 = Math.max(0, tick.x)
      const x1 = Math.min(cam.width, this.ticks[k + 1]?.x ?? end)
      if (x1 <= x0) continue
      data.set([x0 * dpr, top * dpr, x1 * dpr, bottom * dpr, RULE_COLOR[0], RULE_COLOR[1], RULE_COLOR[2], RULE_ALPHA.band * this.mix.rules], count * 8)
      count++
    }

    // Pleats: a flat tone with fold lines, wherever the sheet is folded.
    for (const pleat of this.foldTo.pleats) {
      const x0 = cam.toX(this.foldNow.map(pleat.u0))
      const x1 = cam.toX(this.foldNow.map(pleat.u1))
      if (x1 < 0 || x0 > cam.width || x1 - x0 < 1) continue
      if (count >= MAX_RECTS) break
      data.set([x0 * dpr, top * dpr, x1 * dpr, bottom * dpr, RULE_COLOR[0], RULE_COLOR[1], RULE_COLOR[2], PLEAT_TONE_ALPHA], count * 8)
      count++
      const spacing = Math.max(UNIT / 2, Math.min(UNIT, (x1 - x0) / 6))
      for (let x = x0; x <= x1 + 0.01 && count < MAX_RECTS; x += spacing) {
        data.set([x * dpr - 0.5, top * dpr, x * dpr + 0.5, bottom * dpr, RULE_COLOR[0], RULE_COLOR[1], RULE_COLOR[2], PLEAT_FOLD_ALPHA], count * 8)
        count++
      }
    }

    const hatching = this.mix.hatching
    if (hatching > 0.005) {
      const middle = (top + bottom) / 2
      const reach = (bottom - top) * 0.46
      // Strokes are pinned to the page, so they travel with it rather than shimmering.
      const origin = cam.toX(0)
      const first = origin - Math.ceil(origin / HATCH_SPACING) * HATCH_SPACING
      for (let x = first; x < cam.width && count < MAX_RECTS; x += HATCH_SPACING) {
        const u = this.uAtX(x)
        if (u < 0 || u > 1) continue
        const h = this.rateAt(model.time.year(u, this.warp))
        if (h < 0.015) continue
        const half = h * reach * hatching
        data.set([x * dpr - 0.5 * dpr, (middle - half) * dpr, x * dpr + 0.5 * dpr, (middle + half) * dpr, HATCH_COLOR[0], HATCH_COLOR[1], HATCH_COLOR[2], HATCH_ALPHA * hatching], count * 8)
        count++
      }
    }

    if (count === 0) return
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)
    gl.useProgram(this.programs.rect.handle)
    gl.uniform2f(this.programs.rect.u.uRes!, W, H)
    gl.bindVertexArray(this.rectVao)
    gl.bindBuffer(gl.ARRAY_BUFFER, this.rectBuffer)
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, data.subarray(0, count * 8))
    gl.drawArraysInstanced(gl.TRIANGLE_STRIP, 0, 4, count)
  }

  // ---------------------------------------------------------------- context loss

  private onContextLost = (e: Event): void => {
    e.preventDefault()
    cancelAnimationFrame(this.raf)
    this.raf = 0
  }

  private onContextRestored = (): void => {
    this.texA = this.texB = this.texState = this.texLut = null
    this.edgeVao = null
    this.spanVao = null
    this.warpVao = null
    this.initGL()
    this.uploadModel()
    this.invalidate()
  }
}

/** Height of one row at the current zoom, in CSS pixels. */
function cam_rowPx(cam: Camera, n: number): number {
  return (cam.yScale * 0.976) / Math.max(1, n - 1)
}
