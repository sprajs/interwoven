# The data model

Interwoven records human discoveries and inventions and how they connect. This page describes what is stored, where, and how to add a new kind of information later. `data/schema.json` is the exact definition, and `python tools/validate.py` enforces it.

## What counts as one discovery

**One record is one community achieving one thing, at a time and in a place.** A record can be a scientific finding, a mathematical method, a device, a material, a process or a practice.

The same thing reached twice is two records. Pottery in East Asia and pottery in the Amazon are separate discoveries with their own dates, places, causes and consequences. They share a `concept`, and each says how its community came to have it through `origin`:

| `origin` | Meaning |
| --- | --- |
| `first_known` | The earliest known achievement of this thing anywhere |
| `independent` | Reached separately, with no evidenced knowledge of an earlier one |
| `derived` | Reached through evidenced transmission, then adopted or adapted |
| `revival` | Deliberately recovered after being lost or abandoned |
| `unknown` | Investigated, and the evidence does not settle it |

This lets every view choose what to count. A map of activity counts every record. A chart of the world's frontier counts only `first_known`. Nothing is double-counted by accident, because the choice is explicit.

A place merely adopting something is an `adoption` or `transmission` event on the existing record. It becomes its own record when the community changed it or built on it in a way worth following.

## Three ways two discoveries connect

| Connection | How it is stored | Examples |
| --- | --- | --- |
| **Stated links** | A `links` entry on the later or receiving discovery, with a type, a statement and evidence | Built on, adapted, required, transmitted from, reached independently of |
| **Shared things** | Both records point at the same entry in a register. Nothing extra is stored | Same place, person, organisation, society, concept or field |
| **Nearness** | Computed from dates and coordinates | Within 50 years and 500 km |

Only the first kind is a historical claim that needs evidence. The other two come free once the facets are filled in, which is why most of the work is on facets. A new kind of connection is usually a new facet, not a new link type.

Link types sit in four layers, so a view can draw one layer, several or none:

| Layer | Types |
| --- | --- |
| Dependence | `builds_on`, `adapts`, `requires`, `uses_instrument`, `uses_process`, `uses_theory`, `supersedes`, `part_of` |
| Transmission | `transmitted_from` |
| Parallel | `independent_of` |
| Affinity | `companion_of`, `same_principle`, `same_family` |

A link also records what passed across (`contribution`), how it travelled (`carrier`), how much the later work relied on it (`influence`) and how well the evidence supports the statement (`confidence`). A link has a `status`: `established`, `candidate` (a question, not a claim) or `insufficient` (researched without finding support). Candidate and insufficient links are never drawn as connections.

## Where things live

```
data/
  schema.json          The definition of every record
  vocab.json           Every controlled list of values, each with its meaning
  taxonomy.json        Domains and fields
  discoveries/<domain>/<id>.json    One file per discovery
  sources/<letter>/<id>.json        One file per source
  places.jsonl  people.jsonl  organizations.jsonl  societies.jsonl  concepts.jsonl
  leads.jsonl          Things worth researching that have no record yet
  reference/           World population and other context series
evidence/<letter>/     Saved copies of sources, named after the source
```

Discoveries and sources are one file each, so that several people and agents can work at once without editing the same file. The registers are one line per entry, sorted by id.

## A discovery record

Only `id`, `name`, `description`, `kind`, `domain`, `events`, `earliest_record` and `research` are required. Everything else is filled in as research reaches it.

| Group | Fields | Question answered |
| --- | --- | --- |
| Identity | `id`, `name`, `aliases`, `summary`, `description` | What is it, exactly? |
| Classification | `kind`, `domain`, `fields`, `advance`, `scale` | What sort of thing is it, where does it belong, and what was new? |
| Significance | `tier`, `tier_reason` | How much later work depended on it? |
| Independence | `origin`, `concept` | How did this community come to have it? |
| Cause | `prompted_by`, `why`, `limit_removed` | What set people working on it, and what bottleneck did it relieve? |
| Circumstances | `setting`, `funding`, `societies` | In what kind of setting, paid for by whom, within which society? |
| Where and who | `places`, `people`, `organizations` | Where did it happen, and who did it? |
| Time | `events`, `earliest_record`, `community_entry`, `witnesses` | What is dated about it? |
| Record | `known_from`, `caveats` | How do we know, and what don't we know? |
| Outcome | `reception`, `fate`, `end_reason`, `market` | How was it received, and where is it now? |
| Measures | `measures` | What performance, costs, access or adoption figures are known? |
| Connections | `links` | What did it build on or come from? |
| Research | `research`, `external` | Where does each value come from, and what is still open? |

### Time

Every dated thing known about a discovery is an **event**: an observation, a publication, a first sale, an adoption somewhere, an end of use. Each event has a type, a date, a statement, evidence and, where known, places.

A date keeps its uncertainty. It has an `earliest` and a `latest` point, a `status` (`known`, `approximate` or `bounded`), a `label` as it should be read, and the `basis` for it. When the evidence gives only an upper limit, `earliest` is `null`. Years before the common era are negative, and there is no year 0. No date is ever invented to fill a gap.

Two events are singled out:

- `earliest_record` is the earliest defensible dated record of this exact thing. Charts place the discovery here.
- `community_entry` is when a community demonstrably used or knew it. It is kept apart because invention and use can be centuries apart.

A surviving copy is a `witness`. It shows the thing existed and never dates its origin by itself.

Events may include `contributions`: each identifies exactly one registered `person`, registered `organization`, or described `group`, a controlled `role`, optional `resource`, and evidence specific to that contribution. An organisation may, for example, have supplied equipment at one event without having funded its development. The discovery-wide people and organisation roles remain independent of these event-specific claims.

### Measures

`measures` preserves reported quantities and units, including prices and adoption as well as performance. An extended measure can point to a local `event` or give its own `date`, and specify a `subject`, a registered `person` or `organization`, `conditions`, `lower` and `upper` bounds, and a `status`. Adoption counts can use `numerator`, `denominator` and `denominator_definition`. Monetary figures can retain the original `currency` and `money_context`. A derived extended measure explains its calculation in `method`. Each extended measure needs a time scope, status and evidence with source, locator and support; legacy measures retain their original requirements. Bounds and denominators are checked, but their interpretation and comparability remain research judgments.

### Places, people, organisations and societies

A discovery points at entries in registers. A place has coordinates, a `kind` that says how precise it is (a site, a settlement, an area, a country, a region or a body of water), the present-day country, one of six world regions that match the population series, and the place that encloses it. A vague location stays vague: "Song China, workshop unknown" points at China, with the doubt in a note. It never becomes a made-up point.

### Where each value comes from

`research.basis` records, for each facet, where its value came from:

| Basis | Meaning |
| --- | --- |
| `sourced` | From evidence cited on the record |
| `recalled` | From general knowledge, entered without checking a source. A lead to verify |
| `reviewed` | Checked against the evidence by a second reader |
| `unknown` | Investigated, and the evidence does not settle it |
| `not_applicable` | The question does not apply |

A facet with no basis has not been researched. The validator rejects a facet that has a value and no basis. This is what makes it possible to research one facet across every discovery: `python tools/coverage.py --missing places` lists the records still to do, and `--basis recalled` lists the ones waiting to be checked.

## Adding a new kind of information

1. Decide whether it is a value from a short list (add the list to `vocab.json`), a thing several discoveries can share (add a register), or free text or a number.
2. Add the field to `discovery` in `schema.json`, and its name to `FACETS` in `tools/dataset.py` so that its basis is tracked.
3. Describe it in the table above.
4. Run `python tools/coverage.py --missing <facet>` and research it record by record.

Existing records stay valid, because a facet that is absent simply has not been researched.

## What is deliberately not stored

Anything that can be computed is left out: how many later discoveries depend on one, the time between linked events, how deep a chain runs, whether a link crosses fields or regions, and how many discoveries a place or a period has.

## Reference adoption pilot

`data/reference/adoption/chat-telephone-pilot.json` is an optional, separately validated set of selected country-year observations. It records the source release and SHA-256, the indicator definition and original attribution, exact country/year/value tokens, 1-based physical CSV line numbers including the header, and explicit missing status. The schema is limited to CHAT `telephone` counts in `lines`. The telephone count has no denominator and no implied link to a discovery. Reference panels are not discovery measures and are not compiled into the app.

The two Eurostat AI pilots in `data/reference/eurostat-ai/` are separate survey extracts, each tied to an unchanged selected JSON-stat response and its source hash. Enterprise observations use `isoc_eb_ai` and retain employment size and activity; individual observations use `isoc_ai_iaiu` and retain individual type. Each cell records its complete dimension codes, percentage or null, missing status, source index and any flag. The survey year is not the interview date, and the two populations and indicator definitions are not interchangeable. The enterprise 2025 indicator includes an expanded set of AI technologies. No graph or app behavior is implied.
