# Interwoven

An interactive chart of how science and technology build on one another, drawn as ink on paper.

From the repo root:

```bash
npm install
npm run dev
```

Then open http://localhost:5174. The other commands below run from this `web` folder.

## Reading the chart

- Time runs left to right. **Compressed** gives more room to recent centuries and to periods with more entries; **Linear** gives every year the same width.
- Vertical position has no scale. It comes from the links and shared labels, so related work drifts together without forming categories.
- A solid dot is a technology and an open ring is science. Science titles are set in italic.
- A thin bar with end marks is a date range. A broken line is a link still awaiting review.
- A hollow diamond and `[proxy]` label mark an awareness opportunity, such as a justified publication proxy. A broken ring and `[inferred]` label mark contextual use/availability inference. Their community, evidence, justification and uncertainty appear in details.
- A left-pointing arrow is a known-by upper date limit; a right-pointing arrow is a “not before” lower limit. A lower limit establishes neither continuing use nor a later endpoint. The unknown opposite end stays omitted.
- Zooming brings in deeper levels, from landmarks to fine detail.

**Views:** Threads shows placed entries and their links, Density counts placed entries per year as a hatched silhouette, and Landmarks isolates prominent placed entries. Unplaced keeps the remaining research accessible.

**Keys:** `1` `2` `3` switch views, `l` opens labels, `/` or `⌘K` searches, `0` fits everything, `+` `-` zoom, `Esc` closes.

## Data

The app reads `public/data/timeline.json`, which is generated. Do not edit it by hand.

While `npm run dev` runs, the chart updates itself: when anything in `research/science-technology-graph/data/` or `web/data/` changes, it rebuilds the file and reloads the page. This also covers data arriving through `git pull`. If an import fails, for example halfway through an agent's write, the last good chart stays up and the terminal says why.

To rebuild by hand, for example before a production build:

```bash
npm run import
npm run validate
```

`npm run import` reads `../research/science-technology-graph/data/*.jsonl` and never writes to that folder.

- **Dates:** each mark uses a deliberate, evidenced `community_entry` choice: actual availability, practical use, adoption, recognition, or a clearly justified public-awareness proxy in a named community. Evidence of FIRST commercial availability is preferred where meaningful; a dated offer can establish availability **by** a date while FIRST remains unknown. An earlier invention, discovery, observation or demonstration is never an automatic fallback.
- **Bounds:** `date_interpretation` preserves the selected event date while qualifying community entry as `event_date`, `known_by` or `known_from`. One-sided event dates also stay one-sided under `event_date`. No unknown opposite limit is fabricated. The full event and entry bounds remain in the generated data.
- **Evidence:** `direct`, `scoped_inference` and `awareness_proxy` remain distinct. Contextual inference is limited to use/availability; publication/presentation/disclosure proxies are never called adoption. Niche, local and failed branches are valid within their stated community and scope.
- **Lifecycle:** details retain the distinct event dates and explicit lifecycle unknowns. **Unplaced** retains records still awaiting a defensible selected entry and usable date; it does not substitute an earlier event.
- **Invalid selections:** the importer reports a selected choice that fails its community/evidence/date contract and leaves the last generated chart intact. It never silently downgrades that choice into a dated invention.
- **Relationships:** all source and receiving event references are retained in details. Community-entry display order does not determine whether a historical relationship is valid. Disconnected entries remain available.
- **Levels:** the research `tier` sets the zoom level, and a missing tier counts as level 2.
- **Labels:** the research data has no labels yet, so they come from the rules in `scripts/import-research.ts`. Each node can match several, and the first sets its ink. To set a node's labels yourself, add it to `data/label-overrides.json`:

  ```json
  { "elec-volta-batteries-1800": ["batteries", "electromagnetism"] }
  ```

  A `labels` array on a research node also takes effect, and overrides win over both. A new label id needs a matching `LABEL_RULES` or `DISPLAY_LABELS` entry for its name and ink. The explicit display assignments cover entries whose subject is not recognized by the existing rules.

## Stress test

- `/?stress=50000` generates that many synthetic nodes to test rendering.

```bash
npm test
npm run build
```

## How it works

| Path | Purpose |
| --- | --- |
| `src/data/model.ts` | Builds the graph and the force-based vertical layout |
| `src/engine/time.ts` | The time axis, shared with the shaders through a lookup table |
| `src/engine/shaders.ts` | Pen strokes, marks, date spans and paper, in GLSL |
| `src/engine/Engine.ts` | WebGL 2 rendering, input and animation |
| `src/engine/overlay.ts` | Canvas text placement and the axis |
| `src/ui/` | React interface |

The stack is Vite, React, TypeScript, Tailwind and WebGL 2. Node data lives in GPU textures, so nodes and links read from one source and frames are only drawn when something changes.
