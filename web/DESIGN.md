# The design system

Interwoven asks a lot of a reader: time, links, evidence and doubt on one sheet. Its decisions are written down here and enforced by `src/design.test.ts`. The numbers live in `src/design.ts` for the canvas and `src/styles.css` for the interface.

## The chart

**Time is the strongest thing on the page.** A ruler of dark and light cells runs across the top, like a map's scale bar, with each cell headed by the year it starts. The same cells carry down the chart as bands of tone, so a date can be read from anywhere. Each stretch of the ruler divides as finely as it has room for, at one step, so it reads 1800, 1850, 1900. Whatever has your attention drops a line to the ruler, which shows its date.

**Entries sit on strands.** A linked entry takes the row of its neighbour if it can, so a thread reads as one line, as on a transit map. A row is held from an entry to the next on its thread, so nothing unrelated sits on a line it has nothing to do with. Threads stay together, and are grouped into six subject families, each with its own ink and a heading at the left of the view. Vertical position therefore means something: family first, then thread.

The research has many short threads and many entries with no links yet. The families are what hold these together on the page. No link is drawn that the research does not state.

**Names are progressive.** The page allows one name per fixed area of screen, and names enter by rank. Zooming in puts fewer entries in view, so the same allowance reaches further down: key discoveries first, then more and more of the tree beneath them. Every other entry still shows as a mark, and a line at the bottom says how many are named. With very few in view, a name opens to a sentence, then its whole summary.

**A named entry is a flag.** A box flies above or below its mark, with a solid pole at the date running down to it, so the mark and its strand stay visible. It takes whichever of four positions covers fewest other marks, and keeps that position as the page moves. It holds a short date on a tint of the entry's ink, then the name.

**The chart keeps the page.** Every view opens at full width. A side sheet opens only on request, and the view's own options sit on one quiet line under the chart.

**Density is made of entries.** Each mark stays at its true date and stacks on whatever it would otherwise cover, so a shape on the page is always a count that can be checked by eye. No curve, smoothing or scale stands between the record and the reader, which is why the view dropped its hatched silhouette. Names give way to the shape: only what has your attention is named. The pointer reads one year on the ruler, never a range. The caveat stays in sight, because the shape shows where research has reached, not how much happened.

### What marks and borders say

| | Mark on the strand | Border of its box |
| --- | --- | --- |
| Technology, direct evidence | Solid square | Whole |
| Science, direct evidence | Open circle, name in italic | Whole |
| Scoped inference of use or availability | Square drawn only at its corners | Broken |
| Awareness proxy, such as a publication | Hollow diamond | Dotted |
| Date known only as a limit | Short tail on the open side, once rows have room | The date reads "by 1200" or "from 1200" |
| Date known only as a range | Bar with end stops | The date reads "1608–1610" |

## Type

Source Serif 4, self-hosted in `src/fonts` under the SIL Open Font License. It replaced EB Garamond, whose lowercase is small (x-height 0.40em) and hard to read at label sizes on a screen. Source Serif's is 0.475em, it has optical sizes for small text, and unlike the earlier subset it keeps its old-style figures and true small caps.

The files are a subset of the upstream variable fonts in [google/fonts](https://github.com/google/fonts/tree/main/ofl/sourceserif4), limited to weights 400 to 700, optical sizes 8 to 32, Latin, Greek and common punctuation, and the features `kern liga ccmp locl mark mkmk onum lnum tnum pnum smcp c2sc case frac`. Regular is 170 KB and italic is 146 KB.

| Step | Size / leading | Leading % | Used for |
| --- | --- | --- | --- |
| `title` | 29 / 36 | 124 | The name of the chart |
| `head` | 24 / 30 | 125 | The title of a sheet or entry |
| `lead` | 20 / 24 | 120 | The search field |
| `body` | 17 / 24 | 141 | Reading text, view names, key discoveries on the chart |
| `note` | 14 / 18 | 129 | Dates, captions, the ruler, tables, other names on the chart |

Five steps of about 6:5. That ratio is a judgement: finer steps looked like mistakes, and coarser ones left too few sizes.

- **Roman** is the default.
- **Italic means science,** everywhere, as maps set water apart. It is never used for captions, hints or emphasis.
- **Weight** ranks names on the chart: 600 for the top two ranks, 500 for the rest. Section headings are 600 in small caps.
- **Figures:** old-style proportional in running text, where they sit quietly. Lining in dates and notes, where they must read at a glance. Tabular in columns of counts.

## Space and measure

A 6px unit, half of which (3px) is available for tight gaps. In the interface `--spacing: 3px`, so `p-2` is 6px, `p-4` is 12px and `p-8` is 24px. Only 0, 1, 2, 3, 4, 6, 8, 12, 16, 18 and 24 are allowed. All page geometry in `LAYOUT` is a whole number of units.

| Where | Width | Characters |
| --- | --- | --- |
| Side sheet, body | 372px inside 420px | 48 (range 45 to 90) |
| Notes on the chart | 270px | 42 (range 40 to 50) |

These use the font's measured average character, 0.454em.

## Ink

| Token | Value | Used for |
| --- | --- | --- |
| `ink` | `#1f1b16` | Names, reading text, the ruler's dark cells |
| `ink-2` | `#443c32` | Secondary reading text |
| `ink-3` | `#5c5347` | Notes |
| `rule` | ink at 22% | Under headings, around sheets, between families |
| `rule-soft` | ink at 11% | Between rows |

All text inks clear WCAG AA on both papers, and the ruler's light cell clears it too. Colour belongs to the data, as the six family inks. Text only ever uses the inks above. Family inks also have position and a written heading, so colour never carries identity alone.

## Sources

| Source | What we took from it |
| --- | --- |
| [Butterick, Point size](https://practicaltypography.com/point-size.html), [Line spacing](https://practicaltypography.com/line-spacing.html), [Line length](https://practicaltypography.com/line-length.html) | 15 to 25px for reading text, 120 to 145% leading, 45 to 90 characters |
| [Butterick, Headings](https://practicaltypography.com/headings.html) | Do not stack signals. Space is the most effective one |
| [Bringhurst via Rutter, 2.1.2](http://webtypography.net/2.1.2), [2.2.2](http://webtypography.net/2.2.2), [3.1.1](http://webtypography.net/3.1.1), [3.2.1](http://webtypography.net/3.2.1) | 40 to 50 characters across columns, rhythm from one unit, a modest set of sizes, old-style figures in text |
| [Tufte, Sparklines](https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/), [Tufte CSS](https://edwardtufte.github.io/tufte-css/) | Figure and ground of different weights, notes next to what they describe |
| [Wikipedia on map typography, citing Imhof and Bertin](https://en.wikipedia.org/wiki/Typography_(cartography)), [Howarth, Lettering](https://jeffhowarth.github.io/cart-patterns/patterns/lettering) | Size and weight are ordinal, italic as a category, labels placed to avoid symbols, direct labels over a key |
| [WCAG 2.2, 1.4.3](https://www.w3.org/TR/WCAG22/#contrast-minimum) | 4.5:1 for normal text |

Many of these reached us through Rutter's web edition of Bringhurst and through summaries of Tufte and Imhof, not the books themselves.

## Checks

`npm test` runs `src/design.test.ts`, which fails on a type size or leading outside the scale, an arbitrary length or off-scale space in the interface, italic used for anything but science, a measure outside its range, an ink below 4.5:1, or a stylesheet value that differs from `design.ts`.
