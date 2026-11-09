import { useEffect, useReducer, type ComponentType } from 'react'
import { loadDetail, loadPopulation } from '../data/load.ts'
import type { Entry, Model } from '../data/model.ts'
import type { Bundle } from '../data/types.ts'

type Result<T> = {promise: Promise<void>; value?: T; error?: Error}
const resources = new WeakMap<object, Map<string, Result<unknown>>>()
/** Load code and data together; render on resolution, without a fallback minimum duration. */
function useAsync<T>(owner: object, key: string, load: () => Promise<T>): T | undefined {
  let cache = resources.get(owner)
  if (!cache) { cache = new Map(); resources.set(owner, cache) }
  let result = cache.get(key) as Result<T> | undefined
  if (!result) {
    const created: Result<T> = {promise: Promise.resolve()}
    created.promise = load().then(value => { created.value = value }, error => { created.error = error instanceof Error ? error : new Error(String(error)) })
    cache.set(key, created)
    result = created
  }
  const [, redraw] = useReducer(n => n + 1, 0)
  useEffect(() => {
    let live = true
    void result.promise.then(() => { if (live) redraw() })
    return () => { live = false }
  }, [result])
  if (result.error) throw result.error
  return result.value
}

export function AsyncDetail({model, entry, close}: {model: Model; entry: Entry; close: () => void}) {
  const loaded = useAsync(model, `detail:${entry.id}`, async () => {
    const [code, data] = await Promise.all([import('./Detail.tsx'), loadDetail(model, entry.id)])
    return {Component: code.Detail, data}
  })
  return loaded ? <loaded.Component entry={entry} data={loaded.data} /> : <aside className="detail"><p role="status">Loading record…</p><button onClick={close}>Close</button></aside>
}

type View = {Component: ComponentType<{population?: Bundle['population']}>; population?: Bundle['population']}
export function AsyncView({model, view}: {model: Model; view: 'map' | 'trends' | 'index'}) {
  const loaded = useAsync<View>(model, `view:${view}`, async () => {
    if (view === 'map') return {Component: (await import('../views/MapView.tsx')).MapView}
    if (view === 'index') return {Component: (await import('../views/IndexView.tsx')).IndexView}
    const [code, population] = await Promise.all([import('../views/Trends.tsx'), loadPopulation(model)])
    return {Component: code.Trends, population}
  })
  return loaded ? <loaded.Component population={loaded.population} /> : <p className="notice" role="status">Loading view…</p>
}
