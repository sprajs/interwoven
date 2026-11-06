# What the graph should record so it can be analysed

This proposes the labels and new data that would let us ask how breakthroughs happen. It is a proposal: nothing here has changed the graph. The vocabulary is in `vocabulary.json`, and `check_pilot.py` validates the pilot and reproduces the graph figures below.

## The main point

**One "category of breakthrough" label would not be enough.** The graph needs to answer several separate questions, and they belong on different records:

| Question | Where it belongs | Field |
|---|---|---|
| What was new? | Entry | `advance_type` |
| What set people working on it? | Entry | `prompted_by` |
| What passed from A to B? | Link | `contribution` |
| How much did B rely on A? | Link | `dependence` |
| How did it get across? | Link | `carrier` |
| Was the later version better, and by how much? | New records | `lineage`, `capability` |
| Why is this entry in the graph at all? | Entry | `inclusion_reason` |

The planets show why. These dates and details are from memory and need sourcing before use:

| Discovery | Prompted by | Enabled by |
|---|---|---|
| Jupiter's moons, 1610 | Not recorded in the graph | A new, improved telescope |
| Uranus, 1781 | A systematic sky survey | Herschel's own large reflector |
| Neptune, 1846 | An anomaly in the orbit of Uranus, then a calculated prediction | Mathematics, then an existing refractor |
| Pluto, 1930 | A deliberate search | Photographic plates and a blink comparator |
| 51 Pegasi b, 1995 | A planned radial-velocity programme | A high-precision spectrograph |

All five are "discovered a planet or moon". A single category would make them look alike, when Neptune is nearly the opposite of Jupiter's moons.

## What the graph can and cannot answer today

- **Your telescope question stops after one step.** The graph has Dutch spyglass → Galileo's telescopes → Jupiter's moons and lunar relief, and separately Newton's refraction work → his reflector. Nothing feeds the spyglass from lens-making, nothing follows Newton's reflector, and Uranus, Neptune, Pluto, exoplanets and achromatic lenses have no entries. No record says a later telescope was better than an earlier one.
- **A better example already exists in microscopes.** Royal Institution furnace → Faraday's glass → magnetic rotation, and Jena glass research → Jena glass → Zeiss objectives → Dallinger's comparisons, are exactly the kind of chain you describe.
- **Most recorded ancestry is missing.** 94 of 171 technologies and 20 of 50 science results have no recorded parent. Only 15 of 50 science results have a technology behind them. 17 of the 35 tier 0 entries have no parent, and 59 entries have no link at all. Disconnected entries are valid, but these gaps mean any count of "what led to what" reflects research coverage so far.
- **Relation types mix two things.** Names like `documented-development` (51 of 131 links) say how we know about a link more than what it contributed. In the pilot, that one type covered eight different contributions, from supplying a method to refuting an earlier claim. `documented-transmission` covered both "passed on an idea" and "supplied the numbers".
- **Almost nothing is measured.** Only about 3 descriptions contain a number with a unit (a rough text match), so step changes cannot be told from gradual improvement.
- **People and institutions exist only in prose,** and the 221 entries use 171 different free-text regions. Neither can be counted reliably.
- **Most dates are one-sided.** 154 of 221 chart placements are "known by" limits, so a measured lag between two entries is usually a limit, not a duration.

## Questions this would let us ask

"Wave" is the earliest stage at which the question becomes answerable, as set out under Order of work.

| # | Question | Needs | Wave |
|---|---|---|---|
| 1 | Are discoveries led by tools or by ideas, and does that vary by field and era? | `advance_type`, `prompted_by`, `contribution`, a defined sample | 1, 2 |
| 2 | How deep is the stack beneath a discovery: discovery ← instrument ← optics ← glass ← furnace? | `contribution`, `open_dependencies` | 1 |
| 3 | Did capability rise smoothly or in jumps? | `lineage`, `capability` | 2 |
| 4 | How long from new capability to discovery, and from discovery to use? Is this shrinking? | Linked events with usable dates | 2 |
| 5 | Does science lead technology, or the reverse? | `contribution`, a sound `kind` split | 1 |
| 6 | Do breakthroughs come from combining fields? | Reviewed field labels | 1 |
| 7 | What was the bottleneck, and what happened when it was removed? | `limit_removed`, `capability` | 2 |
| 8 | Which feedback loops exist: instrument → science → better instrument? | `contribution`, event-level links | 1 |
| 9 | Which technologies are keystones that many later things depend on? | Much fuller links | 2 |
| 10 | Are breakthroughs prompted by need, curiosity, accident, the state or the market? | `prompted_by`, `funder` | 3 |
| 11 | How does knowledge travel: papers, people, artefacts, trade, translation? | `carrier`, `place` | 3 |
| 12 | Who does this work and where: workshops, courts, universities, firms, the state? | `actor`, `funder`, `place` | 3 |
| 13 | Are discoveries inevitable? How often do people get there independently? | `parallel_group` | 3 |
| 14 | Which results were ahead of their time, and what was the world waiting for? | `reception`, linked events | 3 |
| 15 | What kills a technology, and what makes one last? | Lifecycle events, `replaced`, `end_reason` | 3 |
| 16 | What knowledge gets lost, and how is it recovered? | `reception`, `craft_practice`, `reconstruction` | 3 |
| 17 | What do we see only because of survivorship? | `inclusion_reason`, dead ends deliberately included | 1, 2 |

## Rules for the labels

1. **Keep labels out of `nodes.jsonl` and `relationships.jsonl`.** Review decisions are bound to a SHA-256 of each record, so adding fields there would invalidate them. Use separate files such as `data/analysis/entry-labels.jsonl` and `data/analysis/link-labels.jsonl`. This also keeps interpretation apart from historical claims.
2. **Never guess.** Use `not_yet_researched`, `unknown` and `not_applicable` as the lifecycle fields already do.
3. **Say whose judgement it is.** Every label records its basis (`actor_statement`, `historian_judgement` or `reviewer_inference`) and its evidence. "Galileo's telescope enabled this" and "this was instrument-led" are claims of different strength.
4. **Allow several values** wherever the world really has several.
5. **Separate the prompt from the enabler.** Enablers come from link contributions, so they are not entered twice.
6. **Do not hand-label what can be computed.** Reach, lag, centrality, chain depth, direction of flow and field crossing all come from the graph.
7. **Test before scaling.** Two coders label the same sample independently. Merge or drop any facet they cannot agree on (Cohen's kappa below about 0.6 is a warning sign).
8. **Name the sample.** The graph is a curated set, not a random one, so "40% of breakthroughs were instrument-led" would be a statement about the curation. Percentages need a defined list, recorded through `inclusion_reason`, that was drawn up without regard to the expected answer.

## Order of work

1. **Finish the science review first.** It may change relation types, entry kinds and tiers, and labels should sit on corrected records.
2. **Wave 1: label what exists.** `inclusion_reason`, `advance_type`, `change_scale`, `contribution`, `dependence`, `lineage` and `open_dependencies` on the existing records. `open_dependencies` also gives a sourced list of what to research next, in place of guessing at gaps.
3. **Wave 2: one complete case.** Build telescopes and planetary discovery in full, starting with lens-making and ending with exoplanets, including failures and instruments that went nowhere. Define the list of discoveries up front so it is a real sample. Add `capability` records (aperture, resolving power, wavelength range, cost if available), `prompted_by` and `limit_removed`. Check whether the labels answer your questions here before repeating this anywhere else. A second complete case, such as microscopy or steel, would then show whether a pattern is general.
4. **Wave 3: context.** `carrier`, `place`, `actor`, `funder`, `parallel_group`, `reception` and `end_reason`.

## What the pilot showed

I coded 36 entries and 35 links across optics, heat, steel, semiconductors, sequencing, mathematics and regional work (`pilot-entries.jsonl`, `pilot-links.jsonl`).

- **The record text is enough for some labels.** `advance_type`, `contribution` and `dependence` could be assigned for every record sampled.
- **`prompted_by` needs real research.** It could not be determined from the text for 24 of 36 entries, and `change_scale` for 10.
- **The pilot changed the vocabulary.** A clinical or field trial needed its own `advance_type` value, and the Hōkūleʻa voyages needed `supplied_platform`, because neither fitted what I had drafted.
- **Labels expose other questions.** A laboratory furnace fits poorly as a breakthrough, a surviving book is a witness to a technique and not its start, and laboratory methods are coded as technology. These feed the entry-identity part of the science review.
- **8 of 36 entries have a prerequisite with no entry yet,** such as Newcomen's engine and Taq polymerase's source.

**Limits:** this was one coder, with no sources reopened and no second coder, so it shows only that the scheme can be applied. It says nothing about reliability, and these labels are not findings. `open_dependencies` are from memory and need sourcing.

## Where the ideas come from

These frameworks informed the facets. I cite them from memory and have not rechecked them, so treat them as reading leads.

| Facet | Sources |
|---|---|
| Tool-led and idea-led science | Price on instrumentalities; Dyson, *Imagined Worlds*; Galison, *Image and Logic* |
| What flows between science and engineering | Rosenberg; Mokyr, *The Gifts of Athena*; Vincenti, *What Engineers Know* |
| `change_scale` | Henderson and Clark (1990); Kuhn; Anderson and Tushman (1986) |
| Recombination | Arthur, *The Nature of Technology*; Fleming (2001) |
| `limit_removed` | Hughes on reverse salients |
| `prompted_by` | Stokes, *Pasteur's Quadrant* |
| `parallel_group`, `reception` | Merton on multiples; van Raan on sleeping beauties |
| Keystones | Bresnahan and Trajtenberg on general-purpose technologies |
| Use, durability and survival | Edgerton, *The Shock of the Old* |
