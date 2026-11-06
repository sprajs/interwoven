// Keeps the chart current while the dev server runs. When the research data changes it
// rebuilds public/data/timeline.json and reloads the page, but only if the chart would
// actually change. A failed import leaves the last good chart in place.
import { spawn } from 'node:child_process'
import { existsSync, readFileSync, watch, type FSWatcher } from 'node:fs'
import { join, resolve } from 'node:path'
import type { Plugin } from 'vite'

/** Long enough to let an agent finish writing all four data files. */
const SETTLE_MS = 1500

export function researchSync(): Plugin {
  return {
    name: 'research-sync',
    apply: 'serve',
    configureServer(server) {
      const web = server.config.root
      const dataDir = resolve(web, '../research/science-technology-graph/data')
      const overridesDir = join(web, 'data')
      const output = join(web, 'public/data/timeline.json')
      const log = (message: string) => server.config.logger.info(`[research-sync] ${message}`, { timestamp: true })

      if (!existsSync(dataDir)) {
        log(`no research data at ${dataDir}, so the chart will not update automatically`)
        return
      }

      const read = () => (existsSync(output) ? readFileSync(output, 'utf8') : '')
      let timer: ReturnType<typeof setTimeout> | undefined
      let running = false
      let again = false

      const run = () => {
        if (running) {
          again = true
          return
        }
        running = true
        const before = read()
        const child = spawn(process.execPath, ['--no-warnings', 'scripts/import-research.ts'], { cwd: web })
        let text = ''
        child.stdout.on('data', (chunk) => (text += chunk))
        child.stderr.on('data', (chunk) => (text += chunk))
        const done = (ok: boolean) => {
          running = false
          if (!ok) log(`import failed, keeping the last good chart:\n${text.trim()}`)
          else if (read() !== before) {
            log(text.trim().split('\n').pop() ?? 'updated')
            server.ws.send({ type: 'full-reload', path: '*' })
          }
          if (again) {
            again = false
            schedule()
          }
        }
        child.on('error', () => done(false))
        child.on('close', (code) => done(code === 0))
      }

      const schedule = () => {
        clearTimeout(timer)
        timer = setTimeout(run, SETTLE_MS)
      }

      const watchers: FSWatcher[] = [dataDir, overridesDir].filter(existsSync).map((dir) =>
        watch(dir, (_event, file) => {
          if (file && /\.(jsonl?|json)$/.test(String(file))) schedule()
        }),
      )
      server.httpServer?.once('close', () => {
        clearTimeout(timer)
        watchers.forEach((w) => w.close())
      })

      log(`watching ${dataDir}`)
      run()
    },
  }
}
