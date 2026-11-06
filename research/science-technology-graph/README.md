# Science and technology graph

A local, evidence-backed graph of scientific results and technological configurations. It includes independent regional developments, short-lived experiments, abandoned branches and configurations with no known descendants.

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

## Lifecycle and dates

A technology's invention, prototype, first commercial availability, deployment, adoption and withdrawal are separate events. The graph places each entry at its best defensible entry into availability, actual use, adoption, recognition or awareness within a named community. A dated offer establishes availability by that date without proving the first offer. Local, specialist, customary and research communities count; an entry need not become a successful commercial product.

Scientific results use documented use, recognition, adoption or public availability of a result or dataset. A publication or presentation can supply an explicitly labelled awareness estimate when stronger entry evidence is unavailable. Publication does not establish acceptance. Neither the earliest stored event nor the date of invention or discovery is an automatic display date. Modern museum access or cataloguing dates do not substitute for a historical technology's entry into use.

Every selected anchor states its community, evidence, rationale, scope and uncertainty. Direct evidence, contextual inference and publication-based awareness estimates remain distinguishable in the chart and detail panel. Where an artifact is a witness to a broader technology, an explicit reviewed scope refinement preserves that distinction.

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

Run `python3 tools/query.py stats` for current counts and `python3 tools/gap_audit.py` for connections and lifecycle gaps. The local app in `../../web` imports the same four canonical files and shows the selected community-entry milestones. Its “Why this date” explanation retains the named community, alternative dates and evidence limits. Entries awaiting a defensible anchor remain searchable in **Unplaced**.

`tools/coverage.py` compares placement coverage with the committed placement checkpoint. It groups the supplied upper date limit, or the lower limit when only that exists. A known-by limit does not establish the true onset era; these are neither invention counts nor claims of continuous use. `CHECKPOINT.md` records the verified current counts, hashes and remaining limits.

Historical acceptance is scoped to the recorded propositions and inspected passages; it does not certify complete ancestry, source infallibility or full-document reading. A reviewed community-entry date does not complete the separate research into first commercial availability, adoption, decline, niche survival or last use.

Sources distinguish retained originals, mapped excerpts, attributed partial research notes and external-only access. Selected PDF excerpts retain original-document hashes and explicit page mappings. A blocked download or metadata-only representation is never described as a captured original.
