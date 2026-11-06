export type WheelDevice = 'pinch' | 'mouse' | 'trackpad'

interface WheelLike {
  ctrlKey: boolean
  metaKey: boolean
  deltaX: number
  deltaY: number
  deltaMode: number
  /** Non-standard, but present in Chromium and Safari, and the best evidence there is. */
  wheelDeltaY?: number
  timeStamp: number
}

/** A gesture keeps its device, so one odd event cannot flip a scroll into a zoom halfway. */
const STICKY_MS = 140

/**
 * Tells a trackpad from a mouse wheel, which the browser does not say directly. A pinch
 * arrives as ctrl+wheel. Line or page units only come from wheels. Chromium and Safari report
 * notched wheels in multiples of 120 and trackpads as exactly three times the pixel delta.
 */
export class WheelClassifier {
  private last: WheelDevice = 'trackpad'
  private lastTime = -Infinity

  classify(e: WheelLike): WheelDevice {
    if (e.ctrlKey || e.metaKey) return this.remember('pinch', e.timeStamp)
    const sticky = e.timeStamp - this.lastTime < STICKY_MS
    if (sticky && this.last !== 'pinch') return this.remember(this.last, e.timeStamp)
    return this.remember(guess(e), e.timeStamp)
  }

  private remember(device: WheelDevice, time: number): WheelDevice {
    this.last = device
    this.lastTime = time
    return device
  }
}

function guess(e: WheelLike): WheelDevice {
  if (e.deltaMode !== 0) return 'mouse'
  if (e.deltaX !== 0) return 'trackpad'
  const wheel = e.wheelDeltaY
  if (wheel !== undefined && wheel !== 0) {
    if (Math.abs(wheel) % 120 === 0) return 'mouse'
    if (Math.abs(wheel + 3 * e.deltaY) < 1.5) return 'trackpad'
  }
  return Math.abs(e.deltaY) >= 50 && Number.isInteger(e.deltaY) ? 'mouse' : 'trackpad'
}

/** How many notches a wheel event is worth, however the platform scaled it. */
export function wheelNotches(e: Pick<WheelLike, 'deltaY' | 'deltaMode' | 'wheelDeltaY'>): number {
  if (e.wheelDeltaY) return -e.wheelDeltaY / 120
  if (e.deltaMode === 1) return e.deltaY / 3
  if (e.deltaMode === 2) return e.deltaY
  return e.deltaY / 100
}
