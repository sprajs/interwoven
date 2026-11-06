# Handover: connection and durability gaps

**For:** the research agent working in this folder.
**From:** the agent building the timeline in `web/`, written 6 November 2026.

## Why this exists

Szymon expected this chart to be far more interconnected, and it is not yet. The graph has 143 entries and 103 relationships, split into 47 separate fragments, and 19 entries have no relationship at all. Almost nothing says how long a technology lasted. Run this for current numbers:

```bash
python3 tools/gap_audit.py --write
```

Your job is to investigate these gaps and record what the evidence supports. **The aim is a truer graph, not a denser one.** Every proposed link below is a question and none of them is a claim. A well-supported "no documented link" counts as a result.

All existing rules in `README.md` and `SCHEMA-CONTRACT.md` still apply. In particular, keep failed and disconnected branches, and never add a link only to reduce the fragment count.

## 1. Answer the candidate questions

`handovers/candidate-links.jsonl` holds 36 questions: 31 about possible links and 5 about possible duplicate entries. Work through them in file order, because the bridges between major threads come first.

For each question, update its record in place:

| `status` | Meaning | What else to do |
| --- | --- | --- |
| `open` | Not investigated yet | Nothing |
| `confirmed` | Evidence supports a link | Add it to `data/relationships.jsonl` with evidence, and summarise it in `finding` |
| `rejected` | Evidence shows no such link, or independent development | Say why and cite sources in `finding` |
| `insufficient` | Investigated but unresolved | Say what you checked and what would settle it in `finding` |

The `proposed_relation` is a starting guess. Use whichever relation the evidence supports, and link through intermediate entries rather than one long jump where they exist. For the `identity` questions, decide whether the two records are one configuration or two. Merge or link them accordingly, without losing provenance.

## 2. Fill the holes in the graph

These are missing entries, not missing links. They are listed by how much they would connect, and they are starting points that you should prioritise using evidence.

**Between existing threads**
- Electronics from 1895 to 1946: vacuum tubes, crystal detectors, radio. This is the largest hole in a thread that should be continuous.
- Junction and diffused transistors, between the 1947 amplifier and the planar work.
- Open-hearth steel, between Bessemer and oxygen converters.
- Computing between the 4004 and genome assembly.
- Gutenberg and European movable type. Asian printing entries exist, but this does not.
- Electric telegraph and telephone, between Faraday and Marconi.

**Missing altogether**
- Electric power: generation, transmission, lighting.
- Medicine: germ theory, vaccination, antibiotics.
- Agriculture and fertiliser, including Haber-Bosch.
- Internal combustion, aviation, rocketry and spaceflight.
- Lasers, optical fibre and modern batteries.
- Networks and software: the internet, the web and machine learning.

Keep the wide regional scope already here, including non-Western and non-market traditions.

## 3. Research durability

The chart needs to show how long technologies lasted and how they gave way to each other. Today the evidence is close to empty:

- Documented decline, revival or adoption: 0 entries
- Documented withdrawal: 2 entries
- Documented abandonment: 1 entry
- Supersession, revival or abandonment links: 0

**What to research**, starting with tier 0 and tier 1 technologies:
1. `adoption`, `decline`, `withdrawal`, `end_of_use`, `abandonment` and `revival`, each scoped to a region and configuration as the contract requires.
2. `ongoing` with an `as_of` date where a technology demonstrably continues. Do not infer it from a missing end date.
3. Which technology displaced which, using the `supersedes`, `revival-of` and `abandonment-of` relations. Good places to start:
   - Bessemer to open-hearth to oxygen steel
   - Point-contact to junction to planar transistors
   - Slide rules to electronic calculators
   - Water power to steam
   - Traditional wayfinding, its decline and its revival through Hōkūleʻa

Replacement is rarely total, so record where something survived, and remember that one supplier's withdrawal is not the end of a technology.

## 4. Questions for you to check

- **Withheld relationships.** Earlier `migration/withheld-relationships.json` and `legacy/v1/` existed in this folder and were never committed, and they are no longer here. If you moved or removed them deliberately, say where they are. The withheld links are strong candidates for this work, and if they have been lost, tell Szymon.
- **Dates.** 114 entries have no selected anchor. Selecting anchors matters to the chart as well as the record, so prioritise tier 0 and tier 1.

## 5. Finishing

1. Run `python3 tools/validate.py --json` and `python3 -m unittest discover -s tests`.
2. Run `python3 tools/gap_audit.py --write`. It flags open questions that are already linked, and questions pointing at entries that no longer exist.
3. Commit explicit paths only. Other agents share this checkout, so check `git status` first and leave `web/` alone.
4. Report the before and after numbers from the audit, and which questions remain open.

The chart picks up your changes to `data/*.jsonl` automatically, so you do not need to touch `web/`.
