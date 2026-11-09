import { describe, expect, it } from 'vitest'
import { ScrollLock, scrollZoomDelta, WheelClassifier, wheelNotches } from './wheel.ts'

const event = (over: Partial<Parameters<WheelClassifier['classify']>[0]>) => ({ ctrlKey: false, metaKey: false, deltaX: 0, deltaY: 0, deltaMode: 0, timeStamp: 0, ...over })

describe('WheelClassifier', () => {
  it('reads ctrl+wheel as a pinch', () => {
    expect(new WheelClassifier().classify(event({ ctrlKey: true, deltaY: 3 }))).toBe('pinch')
  })

  it('reads a notched wheel in pixels, whatever its acceleration', () => {
    expect(new WheelClassifier().classify(event({ deltaY: 4, wheelDeltaY: -120 }))).toBe('mouse')
    expect(new WheelClassifier().classify(event({ deltaY: 100, wheelDeltaY: -120 }))).toBe('mouse')
  })

  it('reads line units as a wheel, as Firefox reports them', () => {
    expect(new WheelClassifier().classify(event({ deltaMode: 1, deltaY: 3 }))).toBe('mouse')
  })

  it('reads fine and two-axis deltas as a trackpad', () => {
    expect(new WheelClassifier().classify(event({ deltaY: 7, wheelDeltaY: -21 }))).toBe('trackpad')
    expect(new WheelClassifier().classify(event({ deltaX: 2, deltaY: 40 }))).toBe('trackpad')
  })

  it('does not flip partway through a gesture', () => {
    const c = new WheelClassifier()
    expect(c.classify(event({ deltaY: 7, wheelDeltaY: -21, timeStamp: 0 }))).toBe('trackpad')
    expect(c.classify(event({ deltaY: 40, wheelDeltaY: -120, timeStamp: 16 }))).toBe('trackpad')
    expect(c.classify(event({ deltaY: 40, wheelDeltaY: -120, timeStamp: 1000 }))).toBe('mouse')
  })
})

describe('ScrollLock', () => {
  it('zooms for two fingers up or down, and pans for sideways', () => {
    expect(new ScrollLock().resolve(0, 12, 0)).toBe('zoom')
    expect(new ScrollLock().resolve(0, -12, 0)).toBe('zoom')
    expect(new ScrollLock().resolve(12, 0, 0)).toBe('pan')
  })

  it('waits until a gesture has moved far enough to judge', () => {
    const lock = new ScrollLock()
    expect(lock.resolve(1, 0, 0)).toBeNull()
    expect(lock.resolve(0, 8, 10)).toBe('zoom')
  })

  it('keeps its direction when the fingers drift, and through momentum', () => {
    const lock = new ScrollLock()
    expect(lock.resolve(0, 20, 0)).toBe('zoom')
    expect(lock.resolve(40, 2, 16)).toBe('zoom')
    expect(lock.resolve(30, 0, 32)).toBe('zoom')
  })

  it('judges afresh after a pause', () => {
    const lock = new ScrollLock()
    expect(lock.resolve(0, 20, 0)).toBe('zoom')
    expect(lock.resolve(20, 0, 500)).toBe('pan')
  })
})

describe('scrollZoomDelta', () => {
  it('zooms in for negative scroll and out for positive, as a wheel does', () => {
    expect(scrollZoomDelta(-50)).toBeGreaterThan(0)
    expect(scrollZoomDelta(50)).toBeLessThan(0)
  })

  it('limits how far one hard flick can jump', () => {
    expect(scrollZoomDelta(-100000)).toBe(0.3)
    expect(scrollZoomDelta(100000)).toBe(-0.3)
  })
})

describe('wheelNotches', () => {
  it('gives one notch for one click on every platform', () => {
    expect(wheelNotches({ deltaY: 4, deltaMode: 0, wheelDeltaY: -120 })).toBe(1)
    expect(wheelNotches({ deltaY: 3, deltaMode: 1 })).toBe(1)
    expect(wheelNotches({ deltaY: 100, deltaMode: 0 })).toBe(1)
  })
})
