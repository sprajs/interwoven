import { Component, useEffect, type ReactNode } from 'react'
import { AsyncDetail, AsyncView } from './ui/Async.tsx'
import { useApp } from './store.ts'
import { KeyLine } from './ui/KeyLine.tsx'
import { TimeBar } from './ui/TimeBar.tsx'
import { Tooltip } from './ui/Tooltip.tsx'
import { TopBar } from './ui/TopBar.tsx'
import { Timeline } from './views/Timeline.tsx'

export function App() {
  const model = useApp((s) => s.model)
  const error = useApp((s) => s.error)
  const view = useApp((s) => s.view)
  const selected = useApp((s) => s.selected)

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
        <main className="main">
          <p className="notice">{error ?? 'Reading the research…'}{error && <button onClick={() => location.reload()}>Reload</button>}</p>
        </main>
      </div>
    )
  }

  return (
    <div className="app">
      <TopBar />
      <KeyLine />
      <main className="main">
        <LoadBoundary key={view}>
          {view === 'timeline' ? <Timeline /> : <AsyncView model={model} view={view} />}
        </LoadBoundary>
      </main>
      {selected && model.byId.has(selected) && <LoadBoundary key={selected}><AsyncDetail model={model} entry={model.byId.get(selected)!} close={() => useApp.getState().select(null)} /></LoadBoundary>}
      <TimeBar />
      <Tooltip />
    </div>
  )
}

class LoadBoundary extends Component<{children: ReactNode}, {error: Error | null}> {
  state: {error: Error | null} = {error: null}
  static getDerivedStateFromError(error: Error) { return {error} }
  render() {
    return this.state.error ? <div role="alert" className="notice">{this.state.error.message} <button onClick={() => location.reload()}>Reload</button></div> : this.props.children
  }
}
