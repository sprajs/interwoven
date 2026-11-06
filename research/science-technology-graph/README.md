# Science and technology graph

A local, evidence-backed graph of advances in global scientific knowledge and technological capability, including short-lived experiments, abandoned branches and configurations with no known descendants.

`schema.json` defines **version 1**. Four JSONL files share this single contract:

| File | Contents |
|---|---|
| `data/nodes.jsonl` | Stable identities, configurations, lifecycle assessments and graph-anchor choices. |
| `data/events.jsonl` | Sourced milestones with date bounds, precision, place/application scope and uncertainty. |
| `data/relationships.jsonl` | Typed historical connections, optionally tied to specific events. |
| `data/sources.jsonl` | Source identity, URLs, inspected passages, access limits and local evidence references. |

`evidence/` contains supporting documents and excerpts. `reviews/` records current decisions. `BACKLOG.md` identifies open questions.

## Use

Run from this directory:

```sh
python3 tools/validate.py --json
python3 -m unittest discover -s tests
python3 tools/query.py stats
python3 tools/query.py node google-glass-enterprise-2
python3 tools/query.py traverse elec-oersted-current-magnetism-1820 --depth 2 --direction outgoing
python3 tools/query.py unresolved-commercial
python3 tools/query.py community-entries
python3 tools/coverage.py --baseline 96b3199
```

Traversal follows historical relationships. Candidate links are excluded unless `--include-candidates` is specified. Disconnected records are valid.

## Global-frontier eligibility

The graph follows advances in humanity’s scientific knowledge and technological capability, assessed against relevant documented prior developments wherever evidence is available. Geography, cultural affiliation, regional first use, independent rediscovery and revival do not by themselves establish a new frontier contribution. Comparison concerns the evidenced configuration or proposition, not cultural rankings or a universally ordered league table of progress.

Retain distinct results and configurations when evidence supports a meaningful contribution: for example a new mechanism, architecture, precision, efficiency, material, production method, reduced cost, improved access, or application. Failed, short-lived, abandoned and extinct advances qualify even without modern descendants. A similar purpose does not establish an equivalent capability; document the actual comparison and its uncertainty.

Merge only the same thing recorded twice from one source, with no independent date or role in a chain. Keep deliberate splits where relationships depend on the separate parts. Record every merge and its reason. A missing novelty investigation is an unresolved question, not a deletion criterion. The documented equivalent prior capability need not already have a node in this dataset. When a confirmed reconstruction, repetition or regional adoption has no appropriate canonical target, exclude its standalone innovation identity while preserving its valid historical assertions and sources in a current exclusion decision or appropriate scoped events; do not force an inaccurate merger. Consolidate equivalent configurations under a researched identity; preserve their scoped invention, availability, use, adoption, decline and revival events, source evidence and supported causal history. A specimen, manuscript, patent or local deployment can witness a technology without becoming a separate innovation identity. Distinguish a new scientific result from a repetition of an earlier observation.

Retain a rediscovery or transmission as a distinct explanatory step when sources establish that the particular event, together with other developments, enabled a later global frontier advance. Do not infer influence or necessity from chronology, resemblance or shared subject matter. If the later contribution or its transmission is unresolved, retain the candidate pending research rather than claiming this exception is proven.

Eligibility and timeline placement are separate. This is a **selective, growing record**, not a complete history or a random sample. Missing ancestry means research coverage is incomplete, not that an entry arose independently.

## Lifecycle and dates

Each entry records two separate questions. `graph_anchor` uses policy `earliest_record`: the earliest defensible dated record of the SAME scoped thing currently established by the sources. `community_entry` preserves its separately sourced availability, use, adoption, recognition or awareness event. Invention, prototype, dated description, publication, deployment and surviving copies remain distinct events.

A dated publication precedes a later citation as an earliest record. An anchor cannot follow an event already establishing the same community's use or knowledge. A surviving copy is evidence about transmission and is never automatically an anchor for the underlying work. Retrospective attestations retain their explicit uncertainty; an interval is not an invented exact onset. Witnesses, components and separately dated experimental configurations retain their distinct identities when the chain depends on them. Historian-held earliest dates remain unplaced while their community events and sources remain accessible.

Events carry their own geographical, market, population and application scope. Approximate dates remain approximate. A source's publication date does not automatically date the work it reports. One-sided bounds retain an explicit status for the unknown limit instead of inventing it. “By” means an upper bound; “Not before” means a lower bound, not ongoing use. Both forms can be placed without manufacturing the missing limit.

| Lifecycle status | Meaning |
|---|---|
| `documented` | Identified event records support the claim. |
| `unknown` | Investigated but unresolved; evidence and reason remain explicit. |
| `not_yet_researched` | This distinct question has not been established. |
| `not_applicable` | The question does not apply for a stated reason. |
| `ongoing` | Evidence supports continuation as of a stated date. |

Withdrawal from sale, production cessation, support cutoff, local abandonment and last use are different. One manufacturer's withdrawal is not a universal death date. Continued niche use and revival can coexist with decline elsewhere.

## Relationships and review

A relationship states an evidenced contribution, adaptation, transmission or bounded requirement. Chronology, analogy and shared vocabulary are insufficient. An enabling invention can precede a successor even when their commercial display dates run in the opposite order; relationship event references retain the actual historical timing.

Historical-claim review and lifecycle-classification review are separate. A sound historical date does not automatically establish commercial availability. `dated_assertion` identifies an evidenced episode whose lifecycle stage still needs classification; it cannot supply a graph anchor.

The validator checks schema, IDs, event ownership, source references, date bounds, anchor eligibility, current review decisions and local evidence hashes. It reports review concerns separately from structural errors. These checks support research; they do not independently prove a historical claim.

Each current review decision binds to a SHA-256 of the complete record, excluding only its top-level review metadata. The accompanying reviews expose the exact historical projections, inspected passages and limits. A changed assertion cannot silently retain a matching review hash.

`reviews/community-entry.json` and `reviews/expansion.json` embed the exact accepted inputs and independent assessments used to compose the records. `reviews/identity.json` preserves duplicate resolutions and original witnesses; `reviews/final-refinements.json` records the later date and tier corrections. `reviews/approximate-dates.json` reconciles the structured status with already qualified approximate bounds. `reviews/connection-questions.json` preserves the assessed candidate links, including insufficient-evidence findings. Source-storage and source-metadata reviews explain byte-preserving changes. Temporary paths in these ledgers are provenance, not dependencies needed to inspect the accepted assertions.

## Current coverage

Run `python3 tools/query.py stats` for current counts and `python3 tools/gap_audit.py` for connections and lifecycle gaps. The local app in `../../web` imports the same four canonical files and shows the selected earliest records and separate community-entry milestones. Its “Why this date” explanation retains the named community, alternative dates and evidence limits. Entries awaiting a defensible anchor remain searchable in **Unplaced**.

`tools/coverage.py` compares placement coverage with the committed placement checkpoint. It groups the supplied upper date limit, or the lower limit when only that exists. A known-by limit does not establish the true onset era; these are neither invention counts nor claims of continuous use. `CHECKPOINT.md` records the verified current counts, hashes and remaining limits.

Historical acceptance is scoped to the recorded propositions and inspected passages; it does not certify complete ancestry, source infallibility or full-document reading. A reviewed community-entry date does not complete the separate research into first commercial availability, adoption, decline, niche survival or last use.

Sources distinguish retained originals, mapped excerpts, attributed partial research notes and external-only access. Selected PDF excerpts retain original-document hashes and explicit page mappings. A blocked download or metadata-only representation is never described as a captured original.

## Kind, relation and consequence boundaries

Kinds describe the referent: `science` is empirical knowledge or explanation;
`mathematics` is a formal result, representation or calculation method;
`technology` is an artifact, instrument, material or reproducible technical process;
`practice` is a learned operational, social or navigational skill/system. Physical
mathematical instruments remain technology. A cultural setting does not by itself
turn a technical process into practice. Witnesses do not inherit their broader
achievement's kind or importance merely from their material substrate.

`documented-development` remains the broad evidenced contribution relation;
`documented-transmission` requires actual transfer. `documented-adaptation` requires
modification of a prior design. Instrument, production and theory relations state
the specific contribution. `bounded-technical-requirement` describes a necessary
function in the scoped configuration, without claiming personal transmission or
universal historical inevitability. `companion-of` means evidenced co-function or
parts of one configuration; `same-principle` and `same-family` express documented
technical affinity. These three are noncausal and excluded from causal ancestry,
reach and impact counts. Mere co-documentation warrants no link.

Every link has one `influence` field: minor, contributing, major, essential or
not_assessed. Confidence concerns support for the statement; influence concerns
its strength. Necessity prose is retired and preserved in historical ledgers.

Tier 0 requires visible later dependence across several fields or generations.
Tier 1 is a major field-level contribution, tier 2 a bounded contribution/use or
transmission, and tier 3 fine detail or a witness. These are editorial consequence
judgements. Documentation volume, regional representation and survival of a good
witness are not ranking criteria. `handovers/revision/stage4-tiers.json` records
the one-pass judgement for every entry and the reason for every move.
