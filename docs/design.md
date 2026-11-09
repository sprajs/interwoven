# The app's design

The app is a set of views over one dataset. This page records the decisions that hold it together. The values live in `app/src/styles.css` for the interface and `app/src/theme.ts` for everything drawn on a canvas, and the two must agree.

## The page belongs to the data

The bar at the top holds the app's name, the four views, and four buttons. Each button states one choice and opens a short list of the alternatives, each with a line saying what it does. Nothing else is laid out. An option is never shown until it is asked for.

| Button | Options | What it changes |
| --- | --- | --- |
| **Links** | Built on, Passed on, Independent, Related | Which stated links are drawn. None by default |
| **Time** | Population, Calendar, Logarithmic | How time is spread across the page |
| **Colour** | Subject, Region, Kind, Origin | What a colour means, and what the timeline's rows are. Its list also switches each category on and off, with how many are in view |
| **Show** | Everything or major only; rows split or together | Which discoveries are drawn |

A fifth piece of state, the stretch of time in view, is set on the strip at the bottom. Every view reads this state and none of them owns it. Changing view keeps it, so the same question can be put to the timeline, the map and the trend chart in turn. The address bar records the whole state, so any view can be linked to.

A quiet line under the bar says what the colours mean. It is left out where the page already says so, as on a timeline with a headed row for each category.

**Detail is one click away, never on the page by default.** The sheet for one record opens with its name, date, a one-sentence summary, what it built on and what followed, and where else the same thing was reached. Everything else sits in sections that open when asked for, and each heading says how much is inside. The index keeps its breakdown of research coverage behind a link in the same way.

Adding a view means reading the shared state and drawing. Adding a time scale means adding one function to `time.ts`. Adding something to colour by means adding one entry to `dims.ts`. A new choice gets a menu, built from `ui/Menu.tsx`.

## The views

**Timeline.** One square per discovery, at its earliest record. Squares that would overlap stack, so a pile is a count that can be checked by eye. Major discoveries form the dark base of a pile and minor ones its pale top. A landmark is named directly above its own pile on a short leader, or not at all, and the selected record is always named. Rows can be split by whatever colour means, or combined into one shape.

**Map.** One dot per discovery, at its most precise known place, on an equal-area projection with no borders. Several discoveries at one site bloom into a countable cluster. A place known only as a country or region is one ring that says how many it holds, never a scatter of points; a ring at sea is dashed. The stretch of time in view is drawn in colour, what came before it is small grey dots, and what comes after is absent. Play sweeps time forward. Clicking a crowd zooms into it.

**Trends.** How many discoveries fall in each equal stretch of the axis: as a count, per century, or per billion person-years lived. A bar that holds only one or two discoveries is drawn in outline, because that is too few to give a rate. Coloured by region, each region gets a row of its own, divided by its own population. World population sits underneath on its own axis.

**Index.** Every record as a sortable table, with dates read as single rounded years. A line above it says how much is researched, and opens into a facet-by-facet breakdown. This is the working view.

A sheet at the right shows one record, as described above, and marks each value by where it came from.

## Time scales

| Scale | Equal widths hold | Good for |
| --- | --- | --- |
| Population | Equal person-years lived | Comparing discovery with the number of people who could have made it |
| Calendar | Equal years | Recent centuries, read plainly |
| Logarithmic | Ten times as many years with each step back | The whole 200,000 years on one page |

On the population scale, a pile's height is a rate per person. A period that looks dense produced more discoveries for each human lifetime lived in it.

The strip at the bottom uses the chosen scale, except on a calendar, where nearly all the data would sit in its last sliver. It uses the logarithm there.

## Honesty

- **The charts show research, not history.** The dataset is selective and growing. Each view that counts things says so in its caption.
- **Dates keep their uncertainty.** A discovery is placed at the latest date its earliest record allows. The sheet shows the date as written, such as "by c. 900 BCE".
- **Places keep their precision.** See the map above.
- **Unchecked values are marked.** In the sheet, a filled dot means the value comes from cited evidence, and a hollow one means it was entered from memory and is waiting to be checked. Every coordinate in the first gazetteer is of the second kind.
- **Too few is said, not drawn.** A rate from one or two discoveries is shown in outline.
- **Only established links are drawn.** Candidate links appear in the sheet as open questions.

## Type

Source Serif 4, self-hosted in `app/src/fonts` under the SIL Open Font License. One family is used throughout.

| Use | Size / leading | Weight |
| --- | --- | --- |
| Name of the app | 25 / 32 | 600 |
| Title of a record | 23 / 28 | 600 |
| View names | 17 / 34 | 400, 600 when chosen |
| Summary in the sheet | 16.5 / 24 | 400 |
| Reading text | 15 / 22 | 400 |
| Controls, table cells | 14 / 20 | 400 |
| Notes, captions, axis labels | 12.5 to 13.5 | 400 |
| Section headings | 11.5 / 16, capitals, tracked 0.06em | 600 |

Names are set in one style everywhere. Figures are lining, and tabular in columns. Thousands are set off with a thin space.

## Colour

Paper `#f6f2e9`, sheet `#fcfaf5`, ink `#1f1b16` with two lighter inks for secondary text and notes. Rules are ink at 20% and 9%.

Colour belongs to the data. Six atlas inks are assigned in a fixed order and never recycled: Prussian blue `#2a5ea0`, vermilion `#cf4c2c`, ochre `#dba31e`, teal `#1a9aa6`, plum `#9a4790` and sap green `#4a9440`. A neutral `#a8a091` stands for "not yet assessed" and "no place yet". Each neighbouring pair, in the order the rows and legends use, passes a colour-vision check on the paper. Colour never carries identity alone: rows are headed, the key is present wherever they are not, and every mark answers to the pointer.

Where a value comes from is shown on an ink ramp, never in colour: full ink for reviewed, lighter for sourced, lightest or hollow for recalled.

Text is always ink. It never takes a category's colour.

## Checks

`npm test` in `app/` covers the time scales, the ticks and the data model. The views are checked by eye at 1440 by 900, in each view, on each time scale.
