# Verified expansion checkpoint

Authoritative directory: `/Users/szymon/Documents/ChatGPT/big_idea/research/science-technology-graph`.

The 6 November 2026 pass is complete at **221 entries, 387 events, 131 relationships and 310 sources**. It added 81 reviewed entries to the 143-entry placement checkpoint, then merged three duplicate identities without losing the distinct historical witnesses. All 221 entries have selected community-entry anchors, all 131 relationships have placed endpoints, and every entry has an explicit display tier and a chart label. No further expansion round is included.

One initial version-1 schema governs the four canonical JSONL files. Placement uses the best defensible availability, actual use, adoption, recognition or explicitly qualified awareness in a named community. It does not automatically use invention, first surviving manuscript or modern museum access. First commercial availability remains a separate question.

## Changes and evidence

- Mathematics, regional infrastructure, materials, mechanics, electronics and molecular/medical cases supplied the 81 additions. The three duplicate resolutions concern the Intel 4004, Hoerni planar configuration and physically isolated Fairchild prototype.
- The common-measure entry now uses Iamblichus's scholarly use by approximately 325 CE, retaining Nicomachus and the 888 manuscript as distinct witnesses. Abū Kāmil uses the explicitly inferred al-Karajī reception around 1010; its later witness remains. Rhind retains the competing approximate 1650–1550 BCE estimates without added padding.
- Thirty-two event statuses were reconciled with their already accepted approximate bounds, including 30 selected anchors. No numeric date or missing bound was invented. Exact bounds whose surrounding discussion mentions a different approximate fact remain exact. The importer derives approximation from the structured status. The chronology validator does not infer definite reversal from an approximate nominal limit.
- The 221 placements comprise 132 direct-evidence choices, 51 scoped inferences and 38 awareness proxies. There are 154 known-by placements with no invented earlier bound; the remaining 67 retain both supplied limits.
- All 739 current node, event and relationship decisions match exact proposition hashes. Constituent review ledgers embed the accepted input projections and independent assessments; temporary filenames are provenance rather than inspection dependencies. Historical acceptance does not complete lifecycle classification.
- 296 source records reference 285 distinct nonempty retained files. Every declared SHA-256 matches the working copy and staged Git bytes; there are no duplicate byte-identical cache files. Fourteen sources have no retained file, with access limits left explicit. The redundant Micrologic copy was consolidated with an audited path-only change. The existing Liu Hui source's credited authors and December 2003 update metadata were corrected against its retained HTML.
- All 36 candidate questions have findings: four confirmed links, three merged duplicate pairs, one resolved product/class identity, and 28 insufficient-evidence findings. No question points to a removed node. Insufficient evidence does not establish historical absence or independent invention.

## Placement coverage

Baseline: placement commit `96b3199fad144880636bede3ae7d750d1b6f6dd3`.

| Supplied placement limit | Before | After | Change |
| --- | ---: | ---: | ---: |
| Before 500 CE | 9 | 23 | +14 |
| 500–1499 | 24 | 42 | +18 |
| 1500–1749 | 11 | 16 | +5 |
| 1750–1944 | 53 | 86 | +33 |
| 1945 onward | 46 | 54 | +8 |
| Total | 143 | 221 | +78 |

Reproduce with `python3 tools/coverage.py --baseline 96b3199`. The bins use the supplied latest year, or the earliest year for a lower-only date. A known-by limit does not establish the true onset era. These are placement counts, not invention dates or evidence of continuous use.

## Verification and preview

Strict graph validation passes with zero errors and zero concerns. All 92 Python tests and 42 web tests pass; web import, validation and the production build pass. Real-browser checks use the expanded saved-repository dataset, verify its network bytes against the generated file, and cover desktop/mobile rendering, search, label filtering, detail panels and WebGL. There are no browser page or console errors.

The local preview is [http://127.0.0.1:5186/](http://127.0.0.1:5186/). Current real-data captures and their checks are in `../../web/output/playwright/browser-check.json` and the `current-community-*.png` images. Superseded interwoven screenshots and unused synthetic capture artifacts were removed. No hosted preview was published.

Run from this graph directory:

```sh
python3 tools/validate.py --json --strict-concerns
python3 -m unittest discover -s tests
python3 tools/gap_audit.py
python3 tools/coverage.py --baseline 96b3199
```

From `../../web`:

```sh
npm run import
npm test
npm run validate
npm run build
```

## Exact artifact hashes

SHA-256 of complete file bytes at this checkpoint:

| Artifact | SHA-256 |
| --- | --- |
| `data/nodes.jsonl` | `fffbb3154ef88e626e65ac036abcfca26daad22d2eecb0bc85994df9076c75ee` |
| `data/events.jsonl` | `0791e91897c331424cdcad2a7b12f7881fa68a311c63c176c9c4a1eaa5fdb1bb` |
| `data/relationships.jsonl` | `58940def127f0f70aa402f766474d101d69de4658039e5e2edb6288ed8a6b932` |
| `data/sources.jsonl` | `74a52c569ec8fc0813a33eab6313b6a121c0f9210d7bc41feb8b1490e8f4cac2` |
| `schema.json` | `315ab1cb21a1a48f198620b79e407f12b9e4cbf49af17bc415a0c99e62c26958` |
| `reviews/current-evidence.json` | `1c4ce980cee3b9c3343137e55b645a4d9b0803089db667879784a33824a739d2` |
| `../../web/public/data/timeline.json` | `d36c2e026a8039842d156d3537c26cf6869b30481919331f93bb2a7bd81e1dba` |

## Remaining research and Git boundary

First commercial availability is documented for 2 of 171 technology entries, unknown for 12 and unresearched for 157. Lifecycle evidence has 2 adoptions, 2 withdrawals and 1 abandonment, with no documented decline, revival or end-of-use episode. The graph has 98 fragments and 59 isolated entries. There are 214 node lifecycle classifications still needing review. These remain explicit gaps; all entries being placed does not make their histories complete.

`BACKLOG.md`, `handovers/gap-audit.md` and the assessed candidate file preserve the current research gaps. The optional Chinese fraction-reduction addition is deferred beyond this pass; its tradition is not linked to the Greco-Roman procedure. The Ibn al-Bannā/al-Qurashī earlier-reception lead remains unresolved.

Work remains on `main`. This checkpoint is recorded in a local commit after placement commit `96b3199`; this execution does not push, change the hosted Site or modify the expansion automation. The last verified remote main was `3df3f220690729bc70d5c8eddcdd113a4632086b`. Other writers had previously updated that remote, so this statement describes this execution's boundary rather than every earlier session action.
