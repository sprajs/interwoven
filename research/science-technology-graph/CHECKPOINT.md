# Current implementation

Authoritative directory: `/Users/szymon/Documents/ChatGPT/big_idea/research/science-technology-graph`.

One initial version-1 schema governs the current nodes, events, relationships and sources. Current reviews bind exact assertions to hashes. Source evidence includes retained originals and mapped excerpts; explicit unknowns remain unresolved.

The current placement policy is community entry: availability, actual use, adoption, recognition or explicitly qualified awareness in a named community. One-sided dates retain their missing bound. First commercial availability remains a separate research question. Use `python3 tools/query.py stats` and `python3 tools/gap_audit.py` for live coverage; the JSONL files and query tool are authoritative.

Validated placement checkpoint, 6 November 2026: 143 nodes are placed, with 292 separately scoped events, 104 relationships and 195 sources. The 143 placements comprise 81 direct evidence choices, 24 contextual inferences and 38 explicitly labelled awareness proxies. There are 97 known-by choices; their earlier limits remain unknown. All 539 current node/event/relationship decisions match their exact proposition hashes, and 178 distinct nonempty local source copies match their declared hashes. These counts describe this checkpoint; subsequent reviewed expansion is recorded in later commits.

The composed review in `reviews/community-entry.json` preserves the final independent assessments, accepted patch hashes and the verified baseline used for unchanged fields. Deterministic event ownership and source-provenance unions are identified separately from historical judgments. Exact composition does not imply that all lifecycle questions have been answered.

Validation commands:

```sh
python3 tools/validate.py --json --strict-concerns
python3 -m unittest discover -s tests
```

From the repository's `web` directory:

```sh
npm run import
npm test
npm run build
npm run validate
```

Work remains on `main`. Completed units are recorded as local Git commits; other writers also use this checkout and remote. This execution does not push Git changes, publish or modify the hosted Site, or resume the paused expansion automation.

The research gaps and missing evidence are recorded in `BACKLOG.md`. Current historical acceptance does not turn unresolved commercial, adoption or end-of-use questions into dates.
