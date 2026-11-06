# Interwoven

An interactive chart of how science and technology build on one another, drawn as ink on paper.

From the repo root:

```bash
npm install
npm run dev
```

Then open http://localhost:5174. The other commands below run from this `web` folder.

## Reading the chart

- Time runs left to right, on the ruler and in the bands below it. **Compressed** gives more room to recent centuries and to periods with more entries. **Linear** gives every year the same width. The bar at the bottom right shows how many years its length covers at the middle of the view.
- Rows are grouped by subject family, and a thread stays on one strand where it can. Lines are only ever links the research states.
- Key discoveries are named first. Zooming in names more of what lies beneath them, and every other entry still shows as a mark.
- A named entry is a flag on a pole at its date. A solid square is technology and an open circle is science, whose names are in italic.
- A square drawn only at its corners, or a box with a broken border, is a use or availability inferred from context. A hollow diamond, or a dotted border, is an awareness proxy such as a publication. Their community, evidence and uncertainty are in the entry's details.
- A date reading "by 1200" is an upper limit, and "from 1200" a lower one. The other end is unknown, and a lower limit establishes neither continuing use nor an endpoint. A short tail on the mark says the same once rows have room for it.
- A broken line is a link still awaiting review.
- If an entry has no defensible date yet, **Awaiting a date** appears under the chart and opens as an index of what is waiting.

The type, spacing and chart rules are explained in [DESIGN.md](DESIGN.md).

## Folding the sheet

**Drag along the ruler** to open a period. The rest of history is not zoomed away: it pleats into narrow strips, each saying how many years it holds, and links keep running across the folds. Detail appears in the open period as if you had zoomed into it.

Drag again to open a second period beside the first, up to three, and they share one scale. This puts, say, the 1780s and the 1950s side by side. Click a pleat on the ruler to unfold it, or press `u` to flatten the sheet. You can also type a period into Find, such as `1600 to 1700`.

## Views

| Key | View | What it shows |
| --- | --- | --- |
| `1` | **Threads** | Everything, on strands grouped by subject |
| `2` | **Stories** | One thread lifted out and laid out to read, with its text beside it |
| `3` | **Reach** | One row per entry: how long it went on being built on, and what is documented about its end |
| `4` | **Density** | Entries per year as a hatched silhouette |

**Stories.** Choose a thread from the list, or click any entry twice (or press `f`) to follow what led to it and what it made possible. Each entry gets its own row in date order, and links turn into corners that drop from a parent and run to its child, so no line crosses a title. A story keeps to one scale of real years. Gaps too long to fit are folded and say how long they are. Arrow keys move through it.

**Reach.** Links become vertical lines hanging from horizontal rules. Two things are drawn separately and must not be confused:

- **Influence reach**, worked out from the links: a rule from an entry to its latest descendant. It is firmer as far as something was built on directly, fine through later entries, and broken where it rests only on links awaiting review. It measures how long something went on being built on in the research so far, not how long it existed.
- **Documented life**, from dated events: a heavy stroke over the stretch the evidence covers, a short upright for evidence of use or sale, a closing bracket for withdrawal from sale, a cross for abandonment. A date such as "by 2023" keeps a dotted tail, because it is only a latest date.

Where the evidence stops, three dots and a question mark say so. They are the same length everywhere, because they measure nothing. They only disappear when the research documents an end and does not call last use unknown. The notes give live counts of what is documented, including the stages with nothing yet, so this view fills in as research lands. Rows can be ordered by thread, date or reach. Where one line breaks at a crossing, that is a drafting convention to show the lines are not connected, and which one goes over means nothing.

## Moving around

| Action | Trackpad | Mouse | Touch |
| --- | --- | --- | --- |
| Pan | Two-finger scroll | Drag | Drag |
| Zoom | Pinch | Wheel | Pinch diagonally |
| Zoom time only | Pinch or scroll over the ruler, or hold Option | Wheel over the ruler, or hold Option | Pinch sideways |
| Zoom height only | Scroll over the left margin, or Shift and pinch | Wheel over the left margin | Pinch upright |

Dragging either end of the bracket in the strip at the bottom stretches it, which also zooms time alone.

Going deeper reveals more of the science: first more names, then a sentence, then an entry's whole summary.

**Keys:** `1`-`4` views, `l` labels, `w` entries awaiting a date, `/` or `⌘K` find, `f` follow the selected entry, `u` unfold slowly, `0` fit and unfold, `+` `-` zoom, `[` `]` zoom time, `{` `}` zoom height, arrows pan or step through a story, `Esc` closes.

Find works on the chart rather than over it. Matches light up where they are as you type. A year goes there, and a period opens it.

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
- **Families:** each label belongs to one subject family in `FAMILIES` in `scripts/import-research.ts`, which sets its ink and where it sits on the chart.
- **Labels:** the research data has no labels yet, so they come from the rules in `scripts/import-research.ts`. Each node can match several, and the first sets its ink. To set a node's labels yourself, add it to `data/label-overrides.json`:

  ```json
  { "elec-volta-batteries-1800": ["batteries", "electromagnetism"] }
  ```

  A `labels` array on a research node also takes effect, and overrides win over both. A new label id needs a matching `LABEL_RULES` or `DISPLAY_LABELS` entry for its name and ink. The explicit display assignments cover entries whose subject is not recognized by the existing rules.

### Lifecycle evidence

Every entry's lifecycle stages and dated events are in `timeline.json`. The app treats an entry with nothing beyond "not yet researched" as unresearched, never as ended or continuing.

## Testing with other data

- `/?stress=50000` generates that many synthetic nodes to test rendering.

```bash
npm test
npm run build
```

## How it works

| Path | Purpose |
| --- | --- |
| `src/data/model.ts` | Builds the graph the chart draws from the data file |
| `src/data/layout.ts` | Places entries on strands, grouped by subject family |
| `src/data/derive.ts` | Reach, rows, stories and reading a typed date |
| `src/data/lifecycle.ts` | What counts as evidence of a later life |
| `src/engine/folds.ts` | The piecewise map that folds the time axis, shared with the shaders |
| `src/engine/camera.ts` | Separate time and height zoom, and flights |
| `src/engine/wheel.ts` | Telling a trackpad from a mouse wheel |
| `src/engine/time.ts` | The time axis, shared with the shaders through a lookup table |
| `src/engine/shaders.ts` | Lines, marks and date spans, in GLSL |
| `src/engine/Engine.ts` | WebGL 2 rendering, input and animation |
| `src/engine/overlay.ts` | Flags, progressive names and the ruler, on a canvas above the GL layer |
| `src/ui/` | React interface |

The stack is Vite, React, TypeScript, Tailwind and WebGL 2. Node data lives in GPU textures, so nodes and links read from one source and frames are only drawn when something changes. Views differ by a position per entry that eases in the texture, a fold map applied in the vertex shaders, and two uniforms that turn each link from a curve into a stitch or a corner, so moving between views is one continuous drawing.
