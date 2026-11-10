# Research guide

How to add to the dataset and how to check it. `docs/data-model.md` describes the records themselves.

## What belongs

**Everything people have discovered or invented, anywhere, at any time.** The aim is a tech tree of human civilisation, so the dataset covers farming, food, health, building, materials, tools, energy, transport, warfare, communication, computing, mathematics, the sciences, institutions, and arts and entertainment. `data/taxonomy.json` lists the domains and their fields.

**An achievement does not have to be a world first.** A community that reached something separately, or took it up and changed it, gets its own record. Polynesian voyaging, farming in New Guinea and printing in Korea all belong, whatever was known elsewhere at the time. Each record says how its community came to have the thing (`origin`) and which general capability it is an instance of (`concept`). Views that need the world's frontier filter on `origin`; views that count human activity count everything.

Failed, abandoned and short-lived things belong too. So do things with no known descendants.

A place that only adopted something is an `adoption` or `transmission` event on the existing record. Make a new record when the community changed the thing or built on it.

The dataset is a selective, growing record. A missing ancestor means nobody has researched it yet, and never that something arose from nothing. Charts say so.

## Rules that never bend

1. **Never invent a date, a place, a person or a link.** Leave the facet out. An empty facet is a correct answer.
2. **Say where every value comes from.** Each filled facet has a basis in `research.basis`: `sourced` (the record cites evidence for it), `recalled` (entered from general knowledge and not yet checked), `reviewed` (checked by a second reader), `unknown` (investigated and unsettled) or `not_applicable`.
3. **Recalled values are leads.** They are useful, they are shown as unverified, and each one is waiting to be replaced by a sourced value.
4. **A date keeps its uncertainty.** "By 1200" stays an upper limit with `earliest: null`. A source's publication date does not date the work it describes. A surviving copy is a witness and does not date the origin.
5. **A link needs its own evidence.** Being earlier, being similar and sharing a subject are not evidence of influence. A question worth asking is a link with `status: "candidate"`.
6. **A vague place stays vague.** Point at the country or region and put the doubt in a note. Never use a precise point that the evidence does not give.

## Adding a discovery

1. Check `data/discoveries/` and `data/leads.jsonl` for the same thing under another name.
2. Create `data/discoveries/<domain>/<id>.json`. The id is a short lowercase name with hyphens. The folder is the domain of the record's primary field.
3. Fill in `name`, `description` (exactly what was achieved), `kind`, `domain`, and at least one dated `event` with evidence. Point `earliest_record` at the event that gives the earliest defensible date, or at `null` when there is none.
4. Add each source as `data/sources/<first letter>/<id>.json`. Record the passages actually read. Save a copy under `evidence/` when the licence and size allow, with its SHA-256.
5. Fill in whatever facets the evidence supports, each with its basis.
6. Add people, places, organisations and societies to their registers if they are new. Use the usual English name as the id so that others pick the same one. Search the register first.
7. Run `python3 tools/validate.py`. It must report no problems before a commit.

A lead that becomes a record is removed from `leads.jsonl`.

When a research lead's field is known, set its optional `field` to an existing taxonomy field ID, such as `energy.steam`. Leave it absent when unclassified; do not infer a field merely to fill the slot. `python3 tools/coverage.py --json` reports lead statuses by explicit field and separately counts unclassified leads.

## Researching one facet across the dataset

This is how a new kind of information is filled in, for example funding, or performance figures.

```sh
python3 tools/coverage.py                       # how complete each facet is
python3 tools/coverage.py --missing funding     # the records still to do
python3 tools/coverage.py --basis recalled --facet people   # values waiting to be checked
python3 tools/coverage.py --by domain           # coverage split by domain
```

Work through the list, cite a source for each value, set the basis to `sourced`, and validate. Where the evidence does not settle the matter, set the basis to `unknown` and add an entry to `research.unresolved` saying what was looked at.

`docs/data-model.md` explains how to add a facet that does not exist yet.

## Measures and event contributions

Record the figure as stated, with its unit, time, subject and conditions. Preserve nominal currency and its context rather than silently converting prices. For adoption, define the population counted by the denominator; missing evidence is not zero adoption. For a derived figure give the method and assumptions. An event reference points to an event on the same discovery; a separate date uses the normal date object. Each extended measure needs `status` and evidence with a locator and what it supports. For example:

```json
{"quantity":"adoption", "value":40, "unit":"percent", "event":"survey",
 "subject":"eligible households in the district", "numerator":40, "denominator":100,
 "denominator_definition":"eligible households surveyed", "status":"derived",
 "method":"40 divided by 100, multiplied by 100",
 "evidence":[{"source":"example-source", "locator":"p. 4", "supports":"Survey counts."}]}
```

Use event `contributions` when an actor's role is supported for a particular stage. For example, `{"organization":"example-company", "role":"supplier", "resource":"equipment", "evidence":[{"source":"example-source", "locator":"p. 5", "supports":"The company supplied equipment for this event."}]}`. Each contribution identifies exactly one person, organisation or described group. Do not infer a funder from an affiliation or treat a supplier as the developer without evidence. The example identifiers must be replaced with real registered entities and sources.

## Places

`data/places.jsonl` is the gazetteer. Each place has coordinates, a `kind` that says how precise it is, the present-day `country`, one of six world regions, and the place that encloses it (`within`). Coordinates were entered from memory and are marked `recalled`. Check them against a gazetteer and change the basis to `sourced` as you go.

## Links

A link is stored on the later or receiving discovery and points at the other one with `from`. Give it a `type`, a one- or two-sentence `statement`, and evidence. Where it can be established, add what passed across (`contribution`), how it travelled (`carrier`) and how much the later work relied on it (`influence`).

Do not store what can be computed. Two discoveries made in the same town, by the same person or within the same society are already connected through the registers, and the app shows that without any link.

## Checks

```sh
python3 tools/validate.py                               # schema, references, dates, saved evidence
python3 -m unittest discover -s tools/tests -t tools    # the tools themselves
cd app && npm test                                      # the app's logic
```

## Checking the reference adoption pilot

The CHAT pilot is a tiny selected factual extract; no redistribution licence for the full release has been identified. Retain full upstream files outside the repository. To reproduce selected rows, obtain the release separately and run, for example:

```sh
python3 tools/import_chat_telephone.py --input /path/to/FinalCHAT_72909.csv --select 'Japan:1950' --select 'Kenya:2000'
```

The importer checks the release hash, never fetches data, and emits a JSON array. A blank is missing, not zero. The count is lines, not users or adoption percentage; a ratio would require a separately researched, scoped denominator and is not part of this pilot.

## Eurostat AI survey extracts

The Eurostat AI pilots preserve selected raw responses in `evidence/e/` with source attribution and SHA-256. Eurostat permits reuse of statistical data with acknowledgement, subject to any source-specific conditions. To reproduce the enterprise observations offline, use the release hash recorded in its panel:

```sh
python3 tools/import_eurostat_ai.py --input evidence/e/eurostat-isoc-eb-ai-selected-20261109.json --dataset isoc_eb_ai --sha256 <release-sha256>
```

Use dataset `isoc_ai_iaiu` and its separate raw file and hash for individuals. The importer accepts the two documented dimension orders for these saved responses and rejects a different order rather than assuming a mapping. Selection, units, survey windows, source flags and missingness must remain attached; a blank cell is not zero. Do not equate enterprise AI use with individual generative-AI use or infer invention from use.
