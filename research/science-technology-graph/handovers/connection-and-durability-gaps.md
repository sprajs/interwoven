# Handover: connection and durability gaps

**For:** the research agent working in this folder.
**From:** the agent building the timeline in `web/`, written 6 November 2026.

## Why this exists

Szymon expected this chart to be more interconnected and to show what is known about technologies' later use. The [current checkpoint](../CHECKPOINT.md) records the verified integration state; the [live gap audit](gap-audit.md) reports connectivity, placement and lifecycle evidence. Use those reports for current totals rather than a fixed count in this handover. To inspect the audit without changing files:

```bash
python3 tools/gap_audit.py
```

Only entries with a selected, usable community-entry anchor appear on the chart; a drawn link needs both ends placed. Selecting defensible anchors makes existing research visible. One-sided dates are supported.

Disconnected entries can represent traditions for which a specific transmission has not been established. **The aim is a truer graph, not a denser one.** An insufficient-evidence finding is useful, but does not establish historical absence or independent invention.

The current rules are in [README.md](../README.md) and the single version-1 [schema.json](../schema.json). Keep failed and disconnected branches, and never add a link only to reduce the fragment count.

New identities require a supported global capability, scientific result, architecture or process contribution. Compare earlier and contemporary configurations anywhere, including distinct tradeoffs, precision, reliability, cost/access and enabling applications. A regional first, rediscovery, revival, reconstruction or additional artifact witness does not qualify by itself. Preserve such evidence as scoped events or supporting context on the appropriate identity; retain a causal intermediate when its contribution to a later frontier advance is specifically evidenced.

Similar function or a shared historical account does not establish identical technology. Different enabling components and workflows can remain distinct. Hold uncertain comparisons for review before merging or excluding anything, and retain the original assertions, evidence and dissent. The [frontier-audit report](frontier-audit.md) and [exact applied decisions](../reviews/frontier-audit.json) document eleven independently reviewed units. They do not certify a complete worldwide comparison of every retained entry. Historical-assertion acceptance and frontier eligibility are separate judgments.

## 1. Select anchors

Check current anchor coverage in the [gap audit](gap-audit.md). When reviewing entries or adding frontier-eligible identities, use the best supported availability, actual use, adoption, recognition or explicitly qualified awareness in a named community. Do not select an invention, private demonstration or modern catalogue access date merely because it is available. First commercial availability remains separate. Retain approximate and open bounds; do not invent a second limit.

## 2. Answer the candidate questions

The original register contained 36 assessed questions: 31 about possible links and 5 about possible duplicate entries. The [active register](candidate-links.jsonl) now contains 35 after `gap-25` was retired because its Ra I vessel endpoint was excluded from the innovation graph. Its exact question, insufficient-evidence finding and disposition remain in [frontier-audit.json](../reviews/frontier-audit.json); retirement does not mean the proposed influence was proved false.

Read current statuses and endpoint checks from the active register and [gap audit](gap-audit.md). Findings and inspected sources remain in [connection-questions.json](../reviews/connection-questions.json), [identity.json](../reviews/identity.json) and the later frontier-audit decisions.

For each question, update its record in place:

| `status` | Meaning | What else to do |
| --- | --- | --- |
| `open` | Not investigated yet | Nothing |
| `confirmed` | Evidence supports the stated relationship or identity resolution | Apply the reviewed decision, preserve evidence, and summarise it in `finding` |
| `rejected` | Positive evidence refutes the proposed relationship or supports independent development | Say why and cite sources in `finding` |
| `insufficient` | Investigated but unresolved | Say what you checked and what would settle it in `finding` |

The `proposed_relation` is a starting guess. Use whichever relation the evidence supports, and link through intermediate entries rather than one long jump where they exist. For `identity` questions, compare functional configurations and historical scope. Apply a reviewed merge only when identity is established; distinct records need not be linked. Hold unresolved comparisons and preserve provenance.

## 3. Fill the holes in the graph

Earlier research added power, telegraph, telephone, antibiotics, software, web, mathematics, manufacturing and infrastructure coverage. The [current research register](research-register.json) tracks ownership, comparisons and dispositions during the active continuation. Inspect existing identities and reviewed frontier decisions before proposing additions. Future priorities must follow evidence; these are not required bridges or an assertion of a continuous lineage.

**Between existing threads**

- Electronics from 1895 to 1946: vacuum tubes, crystal detectors and radio configurations, with specifically documented contributions.
- Junction and diffused transistors, between the 1947 amplifier and the planar work.
- Open-hearth steel, between Bessemer and oxygen converters.
- Actual computing systems, software and instrument interfaces used in genome assembly; an early CPU is not a direct prerequisite without documented dependency.
- Printing: compare type manufacture, tooling, inking and press/workflow contributions against earlier systems worldwide; do not create one technology identity per surviving edition.
- Telegraph and telephone design transmission and system capability; keep local service openings as scoped events unless a distinct contribution is established.

**Additional subjects and depth**

- Electric power: compare generation, transmission and lighting configurations for distinct capabilities or meaningful tradeoffs; record regional adoption separately.
- Medicine: germ theory, vaccination and distinct treatment or diagnostic methods; retain regional use and access as scoped episodes rather than automatically adding identities.
- Agriculture and fertiliser, including Haber-Bosch.
- Internal combustion, aviation, rocketry and spaceflight.
- Lasers, optical fibre and modern batteries.
- Networks and software: specific infrastructure, algorithms and implemented systems beyond the existing computing coverage; distinguish a new capability from another deployment.

Compare traditions worldwide, including non-Western and non-market work. Narrow, failed or extinct developments remain eligible when a distinct contribution is supported; report actual performance and failure rather than assuming a design worked or requiring modern survival.

## 4. Research durability

Use the [live gap audit](gap-audit.md) for lifecycle totals. It reports node-stage assessments separately from scoped event episodes. A reviewed episode has accepted historical and lifecycle-classification review axes, and applies only to its stated configuration, community, application and geographical scope. Multiple episodes can belong to one technology identity.

Overall last use can remain unknown while reviewed local cessation events exist. For example, retirement of Frogmore's No. 2 machine does not establish the end of continuous-wire papermaking. Supplier withdrawal, support cutoff, local abandonment, later niche use and revival are separate questions. Neither two dated episodes nor an uncertain event-date range establishes continuous operation between its bounds. Event counts are not counts of distinct innovations or global endings.

**What to research**, starting with tier 0 and tier 1 technologies:

1. `adoption`, `decline`, `withdrawal`, `end_of_use`, `abandonment` and `revival`, each scoped to a region and configuration as the contract requires.
2. `ongoing` with an `as_of` date where a technology demonstrably continues. Do not infer it from a missing end date.
3. Which technology displaced which, using the `supersedes`, `revival-of` and `abandonment-of` relations. Good places to start:
   - Bessemer to open-hearth to oxygen steel
   - Point-contact to junction to planar transistors
   - Slide rules to electronic calculators
   - Water power to steam
   - Traditional wayfinding's scoped continuity, teaching and revival, interpreting Hōkūleʻa witnesses within the frontier-audit limits

Replacement is rarely total, so record where something survived, and remember that one supplier's withdrawal is not the end of a technology.

## 5. Rejected and unresolved links

The current `BACKLOG.md` preserves the substantive unanswered transfer questions. Unsupported Hertz-result-to-Marconi, exact Andrus–Bond-to-Fairchild, Jena-to-Powell-and-Lealand and Joule-1843-to-Thomson-1848 links must not be restored from chronology or shared terminology. Research new evidence for each specific contribution. Superseded authoring and migration products are not part of the current contract.

## 6. Finishing

1. Run `python3 tools/validate.py --json` and `python3 -m unittest discover -s tests`.
2. Run `python3 tools/gap_audit.py --write`. It flags open questions that are already linked, and questions pointing at entries that no longer exist.
3. Commit explicit paths only. Other agents share this checkout, so check `git status` first. The designated integrator owns canonical files and Git; web changes are coordinated separately. Do not push or publish during this session.
4. Report the before and after numbers from the audit, and which questions remain open.

While the local dev server runs, it imports changes to `data/*.jsonl` automatically. Coordinate generated-data refresh and browser verification with the integrator; research contributors do not need to edit `web/`.
