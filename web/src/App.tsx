import { useEffect } from 'react'
import { buildModel } from './data/model.ts'
import { makeStressDataset } from './data/stress.ts'
import type { RawDataset } from './data/types.ts'
import { validateDataset } from './data/validate.ts'
import { getEngine, useApp } from './store.ts'
import { BottomBar } from './ui/BottomBar.tsx'
import { DetailPanel } from './ui/DetailPanel.tsx'
import { FilterPanel } from './ui/FilterPanel.tsx'
import { Overview } from './ui/Overview.tsx'
import { Rails } from './ui/Rails.tsx'
import { SearchPalette } from './ui/SearchPalette.tsx'
import { TimelineCanvas } from './ui/TimelineCanvas.tsx'
import { Tooltip } from './ui/Tooltip.tsx'
import { TopBar } from './ui/TopBar.tsx'

async function load(): Promise<void> {
  const { setModel, setError } = useApp.getState()
  try {
    const response = await fetch(`${import.meta.env.BASE_URL}data/timeline.json`)
    if (!response.ok) throw new Error(`Could not load data/timeline.json (HTTP ${response.status}).`)
    let data = (await response.json()) as RawDataset

    const stress = Number(new URLSearchParams(location.search).get('stress'))
    if (stress > 0) data = makeStressDataset(data, Math.min(stress, 500000))

    const issues = validateDataset(data)
    const errors = issues.filter((i) => i.severity === 'error')
    if (errors.length) throw new Error(`Dataset has ${errors.length} error(s). First: ${errors[0]!.message}`)
    issues.forEach((i) => console.warn(`[data] ${i.message}`))
    setModel(buildModel(data, stress > 0), issues.map((i) => i.message))
  } catch (e) {
    setError(e instanceof Error ? e.message : String(e))
  }
}

function useKeyboard(): void {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const app = useApp.getState()
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        app.setSearchOpen(!app.searchOpen)
        return
      }
      if (e.key === 'Escape') {
        if (app.searchOpen) app.setSearchOpen(false)
        else if (app.selected !== null) app.select(null)
        else if (app.filtersOpen) app.setFiltersOpen(false)
        return
      }
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || e.metaKey || e.ctrlKey || e.altKey) return
      const engine = getEngine()
      // A shortcut changes the view, so a focus ring left on the last button would mislead.
      if (['1', '2', '3'].includes(e.key) && target instanceof HTMLButtonElement) target.blur()
      switch (e.key) {
        case '/':
          e.preventDefault()
          app.setSearchOpen(true)
          break
        case '1':
          app.setMode('network')
          break
        case '2':
          app.setMode('density')
          break
        case '3':
          app.setMode('steps')
          break
        case 'f':
          app.setFiltersOpen(!app.filtersOpen)
          break
        case '0':
          engine?.fit()
          break
        case '=':
        case '+':
          engine?.zoomBy(1.6)
          break
        case '-':
          engine?.zoomBy(1 / 1.6)
          break
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
}

export function App() {
  const error = useApp((s) => s.error)
  const synthetic = useApp((s) => s.model?.synthetic)
  useKeyboard()
  useEffect(() => void load(), [])

  return (
    <main className="relative h-full w-full select-none overflow-hidden">
      <TimelineCanvas />
      <TopBar />
      <FilterPanel />
      <Rails />
      <DetailPanel />
      <BottomBar />
      <Overview />
      <Tooltip />
      <SearchPalette />
      {synthetic && (
        <div className="glass pointer-events-none absolute left-1/2 top-[4.1rem] z-30 -translate-x-1/2 rounded-full px-3 py-1 text-xs text-ink-2">
          Synthetic stress-test data. Not real entries.
        </div>
      )}
      {error && (
        <div className="absolute inset-0 z-50 grid place-items-center p-6">
          <div className="glass max-w-lg rounded-2xl p-6" role="alert">
            <h1 className="text-base font-semibold">The timeline could not start</h1>
            <p className="mt-2 text-sm leading-relaxed text-ink-2">{error}</p>
          </div>
        </div>
      )}
    </main>
  )
}
