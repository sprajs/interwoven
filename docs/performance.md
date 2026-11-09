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

Search treats words literally with AND semantics and uses SQLite FTS5, not arbitrary SQL. Results include source file paths and stored summaries. Add `--snippets` for matching highlighted excerpts; generating them is measured separately because it costs more than locating and ranking the records. `show` returns the complete original JSON record. Directed walks default to established dependence/transmission links; explicit options select other layers or statuses. Maximum depth is bounded at 100. The database retains original records, events, sources and registers, plus indexed edges, shared entity memberships, research facet bases and citation relations.

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
python3 tools/performance_report.py docs/performance/2026-11-09
```

The browser harness uses an installed Chrome (`channel: 'chrome'`) and Playwright. Its baseline helper builds the historical app using today's data files; it does not switch the working branch or edit source records. Cache-invalidation fixtures are disposable copies. Results record the machine, browser, base commit, dataset version and asset hashes. `working_tree_dirty` is explicit when a benchmark measures an uncommitted implementation; the recorded compiled-HTML hash identifies that tested build.

The browser suite asserts lazy startup, one core request, zero warm immutable-asset transfer, reuse of details, all four views, search, deep links, recovery from a missing detail, browser-restart cache hits, new-version loading and old-tab consistency. Unit tests additionally cover every source/detail record, citations, deterministic builds, independent invalidation, graph cycles, shared ancestors, direction/status/layer filtering, query plans, manifest fallbacks and source freshness. See the dated measurement files for the observed results and limitations.

## Measurements on 9 November 2026

Apple M3 Pro, Chrome 157.0.8103.38, 400 discoveries / 720 events / 181 link records (155 established). The app implementation measured is `fd07484`; the historical app is `4d37f65` compiled with the same 400-record data. Nine trials per row. Times below are navigation to a data-canvas frame, in milliseconds.

| Profile / browser cache | Previous median | Updated median | Updated p95 | Minimal control median |
| --- | ---: | ---: | ---: | ---: |
| Local / cold | 100.1 | 67.0 | 70.8 | 27.2 |
| Local / warm | 63.4 | 32.4 | 33.1 | 14.8 |
| 10 Mbps, 40 ms, CPU 4× / cold | 1,397.4 | 461.4 | 480.0 | 245.0 |
| 10 Mbps, 40 ms, CPU 4× / warm | 332.9 | 178.4 | 188.3 | 98.0 |

The updated app transfers about 405 KB on a cold navigation versus 1,177 KB previously, including the initial font and browser-reported response overhead. Warm navigation transfers none of the hashed data, JS, CSS or fonts; only HTML is revalidated (300 browser-reported bytes). The 330 ms initial baseline outlier is retained in the raw data and its p95; the process is shared across trials, so these measure cold HTTP caches rather than a fresh Chrome process every time.

Single-sample functional probes measured a first detail at 32.6 ms and its repeat at 11.3 ms, a navigation after changing the dataset at 66.6 ms, and a navigation after closing/relaunching Chrome at 263.9 ms. The restart test confirmed disk-cache hits for the core and assets. It still pays browser initialization/rendering costs; disk caching does not imply the same timing as an already-running browser. The detail probe includes any residual initial-page work and is not a nine-trial detail benchmark.

The final research implementation stores summaries for fast results, with highlighted matching excerpts available using `--snippets`. Source freshness checks use a single directory traversal with cached directory-entry metadata. Python 3.14.6 and SQLite 3.53.2 measured:

| Operation | Median | p95 | Samples |
| --- | ---: | ---: | ---: |
| Ranked search with summaries, eight queries | 0.040–0.129 ms | 0.053–0.160 ms | 101 per query |
| Search with highlighted excerpts (`water`) | 0.909 ms | 1.406 ms | 101 |
| Incoming graph walk, depth 4 | 0.145 ms | 0.505 ms | 101 |
| Shared entity lookup | 0.032 ms | 0.074 ms | 101 |
| Freshness-checked connection and search | 6.738 ms | 8.084 ms | 31 |
| Standalone CLI search, including Python startup | 79.731 ms | 95.788 ms | 11 |
| Unchanged browser-data build, including Python startup | 89.435 ms | 95.848 ms | 11 |

A complete research-index rebuild took 442 ms in one sample. Reading all source JSON alone took a median 57 ms; that is an ingestion reference, not an equivalent ranked query. Reusing a research connection avoids process launch and repeated freshness scans while retaining a consistent dataset snapshot. The research result records the exact query-source SHA-256 and dataset/builder fingerprint because the final query optimization was measured before its commit.

The functional suite passed 44 Python tests and 53 TypeScript tests, plus the browser suite. Deployment cache headers, single-record and link invalidation, source additions/deletions, timestamp-preserving edits, old SQLite readers, old browser tabs, failed detail recovery and deep links were checked. Browser comparisons have small sample sizes and run on one machine without exclusive hardware access; they establish a substantial improvement and the stated lab budgets, not universal or theoretical optimality. Warm local startup is about one frame above the deliberately incomplete control. The cold/throttled app still has measurable framework, layout and text-rendering overhead.

[Raw browser samples](performance/2026-11-09/browser.json), [research timings](performance/2026-11-09/research.json), [summary values](performance/2026-11-09/summary.json), [comparison figure](performance/2026-11-09/comparison.svg), and [verified timeline screenshot](performance/2026-11-09/timeline.png).
