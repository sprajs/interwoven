# Interwoven

An interactive chart of how science and technology build on one another, and the research behind it.

| Folder | What it holds |
| --- | --- |
| `research/science-technology-graph` | The research: entries, events, links and sources as JSONL, with the evidence, reviews and tools that maintain them |
| `web` | The chart. It reads the research and never writes to it |

```bash
npm install
npm run dev
```

Binary evidence is a local download cache. Each item has a small committed `.cache.json` descriptor beside its ignored PDF, JPG or PNG. The chart and research JSON remain usable without downloading that cache. See the [evidence workflow](research/science-technology-graph/README.md#evidence-storage) for fetching, capturing and verifying individual sources.

For a new checkout, `git clone --filter=blob:none https://github.com/sprajs/big_idea.git` avoids eagerly downloading binaries retained in older Git history. Current binary evidence uses neither ordinary Git nor Git LFS.

Then open http://localhost:5174. While the server runs, the chart rebuilds itself whenever the research changes.

Each folder has its own README, and `web/DESIGN.md` explains the chart's design. `AGENTS.md` has the working rules for this repository.
