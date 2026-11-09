import { buildModel, type Model } from './model.ts'
import type { Bundle, CoreBundle, DetailData, Manifest } from './types.ts'

const FORMAT = 1
const base = `${import.meta.env.BASE_URL}data/`
async function read<T>(file: string): Promise<T> {
  if (!/^(manifest\.json|(?:core|details|population)\/[a-f0-9]{24}\.json)$/.test(file)) throw new Error('Invalid dataset asset path')
  const response = await fetch(base + file, {cache: file === 'manifest.json' ? 'no-cache' : 'default'})
  if (!response.ok) throw new Error(`Research could not be loaded (${response.status}). Reload to get the latest version.`)
  return response.json() as Promise<T>
}

let pending: Promise<Model> | undefined
/** Deduplicate StrictMode and simultaneous consumers; failed requests remain retryable. */
export function loadModel(): Promise<Model> {
  return pending ??= (async () => {
    const embedded = document.getElementById('dataset-manifest')?.textContent
    const manifest: Manifest = embedded ? JSON.parse(embedded) : await read('manifest.json')
    if (manifest.format !== FORMAT) throw new Error('This dataset needs a newer app. Reload this page.')
    const core = await read<CoreBundle>(manifest.core)
    if (core.format !== FORMAT) throw new Error('This dataset needs a newer app. Reload this page.')
    return buildModel(core)
  })().catch(error => { pending = undefined; throw error })
}

const cache = new WeakMap<Model, Map<string, Promise<unknown>>>()
function resource<T>(model: Model, file: string): Promise<T> {
  let resources = cache.get(model)
  if (!resources) { resources = new Map(); cache.set(model, resources) }
  const existing = resources.get(file)
  if (existing) return existing as Promise<T>
  // Keep rejected promises stable for React.use; the error boundary offers a reload.
  const promise = read<T>(file)
  resources.set(file, promise)
  return promise
}
export function loadDetail(model: Model, id: string): Promise<DetailData> {
  const file = model.bundle.details[id]
  if (!file) return Promise.reject(new Error(`Unknown discovery: ${id}`))
  return resource<DetailData>(model, file)
}
export function loadPopulation(model: Model): Promise<Bundle['population']> {
  return resource(model, model.bundle.population_file)
}
