# Rebuilding and interrogating the edition

The reviewed JSON files in contributions/* are canonical. Contribution-local build/migration scripts are preserved drafting aids; some predate editorial review and must not be replayed over the canonical files. tools/build_synthesis_records.py owns the authored SYN records and must be edited deliberately when synthesis changes.

Run from any directory with Python 3:

```
python /Users/szymon/.codex/worktrees/562f/big_idea/research/technology-adoption/tools/build_collection.py
python /Users/szymon/.codex/worktrees/562f/big_idea/research/technology-adoption/tools/build_chronology.py
python /Users/szymon/.codex/worktrees/562f/big_idea/research/technology-adoption/tools/build_explorer.py
python /Users/szymon/.codex/worktrees/562f/big_idea/research/technology-adoption/tools/check_review_repairs.py
python /Users/szymon/.codex/worktrees/562f/big_idea/research/technology-adoption/tools/check_edition.py
```

Collection generation validates schema, stable identifiers, references, test status, graph scope and necessary-input rationale, then writes JSON, CSV, readable ledgers and case cards. Explorer generation refuses a validation result containing errors. The repair checks verify selected substantive distinctions and exact data transport, preserve snapshot integrity and exercise invalid-record probes in temporary copies. None of these checks proves historical truth or replaces independent reading.

Live Markdown links are checked; immutable selected review snapshots retain their original manifest and historical scope. A selected snapshot need not include every file reached by the original relative links. Source PDFs and extraction caches are local inspection material, not a publication package.

To reuse a graph edge, read its scope, relation direction, basis, claim and source before following another edge. `depends-on` points from a system to a bounded requirement. Multiple incoming edges do not assert sufficiency, a joint requirement, or causal identification. A shared concept label does not equate historical configurations. No automatic transitive inference is warranted across episodes.

For a claim, inspect `statement`, `causal_status`, `test`, `counterevidence`, `inference_limits` and each supporting locator. `confidence` concerns that bounded statement. An evaluated test can reject a categorical proposition without identifying the strongest remaining mechanism; independent reviews address that distinction. Source-count and case-count summaries are inventory, not evidential weights.

For complete-edition checks also run build_chronology.py before build_explorer.py, and check_edition.py after generation. It checks all canonical contributions against their compiled counterparts, all CSV fields, embedded HTML data, chronology coverage and frozen snapshot hashes. data/EDITION_CHECKS.json is the result. The final generation/integrity records identify accepted bytes. The selected external review archive `later-selected` is excluded from live-link closure just like other immutable snapshots; its own hashes are checked.

Contribution author handoff manifests and earlier validation.json files are provenance from that handoff, and can predate editorial repairs. contributions/*/EDITION_VALIDATION.json and data/validation.json identify current integrated canonical hashes/counts. Do not replay contribution-local drafting builders over reviewed JSON. Final acceptance is in the independent review reports and response log, not in a structural pass alone.

The authored `contributions/SYN/synthesis_specs.json` can be compiled with `build_synthesis_records.py` when deliberately revising the synthesis. It is included in the generation manifest; comparisons remain separately authored canonical records.

To verify the delivered bytes without rebuilding, run `python tools/verify_integrity.py` from the research root (or use its absolute path). It checks both `data/GENERATION_MANIFEST.json` and `FINAL_INTEGRITY.json`. Rebuilding refreshes the dated contribution validation records, so a later rebuild can correctly differ from the delivered-byte manifest. Preserve the original manifest when making a new edition. Historical review targets and their verdicts must not be overwritten with the new state.
