# Rebuilding and interrogating the edition

The reviewed JSON files in contributions/* are canonical. Contribution-local build/migration scripts are preserved drafting aids; some predate editorial review and must not be replayed over the canonical files. tools/build_synthesis_records.py owns the authored SYN records and must be edited deliberately when synthesis changes.

Run from any directory with Python 3:

```
python /Users/szymon/.codex/worktrees/562f/big_idea/research/technology-adoption/tools/build_collection.py
python /Users/szymon/.codex/worktrees/562f/big_idea/research/technology-adoption/tools/build_explorer.py
python /Users/szymon/.codex/worktrees/562f/big_idea/research/technology-adoption/tools/check_review_repairs.py
```

Collection generation validates schema, stable identifiers, references, test status, graph scope and necessary-input rationale, then writes JSON, CSV, readable ledgers and case cards. Explorer generation refuses a validation result containing errors. The repair checks verify selected substantive distinctions and exact data transport, preserve snapshot integrity and exercise invalid-record probes in temporary copies. None of these checks proves historical truth or replaces independent reading.

Live Markdown links are checked; immutable selected review snapshots retain their original manifest and historical scope. A selected snapshot need not include every file reached by the original relative links. Source PDFs and extraction caches are local inspection material, not a publication package.

To reuse a graph edge, read its scope, relation direction, basis, claim and source before following another edge. `depends-on` points from a system to a bounded requirement. Multiple incoming edges do not assert sufficiency, a joint requirement, or causal identification. A shared concept label does not equate historical configurations. No automatic transitive inference is warranted across episodes.

For a claim, inspect `statement`, `causal_status`, `test`, `counterevidence`, `inference_limits` and each supporting locator. `confidence` concerns that bounded statement. An evaluated test can reject a categorical proposition without identifying the strongest remaining mechanism; independent reviews address that distinction. Source-count and case-count summaries are inventory, not evidential weights.
