# The design system

Interwoven asks a lot of a reader: time, links, evidence and doubt on one sheet. Typography carries most of that, so its decisions are written down here and enforced by `src/design.test.ts`. The numbers live in `src/design.ts` for the canvas and `src/styles.css` for the interface.

## What the sources say

| Source | What it says, in short | What we took from it |
| --- | --- | --- |
| [Butterick, Point size](https://practicaltypography.com/point-size.html) | Web body text at 15 to 25px, and fonts of the same size can look quite different | A 17px base, because this font runs small |
| [Butterick, Line spacing](https://practicaltypography.com/line-spacing.html) | 120 to 145% of the point size, tighter as type gets smaller | Every step falls in that range, and the test checks it |
| [Butterick, Line length](https://practicaltypography.com/line-length.html) | 45 to 90 characters including spaces | Sheet width is set from a measured character count |
| [Butterick, Headings](https://practicaltypography.com/headings.html) | Bump size by the smallest visible increment, at most three levels, and do not stack signals. Space is the most effective signal | Section headings stay small, separated by weight, a rule and space |
| [Butterick, Tables](https://practicaltypography.com/tables.html) | Turn off borders and add back only those that help | Tables keep one fine rule per row and no columns |
| [Bringhurst via Rutter, 2.1.2](http://webtypography.net/2.1.2) | 45 to 75 characters for a single column, with 66 widely held to be ideal, and 40 to 50 across multiple columns | Columns of notes are set to 48 characters |
| [Bringhurst via Rutter, 2.2.2](http://webtypography.net/2.2.2) | Vertical rhythm comes from one base unit, and every spacing and image sits on multiples of it | A 6px unit, half of a 12px leading module |
| [Bringhurst via Rutter, 3.1.1](http://webtypography.net/3.1.1) | Start with a modest set of distinct, related sizes | Five steps |
| [Bringhurst via Rutter, 3.2.1](http://webtypography.net/3.2.1) | Old-style figures in lowercase text, lining figures with capitals | Could not be adopted, see "What the font cannot do" |
| [Mortensen, The typographic scale](https://spencermortensen.com/articles/typographic-scale/) | A scale is a base, a ratio and a number of notes per interval. Titles run at about twice the body | Title is 1.7 times the body |
| [Brown, More Meaningful Typography](https://alistapart.com/article/more-meaningful-typography/) | Modular scales are educated suggestions, and rounding them is fine | Sizes are rounded to whole pixels, which also render more crisply |
| [Tufte, Sparklines](https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/) | Clutter comes from figure and ground of similar weight. Avoid frames, since placement already implies a grid. Make small graphics word-sized | Chrome stays lighter than data, no boxes, and the unplaced marks are a word-sized graphic |
| [Tufte CSS](https://edwardtufte.github.io/tufte-css/) | Greyscale text with colour kept for figures, and notes placed next to what they refer to | Text never takes a series colour, and sentences sit on the chart |
| [Wikipedia on map typography, citing Imhof and Bertin](https://en.wikipedia.org/wiki/Typography_(cartography)) | Legibility, association, hierarchy, distribution. Weight and size are ordinal, and italic is a convention for water. Set a label close to its symbol without touching it | Rank uses size then ink, italic is one category, names sit one unit from their marks |
| [Howarth, Lettering](https://jeffhowarth.github.io/cart-patterns/patterns/lettering) | Labels have right of way over lines, and a label and symbol that share a form are easier to connect. Legends split attention | Paper halos around words, marks as tall as the lowercase, and direct labels over a key |
| [WCAG 2.2, 1.4.3](https://www.w3.org/TR/WCAG22/#contrast-minimum) | 4.5:1 for normal text | All three inks pass, and the test checks both papers |

Many of these reached us through Rutter's web edition of Bringhurst and through summaries of Tufte and Imhof, rather than the books themselves. Müller-Brockmann's *Grid Systems* could only be checked through secondary descriptions, which agree that his modules derive from the baseline grid.

## What the font cannot do

The bundled EB Garamond is a subset. Reading its feature table shows `dnom frac liga locl numr pnum rlig tnum` and no `onum` or `smcp`, so:

- **It has no old-style figures.** The earlier `font-variant-numeric: oldstyle-nums` had no effect and has been removed. All figures are lining, which is right on a ruler and less ideal in running text.
- **It has no small caps,** and faked ones are worse than none, so section headings do not use them.
- **Its x-height is 0.40em and its average character is 0.376em** including spaces, both measured from the font. Small x-height is why the base is 17px and not 16px, and these figures are what the measure rules are computed from.

The full upstream EB Garamond has both features. Adopting it would mean old-style figures in text and small-cap headings, and is the obvious next step.

## The system

### Type

Five steps by 6:5 from 17px, rounded to whole pixels, each on a leading made of whole units.

| Step | Size / leading | Leading % | Used for |
| --- | --- | --- | --- |
| `title` | 29 / 36 | 124 | The name of the chart |
| `head` | 24 / 30 | 125 | The title of a sheet or entry |
| `lead` | 20 / 24 | 120 | Landmark names on the chart, the search field |
| `body` | 17 / 24 | 141 | Reading text, view names, major names on the chart |
| `note` | 14 / 18 | 129 | Everything secondary: dates, captions, the ruler, tables, minor names |

6:5 is the smallest ratio whose steps can be told apart at a glance on this face. Anything finer gave neighbouring sizes that looked like mistakes, and anything coarser had too few usable steps between 14 and 29.

### Three voices, one meaning each

- **Roman** is the default.
- **Italic means science,** everywhere, as maps set water apart. It is never used for captions, hints or emphasis. The chart used it for all of those, which diluted the one thing it encodes. The test forbids any other use in the interface.
- **Weight 500** appears once, on small section headings, where it stands in for the size change they do not get. Bold plus italic never happens.

### Rank on the chart

Size for the first three tiers and ink for the last: `lead`, `body`, `note`, then `note` in a lighter ink. In the reach view's tight rows the sizes step down one, as Priestley kept names small. Weight is not used, so a name's rank reads from one signal at a time.

A mark's diameter equals the x-height of its name (0.40 × size), so a mark and its word read as one object. The earlier size bonus for well-linked entries is gone: it encoded something nothing explained.

### Space

A 6px unit, half of which (3px) is available for tight optical gaps. In the interface `--spacing: 3px`, so `p-2` is 6px, `p-4` is 12px and `p-8` is 24px. Only 0, 1, 2, 3, 4, 6, 8, 12, 16, 18 and 24 are allowed. All page geometry in `LAYOUT` is a whole number of units.

### Measure

| Where | Width | Characters |
| --- | --- | --- |
| Side sheet, body | 336px inside 384px | 53 (range 45 to 90) |
| Sentences on the chart, notes in columns | 252px | 48 (range 40 to 50) |

### Ink and rules

| Token | Value | Contrast on paper | Used for |
| --- | --- | --- | --- |
| `ink` | `#26211c` | 13.9 | Names and reading text |
| `ink-2` | `#4e463c` | 8.1 | Secondary reading text |
| `ink-3` | `#6a6156` | 5.3 | Notes |
| `rule` | ink at 22% | | Structure: under headings, around sheets |
| `rule-soft` | ink at 11% | | Between rows |

Three line weights: 0.75 hair, 1 rule, 1.5 stroke. Colour belongs to the data: text only ever uses the inks above.

## Designing for a sparse chart

Only entries with a selected, researched date are on the chart, so it may start small and fill in. These decisions switch themselves off as the data grows: with every entry placed there are no loose threads and no row of marks waiting, and above 60 entries depth takes over again.

- **Everything shows.** Below 60 entries, depth does not hide any, the depth control goes away, and dates sit under names, because a chart this size can be read whole.
- **Loose threads.** A link to an entry with no date cannot be drawn to anywhere, so it is drawn as a short fine thread leaving the mark, all one length because it measures nothing. Right is what the entry led to and left is what it built on. These are the places the chart will grow from.
- **Reach follows links through undated entries,** which can carry a reach on to a dated entry beyond them but never extend it themselves.
- **Awaiting a date is part of the piece.** Below the chart, a word-sized row of marks shows what is waiting, in no time order because it has none. It opens an index set like the back of a book: grouped, in columns, with the reasons counted at the top. Pointing at an entry lights what it is already linked to on the chart, which stays in view.

## Marks that qualify evidence

A mark says how far to trust its date, not only what it is. An awareness proxy is a hollow diamond and an inference is a broken ring, each with a word beside its name on the chart, so neither reads as an ordinary documented entry. A short open arrow says a date is a limit on one side only, and the unknown end is left undrawn. These sit in the key with the other marks, and take their sizes from the same steps.

## Checks

`npm test` runs `src/design.test.ts`, which fails on:

- a type size or leading outside the scale, in the interface or on the canvas
- an arbitrary length, an unnamed breakpoint or an off-scale space in the interface
- italic used for anything but science
- a leading outside 120 to 145%, or a step off the unit
- a measure outside its range
- an ink below 4.5:1, or a stylesheet value that differs from `design.ts`
