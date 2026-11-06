# Handover: connection and durability gaps

**For:** the research agent working in this folder.
**From:** the agent building the timeline in `web/`, written 6 November 2026.

## Why this exists

Szymon expected this chart to be more interconnected and to show how long technologies lasted. The initial audit found 143 entries, 103 relationships, 47 fragments and 19 isolated entries. Those are the original audit figures, not a live count. Run this for current numbers:

```bash
python3 tools/gap_audit.py --write
```

Only entries with a selected, usable community-entry anchor appear on the chart; a drawn link needs both ends placed. Selecting defensible anchors makes existing research visible. One-sided dates are supported.

The current checkpoint has 221 entries, 131 relationships, 98 fragments and 59 isolated entries. All entries are placed and all relationships have placed endpoints. The larger number of fragments reflects expanded coverage, including traditions for which a specific transmission has not been established. **The aim is a truer graph, not a denser one.** An insufficient-evidence finding is useful, but does not establish historical absence or independent invention.

The current rules are in `README.md` and the single version-1 `schema.json`. Keep failed and disconnected branches, and never add a link only to reduce the fragment count.

## 1. Select anchors

All 221 current entries have selected anchors. When reviewing these or adding future entries, use the best supported availability, actual use, adoption, recognition or explicitly qualified awareness in a named community. Do not select an invention, private demonstration or modern catalogue access date merely because it is available. First commercial availability remains separate. Retain approximate and open bounds; do not invent a second limit.

## 2. Answer the candidate questions

`handovers/candidate-links.jsonl` holds 36 assessed questions: 31 about possible links and 5 about possible duplicate entries. Four link questions are confirmed: magneto-optics to Maxwell, Bessemer to Gerlafingen, MOS devices to silicon-gate circuitry, and chain termination to fluorescent-primer sequencing. Three duplicate pairs have been merged, and the separate 2N1613 product/class question is resolved. The remaining 27 link questions and one identity question have insufficient evidence. Full findings and inspected sources are retained in `reviews/connection-questions.json` and `reviews/identity.json`.

For each question, update its record in place:

| `status` | Meaning | What else to do |
| --- | --- | --- |
| `open` | Not investigated yet | Nothing |
| `confirmed` | Evidence supports a link | Add it to `data/relationships.jsonl` with evidence, and summarise it in `finding` |
| `rejected` | Evidence shows no such link, or independent development | Say why and cite sources in `finding` |
| `insufficient` | Investigated but unresolved | Say what you checked and what would settle it in `finding` |

The `proposed_relation` is a starting guess. Use whichever relation the evidence supports, and link through intermediate entries rather than one long jump where they exist. For the `identity` questions, decide whether the two records are one configuration or two. Merge or link them accordingly, without losing provenance.

## 3. Fill the holes in the graph

The 81-entry expansion added power, telegraph, telephone, antibiotics, software, web, earlier mathematics, manufacturing, regional infrastructure and other specific configurations. Remaining gaps include both new subjects and deeper coverage of subjects already present. Future priorities must follow evidence; these are not required bridges or an assertion of a continuous lineage.

**Between existing threads**
- Electronics from 1895 to 1946: vacuum tubes, crystal detectors and radio configurations, with specifically documented contributions.
- Junction and diffused transistors, between the 1947 amplifier and the planar work.
- Open-hearth steel, between Bessemer and oxygen converters.
- Computing between the 4004 and genome assembly.
- Gutenberg and European movable type. Asian printing entries exist, but this does not.
- Telegraph and telephone design transmission and regional adoption; services in Britain, the United States, India and Japan now have entries.

**Additional subjects and depth**
- Electric power: expand the existing Pearl Street, Niagara and Lauffen–Frankfurt cases into regional generation, transmission and lighting adoption.
- Medicine: germ theory and vaccination; extend the existing penicillin, insulin, antisepsis and diagnostic-instrument cases through regional use and access.
- Agriculture and fertiliser, including Haber-Bosch.
- Internal combustion, aviation, rocketry and spaceflight.
- Lasers, optical fibre and modern batteries.
- Networks and software: internet infrastructure, machine learning, and adoption beyond the existing FORTRAN, business computing and public web-release entries.

Keep the wide regional scope already here, including non-Western and non-market traditions.

## 4. Research durability

The chart still has sparse evidence about duration and replacement. At this checkpoint:

- Documented adoption: 2 entries
- Documented decline, revival or end of use: 0 entries
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

## 5. Rejected and unresolved links

The current `BACKLOG.md` preserves the substantive unanswered transfer questions. Unsupported Hertz-result-to-Marconi, exact Andrus–Bond-to-Fairchild, Jena-to-Powell-and-Lealand and Joule-1843-to-Thomson-1848 links must not be restored from chronology or shared terminology. Research new evidence for each specific contribution. Superseded authoring and migration products are not part of the current contract.

## 6. Finishing

1. Run `python3 tools/validate.py --json` and `python3 -m unittest discover -s tests`.
2. Run `python3 tools/gap_audit.py --write`. It flags open questions that are already linked, and questions pointing at entries that no longer exist.
3. Commit explicit paths only. Other agents share this checkout, so check `git status` first. The designated integrator owns canonical files and Git; web changes are coordinated separately. Do not push or publish during this session.
4. Report the before and after numbers from the audit, and which questions remain open.

The chart picks up your changes to `data/*.jsonl` automatically, so you do not need to touch `web/`.
