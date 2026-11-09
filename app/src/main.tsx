import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App.tsx'
import './styles.css'
import { loadModel } from './data/load.ts'
import { useApp } from './store.ts'

// Begin consuming the preloaded core before React's first commit/effects.
void loadModel().then(useApp.getState().setModel, (error: Error) => useApp.getState().setError(error.message))

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
