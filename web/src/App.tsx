import { useEffect } from 'react'
import { buildModel } from './data/model.ts'
import { makeStressDataset } from './data/stress.ts'
import type { RawDataset } from './data/types.ts'
import { indexLifecycle, type LifecycleFile } from './data/lifecycle.ts'
import { validateDataset } from './data/validate.ts'
import { followEntry, getEngine, stepStory, useApp } from './store.ts'
import { BottomBar } from './ui/BottomBar.tsx'
import { DetailPanel } from './ui/DetailPanel.tsx'
import { LabelsPanel } from './ui/LabelsPanel.tsx'
import { Overview } from './ui/Overview.tsx'
import { Rails } from './ui/Rails.tsx'
import { SearchPalette } from './ui/SearchPalette.tsx'
import { TimelineCanvas } from './ui/TimelineCanvas.tsx'
import { Tooltip } from './ui/Tooltip.tsx'
import { TopBar } from './ui/TopBar.tsx'
import { UnplacedPanel } from './ui/UnplacedPanel.tsx'

async function load(): Promise<void> {
  const { setModel, setError } = useApp.getState()
  try {
    const params = new URLSearchParams(location.search)
    const stress = Number(params.get('stress'))
    let data: RawDataset
    const usesResearch = !(stress > 0)
    if (stress > 0) {
      data = makeStressDataset(Math.min(stress, 500000))
    } else {
      const response = await fetch(`${import.meta.env.BASE_URL}data/timeline.json`)
      if (!response.ok) throw new Error(`Could not load data/timeline.json (HTTP ${response.status}).`)
      data = (await response.json()) as RawDataset
    }
    const issues = validateDataset(data)
    const errors = issues.filter((i) => i.severity === 'error')
    if (errors.length) throw new Error(`The dataset has ${errors.length} error(s). First: ${errors[0]!.message}`)
    issues.forEach((i) => console.warn(`[data] ${i.message}`))
    const model = buildModel(data, stress > 0)
    setModel(model)
    // The sidecar is optional. Without it every later life simply reads as not researched.
    if (usesResearch) {
      const response = await fetch(`${import.meta.env.BASE_URL}data/lifecycle.json`).catch(() => null)
      if (response?.ok) {
        const file = (await response.json()) as LifecycleFile
        useApp.getState().setLife(indexLifecycle(file, model.indexById), file.records)
      }
    }
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
        else if (app.mode === 'story' && app.story) {
          app.setStory(null)
          app.select(null)
        } else if (app.selected !== null || app.unplacedSelected !== null) app.select(null)
        else if (app.unplacedOpen) app.setUnplacedOpen(false)
        else if (app.labelsOpen) app.setLabelsOpen(false)
        else if (app.openPeriods > 0) getEngine()?.unfoldAll()
        return
      }
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || e.metaKey || e.ctrlKey || e.altKey) return
      const engine = getEngine()
      // A shortcut changes the view, so a focus ring left on the last button would mislead.
      if (['1', '2', '3', '4', '5'].includes(e.key) && target instanceof HTMLButtonElement) target.blur()
      const inStory = app.mode === 'story' && app.story !== null
      switch (e.key) {
        case '/':
          e.preventDefault()
          app.setSearchOpen(true)
          break
        case '1':
          app.setMode('threads')
          break
        case '2':
          app.setMode('story')
          break
        case '3':
          app.setMode('reach')
          break
        case '4':
          app.setMode('density')
          break
        case '5':
          app.setMode('landmarks')
          break
        case 'f':
          if (app.selected !== null) followEntry(app.selected)
          break
        case 'u':
          engine?.unfoldAll()
          break
        case 'w':
          app.setUnplacedOpen(!app.unplacedOpen)
          break
        case 'r':
          engine?.redraw()
          break
        case 'ArrowLeft':
          e.preventDefault()
          if (inStory) stepStory(-1)
          else engine?.panByKeys(e.shiftKey ? 240 : 80, 0)
          break
        case 'ArrowRight':
          e.preventDefault()
          if (inStory) stepStory(1)
          else engine?.panByKeys(e.shiftKey ? -240 : -80, 0)
          break
        case 'ArrowUp':
          e.preventDefault()
          if (inStory) stepStory(-1)
          else engine?.panByKeys(0, 80)
          break
        case 'ArrowDown':
          e.preventDefault()
          if (inStory) stepStory(1)
          else engine?.panByKeys(0, -80)
          break
        case '[':
          engine?.zoomBy(1 / 1.5, 'time')
          break
        case ']':
          engine?.zoomBy(1.5, 'time')
          break
        case '{':
          engine?.zoomBy(1 / 1.4, 'height')
          break
        case '}':
          engine?.zoomBy(1.4, 'height')
          break
        case 'l':
          app.setLabelsOpen(!app.labelsOpen)
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
  useKeyboard()
  useEffect(() => void load(), [])

  return (
    <main className="relative h-full w-full select-none overflow-hidden">
      <TimelineCanvas />
      <TopBar />
      <BottomBar />
      <Overview />
      <LabelsPanel />
      <UnplacedPanel />
      <Rails />
      <DetailPanel />
      <Tooltip />
      <SearchPalette />
      {error && (
        <div className="absolute inset-0 z-50 grid place-items-center p-6">
          <div className="sheet max-w-lg border border-rule p-8" role="alert">
            <h1 className="text-head">The chart could not be drawn</h1>
            <p className="mt-2 text-ink-2">{error}</p>
          </div>
        </div>
      )}
    </main>
  )
}
