import { useEffect } from 'react'
import { loadModel } from './data/model.ts'
import { useApp } from './store.ts'
import { Controls } from './ui/Controls.tsx'
import { Detail } from './ui/Detail.tsx'
import { TimeBar } from './ui/TimeBar.tsx'
import { Tooltip } from './ui/Tooltip.tsx'
import { TopBar } from './ui/TopBar.tsx'
import { IndexView } from './views/IndexView.tsx'
import { MapView } from './views/MapView.tsx'
import { Timeline } from './views/Timeline.tsx'
import { Trends } from './views/Trends.tsx'

export function App() {
  const model = useApp((s) => s.model)
  const error = useApp((s) => s.error)
  const view = useApp((s) => s.view)
  const selected = useApp((s) => s.selected)

  useEffect(() => {
    loadModel().then(useApp.getState().setModel, (e: Error) => useApp.getState().setError(e.message))
  }, [])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') useApp.getState().select(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  if (!model) {
    return (
      <div className="app">
        <header className="topbar">
          <h1 className="brand">Interwoven</h1>
        </header>
        <div />
        <main className="main">
          <p className="notice">{error ?? 'Reading the research…'}</p>
        </main>
      </div>
    )
  }

  return (
    <div className="app">
      <TopBar />
      <Controls />
      <main className="main">
        {view === 'timeline' && <Timeline />}
        {view === 'map' && <MapView />}
        {view === 'trends' && <Trends />}
        {view === 'index' && <IndexView />}
      </main>
      {selected && model.byId.has(selected) && <Detail key={selected} entry={model.byId.get(selected)!} />}
      <TimeBar />
      <Tooltip />
    </div>
  )
}
