# Loading and research performance

JSON records remain authoritative and editable. `tools/build.py` produces two disposable read models: a versioned browser dataset and a local SQLite research index. Neither is edited by agents or committed. Validation continues to run against the original records.

## Browser artifacts

The initial HTML embeds the dataset manifest and preloads its content-addressed core in parallel with JavaScript. The core contains the fields used by the timeline, map, index, search and filters, all typed graph edges, lightweight entity names and the world population time axis. Narratives, events, evidence and source metadata live in one content-addressed detail file per discovery. A detail includes links touching either end and their evidence. Regional population series load with Trends. Map, Trends, Index and Detail code load only when used.

The compiler hashes deterministic UTF-8 output with SHA-256 (24 hexadecimal characters in filenames). The manifest is published last using atomic file replacement. Unchanged files retain their names and modification times. A record edit changes that record's detail, the core's detail pointer and the manifest. A link edit changes both endpoints' details. Changing a citation updates details using it. Old hashed files remain available to tabs opened before the change. Derived relationships do not become historical claims: only established links are drawn; walks filter direction, layer and status and track visited nodes.

Browser and research caches check file sizes and nanosecond modification times, including additions, deletions and builder changes. An unchanged browser build skips recompilation. Run `python3 tools/build.py --check` to force validation and a fresh browser compilation. If external tooling deliberately preserves both size and modification time, use this command and `python3 tools/research.py status --verify` for content-hash verification.

`npm run build` writes the production app to `app/dist`. Serve it with:

```bash
npm --prefix app run preview -- --port 4173
```

This uses the standard-library server in `tools/serve.py`, serving precompressed gzip and these policies:

| Response | Cache-Control |
| --- | --- |
| HTML and manifest | `no-cache` (ETag revalidation) |
| Hashed core, details, population and JS/CSS/font assets | `public, max-age=31536000, immutable` |

A different web server/CDN must implement the same headers, correct `Content-Encoding: gzip` and `Vary: Accept-Encoding`. Merely uploading `.gz` files does not enable compression. The development server gives hashed data immutable caching but development module loading is not a production performance measurement.

Deploy HTML after the referenced artifacts. Keep prior hashed data **and** JS/CSS assets for the lifetime of supported open tabs. Builds deliberately preserve old assets. Retention/garbage collection belongs to deployment policy; do not delete a live version's files. Missing or incompatible assets show a recovery action rather than an endless spinner. Detail and view loaders request code and data together, keep results scoped to the loaded core, and never substitute data from a different version.

## Research tools

```bash
python3 tools/research.py search 'steam engine'
python3 tools/research.py show clausiuss-heat-work-reconciliation
python3 tools/research.py walk clausiuss-heat-work-reconciliation --direction incoming --depth 4
python3 tools/research.py shared clausiuss-heat-work-reconciliation --kind person
python3 tools/research.py status --verify
```

Search treats words literally with AND semantics and uses SQLite FTS5, not arbitrary SQL. Results include source file paths. `show` returns the complete original JSON record. Directed walks default to established dependence/transmission links; explicit options select other layers or statuses. Maximum depth is bounded at 100. The database retains original records, events, sources and registers, plus indexed edges, shared entity memberships, research facet bases and citation relations.

A standalone command verifies source freshness before querying and rebuilds when necessary. For many queries, reuse one read-only connection to one consistent snapshot instead of repeatedly launching Python:

```python
from contextlib import closing
from research import connect, search, walk

with closing(connect()) as database:
    results = search(database, 'printing')
    ancestors = walk(database, results[0]['id'], depth=4)
```

Run from `tools/`, or add that directory to `PYTHONPATH`. Reconnect when new source edits should become visible. `PRAGMA foreign_key_check` and full record parity tests protect references and provenance. The SQLite file is atomically replaced during rebuild, so existing readers retain a complete old snapshot.

## Measurement and targets

Measurements use optimized production bundles in Chrome, the same current dataset for the historical and updated app, identical gzip/cache serving, 1440 × 900 viewports and repeated trials. Cold trials clear the browser HTTP cache and use a fresh context. Warm trials navigate again in that context. A separate check closes and relaunches Chrome with the same profile to verify disk-cache persistence. OS filesystem caches are warm; these are not cold-disk or real-user field measurements.

The primary loading metric is navigation to the first data-canvas draw plus the next animation frame. It includes the actual chart rather than only the loading notice. This is **not LCP** (canvas is not a normal LCP content candidate), and the interaction checks are not field INP. Resource sizes are collected after the initial font finishes loading. Detail-opening latency is measured inside the browser from selection to its first rendered frame, excluding Playwright action waiting.

Two profiles run: local/unthrottled and 10 Mbps download/upload, 40 ms emulated latency, 4× CPU slowdown. The controls load the same core and draw real discovery marks with plain canvas, omitting React, labels, collision layout, menus, filtering and details. These deliberately incomplete controls estimate the available headroom; they are **not** equivalent apps or proofs of a universal theoretical optimum. Research controls likewise separate `SELECT 1`, ID lookup, a resident adjacency traversal and bare Python startup from useful queries and freshness checks.

Initial engineering targets for this dataset and machine are local median startup below 100 ms, warm startup within a few display frames, throttled cold startup below 500 ms, first local detail below 100 ms, repeat detail within one or two frames, resident research searches below 1 ms at p95, and no network transfer of unchanged immutable assets on a warm navigation. These are substantially stricter loading targets than the general [Core Web Vitals guidance](https://developers.google.com/search/docs/appearance/core-web-vitals). They are laboratory budgets, not hardware-independent guarantees. Compare medians and p95, retain outliers, and do not infer global optimality from small samples.

## Reproduce

```bash
npm ci --prefix app
npm test
python3 tools/validate.py
npm run build
npm --prefix app run benchmark:baseline -- 4d37f65
npm --prefix app run benchmark -- --runs 9 --out docs/performance/2026-11-09/browser.json
python3 tools/benchmark.py --out docs/performance/2026-11-09/research.json
```

The browser harness uses an installed Chrome (`channel: 'chrome'`) and Playwright. Its baseline helper builds the historical app using today's data files; it does not switch the working branch or edit source records. Cache-invalidation fixtures are disposable copies. Results record the machine, browser, base commit, dataset version and asset hashes. `working_tree_dirty` is explicit when a benchmark measures an uncommitted implementation; the recorded compiled-HTML hash identifies that tested build.

The browser suite asserts lazy startup, one core request, zero warm immutable-asset transfer, reuse of details, all four views, search, deep links, recovery from a missing detail, browser-restart cache hits, new-version loading and old-tab consistency. Unit tests additionally cover every source/detail record, citations, deterministic builds, independent invalidation, graph cycles, shared ancestors, direction/status/layer filtering, query plans, manifest fallbacks and source freshness. See the dated measurement files for the observed results and limitations.
