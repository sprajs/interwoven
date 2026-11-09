import { execFile } from 'node:child_process'
import { resolve } from 'node:path'
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

const root = resolve(import.meta.dirname, '..')

/** Compiles `data/` into the file the app reads, at start-up and whenever the data changes. */
function dataset(): Plugin {
  const build = () =>
    new Promise<void>((done, fail) => {
      execFile('python3', [resolve(root, 'tools/build.py')], (error, stdout, stderr) => {
        if (error) fail(new Error(stderr || error.message))
        else {
          console.log(stdout.trim())
          done()
        }
      })
    })
  return {
    name: 'interwoven-dataset',
    buildStart: build,
    configureServer(server) {
      let timer: NodeJS.Timeout | undefined
      server.watcher.add(resolve(root, 'data'))
      server.watcher.on('all', (_event, path) => {
        if (!path.startsWith(resolve(root, 'data'))) return
        clearTimeout(timer)
        timer = setTimeout(() => {
          build().then(
            () => server.ws.send({ type: 'full-reload' }),
            (error: Error) => console.error(error.message),
          )
        }, 300)
      })
    },
  }
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), ...(mode === 'test' ? [] : [dataset()])],
  server: { port: 5175, strictPort: true },
}))
