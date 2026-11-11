# R3 relationship-evidence and historical-map review

**Decision: the five sampled relationships withstand targeted source checks, but the frozen R3 edition does not yet supply the requested integrated historical relationship map.** Its case library and comparative synthesis have materially improved. This is a verdict on the snapshot captured at 2026-11-05 16:36:43 UTC, not on the separate historical layer now being prepared.

The sample was saved in [selection.json](selection.json) before original-source checks. It comprises all three newly introduced documented-transmission edges and two new cross-strand comparisons. Seven distinct cited works (nine contribution-local source IDs) were inspected. This is purposive risk sampling, not an estimated error rate for the collection. No unchanged accepted claim was reopened except where needed to test a new comparison.

## Remaining acceptance issue — R3-REL-F01 (P1)

The graph has **428 nodes, 299 edges and 138 weak components**, compared with 347/246/109 in R2. Its largest component has seven nodes. There are zero cross-strand edges, zero edges joining endpoints with disjoint case IDs, and zero multi-case edges. All ten documented-transmission edges stay within individual cases. These calculations are retained in [topology_checks.json](topology_checks.json); the graph remains internally referentially valid.

There is meaningful integration elsewhere: 69 comparisons include ten cross-strand comparisons, and their analytical case graph connects 81 of the 88 cases in its largest component. The new Ghana and Chinese-textile comparisons are substantive, source-consistent interpretations. The nine chronological routes cover all 88 cases. However, those routes contain only IDs, titles, scopes and case lists; they explicitly add no historical or causal relationships. The narrative organises mechanisms and comparisons rather than supplying a traversable history of developments, transmissions and convergences across cases.

Exact snapshot anchors: analysis/GLOBAL_MAP.md:3–5 and 38–40; data/CHRONOLOGICAL_ROUTES.md:3–5; analysis/SYNTHESIS.md:21; data/GRAPH_GUIDE.md:3–5. The GLOBAL_MAP diagram at lines42–53 is explicitly an analytical reading guide. The caution is epistemically appropriate; it also states the present deliverable boundary.

**Acceptance condition:** assess the separately planned historical layer once it provides explicit configuration endpoints, dates and regions, typed relationships, evidence passages, alternatives and uncertainty, with substantive routes linking relevant cases across the requested eras and regions. Distinguish documented development/transmission, scoped engineering dependence, chronology and analytical comparison. A single forced genealogy or a fully connected graph is unnecessary. Unknown links must stay unknown. This audit neither reviews nor prejudges the forthcoming layer.

## Preregistered source results

| Relationship | Result and evidence boundary | Exact snapshot record |
|---|---|---|
| SKL-E01 | Supported named H4-to-K1 replication. Museum sheet and contemporary obituary transcription support another maker’s copy; no serial-manufacture or universal-necessity inference. | data/graph.json:12775; claim SKL-K01 at data/claims.json:8383 |
| SKL-E09 | Supported bounded apprenticeship transmission. Grace’s direct participation and retrospective histories support supervised learning, without representative effectiveness or exclusive-route claims. | data/graph.json:13028; SKL-K10 at data/claims.json:8639 |
| SKL-E16 | Supported early TEA network transmission. Collins preserves failed contacts and possible written-only success; contact is neither sufficient nor universally necessary. | data/graph.json:13248; SKL-K16 at data/claims.json:8803 |
| GHA-X02 | Supported cross-strand comparison. African road/lorry agency and railway spatial effects are compatible; shared scholarship is acknowledged. Earlier complementarity and later competition are period-scoped in GHA-E02/E03. | data/comparisons.json:326; GHA-E02/E03 at data/graph.json:6948/6979 |
| CTX-X01 | Supported cross-period comparison. Earlier factory-yarn hybrids and later constrained household production use different parts of the same Eyferth article. No common causal denominator or backward projection is asserted. | data/comparisons.json:154; CTX-K01/K02/K03 at data/claims.json:1403/1427/1456 |

The transmission edges are real local historical relationships; the two comparison records are real analytical connections. They should not be counted as five cross-case causal-development paths.

Original-source locators and access:

- [RMG K1 object sheet](https://www.rmg.co.uk/sites/default/files/import/media/pdf/K1.pdf), Description; [Kendall obituary transcription](https://www.captaincooksociety.com/cooks-life/people/cooks-officers-and-crew-and-contemporaries/larcum-kendall-obituary), opening copying paragraphs. The reported 1769 completion and approximate 1771 delivery are different events, not necessarily contradictory dates.
- [Grace, African Motors](https://www.bibliopen.org/p/bopen/9781478094456), printed pp. 94–95 and 117–121; original book cache text lines 3982–4000 and 4840–4992.
- [Collins, The TEA Set](https://research.engineering.nyu.edu/~jbain/scitechsoc/readings/74Collins.pdf), printed pp. 172–173,176–177 and 183; cache lines 383–425,550–625 and 900–931.
- [Austin, Ghana](https://eprints.lse.ac.uk/4392/1/Labour_and_land_in_Ghana_(LSERO_version).pdf), accepted manuscript pp. 5–7; cache lines 272–293,321–341 and 388–419. [Jedwab–Moradi, January 2015 manuscript](https://alexandermoradi.org/research/rail.pdf), §4.1 pp. 11–12 and §5.1.3 p. 18. The repaired GHA-S05/GHA-K11 section/page locators are verified against the original manuscript: sample lines 460–470; migration/citations 735–748.
- [Eyferth 2012 publisher PDF](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/1B4DC63727682F1EEC958A62A4126757/S0020859012000521a.pdf/womens-work-and-the-politics-of-homespun-in-socialist-china-1949-1980.pdf), printed pp. 373–374,379 and 383–387. The live publisher text supplied the checked passages; no local original-PDF hash is claimed.

## Verification and limits

[relationship_audit.json](relationship_audit.json) records judgments and exact JSON pointers. [source_access.json](source_access.json) records passage access, original-document/cache hashes, publication versions and limits. [checks.json](checks.json) records the final selected-input hash recheck and graph reference checks. All four preregistered R2/R3 graph/comparison hashes remain unchanged; no graph endpoint, case, claim or source reference errors were found.

This review inspected targeted passages, not entire books or every claim. It did not recreate underlying Board records, interviews, archives or spatial estimators, and did not re-audit the unchanged engineering-necessity edges. Main research and snapshot files were read only. Browser parity and final live drift remain the parent review’s responsibility.
