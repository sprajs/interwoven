import { execFile } from 'node:child_process'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

const root = resolve(import.meta.dirname, '..')

/** Compiles `data/` into the file the app reads, at start-up and whenever the data changes. */
function dataset(): Plugin {
  let base = '/'
  let queued = Promise.resolve()
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
    configResolved(config) { base = config.base },
    buildStart: build,
    transformIndexHtml: {
      order: 'pre',
      async handler() {
        const manifest = JSON.parse(await readFile(resolve(root, 'app/public/data/manifest.json'), 'utf8'))
        return [
          {tag: 'link', attrs: {rel: 'preload', as: 'fetch', href: `${base}data/${manifest.core}`, crossorigin: 'anonymous'}, injectTo: 'head'},
          {tag: 'script', attrs: {id: 'dataset-manifest', type: 'application/json'}, children: JSON.stringify(manifest).replaceAll('<', '\\u003c'), injectTo: 'head'},
        ]
      },
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (/\/data\/(core|details|population)\/[a-f0-9]{24}\.json(?:$|\?)/.test(req.url ?? '')) res.setHeader('Cache-Control', 'public, max-age=31536000, immutable')
        next()
      })
      let timer: NodeJS.Timeout | undefined
      server.watcher.add(resolve(root, 'data'))
      server.watcher.on('all', (_event, path) => {
        if (!path.startsWith(resolve(root, 'data'))) return
        clearTimeout(timer)
        timer = setTimeout(() => {
          queued = queued.catch(() => {}).then(build)
          queued.then(
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
  build: { emptyOutDir: false },
}))
