# The app's design

The app is a set of views over one dataset. This page records the decisions that hold it together. The values live in `app/src/styles.css` for the interface and `app/src/theme.ts` for everything drawn on a canvas, and the two must agree.

## Three choices, shared by every view

| Choice | Options | What it changes |
| --- | --- | --- |
| **Time** | People alive, Calendar, Logarithmic | How time is spread across the page |
| **Colour** | Subject, Region, Kind, Origin | What a colour means, and what the timeline's rows are |
| **Links** | Built on, Passed on, Independent, Related | Which stated links are drawn. None by default |

A fourth piece of state, the stretch of time in view, is set on the strip at the bottom. Every view reads these four and none of them owns one. Changing view keeps them, so the same question can be put to the timeline, the map and the trend chart in turn. The address bar records the whole state, so any view can be linked to.

Adding a view means reading that state and drawing. Adding a time scale means adding one function to `time.ts`. Adding something to colour by means adding one entry to `dims.ts`.

## The views

**Timeline.** One square per discovery, at its earliest record. Squares that would overlap stack, so a pile is a count that can be checked by eye. The most consequential discoveries sit at the bottom of a pile and are drawn at full strength; the rest are lighter. The landmarks are named where there is clear paper above the piles. Rows can be split by whatever colour means, or combined into one shape.

**Map.** One dot per discovery, at its most precise known place, on an equal-area projection with no borders. Several discoveries at one place bloom into a countable cluster. A place known only as a country or region is drawn as a ring, never as a precise point. The stretch of time in view is drawn in full; what came before it stays as a faint trace; what comes after is absent. Play sweeps time forward.

**Trends.** How many discoveries fall in each equal stretch of the axis: as a count, per century, or per billion person-years lived. World population sits underneath on its own axis.

**Index.** Every record as a sortable table, under a summary of how far each facet has been researched. This is the working view.

A sheet at the right shows one record in full, and marks each value by where it came from.

## Time scales

| Scale | Equal widths hold | Good for |
| --- | --- | --- |
| People alive | Equal person-years lived | Comparing discovery with the number of people who could have made it |
| Calendar | Equal years | Recent centuries, read plainly |
| Logarithmic | Ten times as many years with each step back | The whole 200,000 years on one page |

On the people scale, a pile's height is a rate per person. A period that looks dense produced more discoveries for each human lifetime lived in it.

The strip at the bottom uses the chosen scale, except on a calendar, where nearly all the data would sit in its last sliver. It uses the logarithm there.

## Honesty

- **The charts show research, not history.** The dataset is selective and growing. Each view that counts things says so in its caption.
- **Dates keep their uncertainty.** A discovery is placed at the latest date its earliest record allows. The sheet shows the date as written, such as "by c. 900 BCE".
- **Places keep their precision.** See the map above.
- **Unchecked values are marked.** In the sheet, a filled dot means the value comes from cited evidence, and a hollow amber one means it was entered from memory and is waiting to be checked. Every coordinate is currently of the second kind.
- **Only established links are drawn.** Candidate links appear in the sheet as open questions.

## Type

Source Serif 4, self-hosted in `app/src/fonts` under the SIL Open Font License. One family is used throughout.

| Use | Size / leading | Weight |
| --- | --- | --- |
| Name of the app | 25 / 32 | 600 |
| Title of a record | 23 / 28 | 600 |
| View names | 17 / 32 | 400, 600 when chosen |
| Summary in the sheet | 16.5 / 24 | 400 |
| Reading text | 15 / 22 | 400 |
| Controls, table cells | 14 / 20 | 400 |
| Notes, captions, axis labels | 12.5 to 13.5 | 400 |
| Section headings | 11.5 / 16, capitals, tracked 0.06em | 600 |

Italic means science, in names on the timeline, in the table and in the sheet. It is used for nothing else. Figures are lining, and tabular in columns.

## Colour

Paper `#f6f2e9`, sheet `#fcfaf5`, ink `#1f1b16` with two lighter inks for secondary text and notes. Rules are ink at 20% and 9%.

Colour belongs to the data. Six hues are assigned in a fixed order and never recycled: blue `#2a78d6`, orange `#eb6834`, aqua `#1baf7a`, yellow `#eda100`, magenta `#e87ba4`, green `#008300`. A neutral `#a8a091` stands for "not yet assessed" and "no place yet". The order passes a colour-vision check between neighbours on the paper background. Several hues are light against paper, so colour never carries identity alone: rows are headed, the legend is always present, and every mark answers to the pointer.

Text is always ink. It never takes a category's colour.

## Checks

`npm test` in `app/` covers the time scales, the ticks and the data model. The views are checked by eye at 1440 by 900, in each view, on each time scale.
