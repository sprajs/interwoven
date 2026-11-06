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

Then open http://localhost:5174. While the server runs, the chart rebuilds itself whenever the research changes.

Each folder has its own README, and `web/DESIGN.md` explains the chart's design. `AGENTS.md` has the working rules for this repository.
