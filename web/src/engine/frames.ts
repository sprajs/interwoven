import type { Engine } from './Engine.ts'

type FrameListener = (engine: Engine) => void
const listeners = new Set<FrameListener>()

/** Lets DOM widgets follow the camera each frame without going through React. */
export function onEngineFrame(listener: FrameListener): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function emitFrame(engine: Engine): void {
  for (const listener of listeners) listener(engine)
}
