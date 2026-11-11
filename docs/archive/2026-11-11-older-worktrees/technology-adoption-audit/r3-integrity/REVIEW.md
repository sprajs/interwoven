# R3 independent integrity, chronology and navigation review

**The four R2 defects are closed at the frozen-data and inspected-code level. The edition is now a consistent, navigable research library. It does not yet supply the requested integrated historical relationship map.** This remaining scope gap should not be confused with a requirement to force its historical evidence into one connected tree.

The review target is `r3-snapshot`, captured 5 November 2026 at 16:36:43 UTC: 88 cases, 329 claims, 204 source records, 428 nodes, 299 edges and 69 comparisons across 17 complete contributions (16 case-bearing strands and SYN). All 387 files listed in its outer manifest match their hashes before and after this review. I did not write to the snapshot or live programme, contact programme participants, push or publish. All new artifacts and test copies are in this review directory. The announced future relationship layer is outside this review.

This is an independent integrity and reading-path audit, not another historical-source audit. The code checks below execute the frozen explorer's routing/render functions in Node with minimal JSON/location fixtures. They do **not** establish live browser behavior, layout, keyboard/focus handling, reload/new-tab behavior or accessibility. The parent reviewer owns the browser attempt and final live-main drift check.

## R2 closure and transport

| R2 finding | Result in this frozen edition |
|---|---|
| R2-01, OCE canonical/export disagreement | Closed. All 17 complete canonical dossiers exactly equal their compiled records, including ordering, for cases, claims, sources, nodes, edges and comparisons. OCE governance records OCE-T26/OCE-E19 are present. All current contribution hash records match their canonical files. |
| R2-02, obsolete 59-case chronology/synthesis | Closed at its stated stale-edition/case-coverage scope. Synthesis 2 explicitly integrates the added ENE/OCE/POL/PSY/SKL strands and CTX/GHA additions; every one of 88 cases appears in the current chronology. The route limitations below are a narrower usability issue, not an obsolete edition. |
| R2-03, references not directly navigable | Closed at source/executable-function scope. Typed case, claim, source, node, edge and comparison views now link to one another, with case return context and source-specific claim locators. All 18,917 internal links emitted by rendering all 1,417 records resolve to known typed records or routes. |
| R2-04, section hashes overwrite case identity | Closed at source/executable-function scope. URLs separately encode `view`, `id` and `section`; all 528 case/section combinations retain identity when reparsed. Old case-only hashes migrate to typed URLs, while ambiguous old `#relations` links explicitly require a case. Actual browser reload/new-tab acceptance remains outside this subreview. |

Four CSV exports preserve their complete record-key unions, row order and all 8,207 populated field values, including nested JSON. Seven embedded HTML payloads—cases, claims, sources, comparisons, graph, validation and chronology—exactly equal the compiled JSON. There are no duplicate record IDs or unresolved structured references. This establishes transport fidelity, not historical truth.

Evidence: [verification.json](verification.json), [navigation-verification.json](navigation-verification.json), [audit_integrity.py](audit_integrity.py), [check_navigation.mjs](check_navigation.mjs). Exact owning file/line and ID locators, with hashes, are in [source-locators.json](source-locators.json).

## Reproduction and the selected-snapshot boundary

Unmodified stock tools were run only in [rebuild-copy](rebuild-copy). Collection generation regenerated **106 core output files byte-for-byte**, including JSON, CSV, readable ledgers, all case pages, chronology and its Markdown index. Generating the explorer separately from the frozen validated data produced a byte-identical HTML file.

The complete stock pipeline cannot pass on this selected snapshot without assets deliberately outside the capture. `build_collection.py` reports 51 missing local links, all to omitted review/archive/UI evidence or CTX evidence notes. It then marks validation invalid; `build_explorer.py` correctly refuses that result. `check_review_repairs.py` stops at the omitted round-one snapshot manifest. `verify_integrity.py` stops at `data/GENERATION_MANIFEST.json`, which was not captured; `FINAL_INTEGRITY.json` is also absent. These are **limits of this review target**, not observed defects in the live programme.

`check_edition.py` passes 139 checks on the original copy, but reports **zero nested review snapshots and zero nested review files checked**. That pass must not be described as verification of excluded review archives. The independent outer-manifest check does verify all 387 captured files. Only `data/validation.json` and `data/EDITION_CHECKS.json` change during the isolated run, for the selection-dependent reasons above. Full commands/results and missing paths remain in the machine-readable verification and individual tool logs.

## Reading paths and uncertainty

The revised interface provides meaningful paths that the R2 edition lacked:

| Reading task | Supported path and its limit |
|---|---|
| Inspect oral rehydration evidence | `MED-C07 → MED-E18 → MED-K20 → MED-S14`, with the claim-specific “pp. 59–60, Box 1 and Methodology” locator and a return URL retaining MED-C07/relations. This is a provenance path, not source entailment verification. |
| Compare precision/navigation across regions and centuries | `SKL-C01 → SYN-X07 → OCE-C01 → SYN-X07`. The destination preserves the comparison ID in `via`; both cases and the comparison remain accessible. Its question concerns tools/instruction/feedback and expressly limits claims of universal necessity. |
| Compare Chinese/Korean/European printing | An early-modern reader can enter NET-C04, then follow NET-X01 to NET-C02 and NET-C03. The comparison preserves differences and does not assert a historical transmission arrow. The chronology itself has the later-episode omission noted below. |
| Read water rights and public authority across regions | OCE-C02 is available from ancient, twentieth-century and recent routes, then SYN-X03/SYN-X08 link it to African, Asian and European institutional cases. These are analytical contrasts; they do not imply historical connection. |
| Follow an exact graph node | Each node view exposes its incident edges and the cases in scope. The tested MED-T25 view links MED-E18. Similar labels elsewhere remain separate identities. |
| Inspect ancient production versus reconstruction | MAT-C04 retains the ancient/experimental distinction in its period, episode and graph scopes. Its comparison network is a separate three-case component; the reader can return to chronology for the rest of the collection. |

Claims show confidence, causal status, sources and locators. Their test/rival/ambiguity details are expanded on the claim view and available behind a disclosure on case pages. Source views retain access, evidence lineage and scope limits. Edge cards show confidence, basis, scope and qualification, with alternatives, joint inputs, necessity rationale and dispute available. Comparison records retain differences, shared evidence, omitted countercases and conclusion limits. Chronology shows both case period and episode interval, with observation limits available. These protections should survive any map redesign.

## Graph and comparison topology

The graph has **138 weakly connected components**. The largest has seven nodes. Component sizes are: one of 7, six of 6, thirteen of 5, twenty-seven of 4, thirty-five of 3, fifty-one of 2 and five isolated nodes. The isolated nodes are AGR-T01, GHA-T12, MAT-T07, NET-T12 and NET-T13; their isolation is not itself a defect.

No edge has multiple case IDs; no edge crosses contribution-owned endpoints; every edge's endpoints share at least one case. Three shared nodes do make multi-case components: IND-T01 spans IND-C01/C02, IND-T14 spans IND-C04/C05, and ENE-T01 spans ENE-C01/C03. This distinction matters: it would be wrong to say that **every** graph component is single-case. It would also be wrong to treat these shared local nodes as a global historical network.

The 299 edge bases are 210 observed contributions, 40 technical possibilities, 30 hypotheses, 9 bounded necessities and 10 documented transmissions; there are no inferred-transmission records. The documented transmissions concern specific episodes in ENE, MED, OCE and SKL. Their qualifiers remain bounded, for example named replication, teaching channels, and contact in a studied early laser-building network. These are useful historical relationships, not a continuous lineage spanning the collection.

All 88 cases occur in at least one comparison. Treating each comparison as an undirected case association yields four components: 81 cases; MAT-C03/C04/C07; AGR-C01/C02; and MAT-C01/C06. Ten comparisons cross contribution boundaries. This is substantial comparative connectivity, but it is **analogy/contrast connectivity**, not technical dependence or transmission. Full component membership, relation/basis counts and transmission records are retained in verification.json.

## Residual findings

**R3-INTEGRITY-01 — P2, unmet map scope.** The current top-level explorer has Cases, Chronology and Comparisons. Its graph displays are case-local edge cards, individual edges and incident-node views. `GLOBAL_MAP.md` supplies dated buckets, regional coverage prose, and an expressly analytical Mermaid diagram. It explicitly states that the graph comprises scoped networks, and the synthesis says a continuous cross-era dependency history is not established. Those caveats are honest. They do not supply the requested integrated historical relationship map.

Acceptance should require a navigable historical overview that keeps four meanings distinct: evidence-bearing transmission/development; configuration-scoped engineering dependence; chronology/context; and analogy/comparison. A reader should be able to select a relationship and reach its exact case, claim, source locator, dates and uncertainty, and see where a historical path is absent or unresolved. Existing evidence should be surfaced before new arrows are added. An acceptable overview may retain disconnected histories and unresolved regions; merging similar names, inferring transmission from date order, or imposing a unified tree would fail the requirement. The forthcoming layer needs its own review rather than inheriting this edition's parity pass.

Owning evidence: `tools/build_explorer.py:51–57,177–237`; `analysis/GLOBAL_MAP.md:36–63`; graph statistics above. This is a scope gap, not a request to make 138 components mathematically connected.

**R3-INTEGRITY-02 — P3, era-route discoverability.** All cases are covered, but not all significant operating subepisodes are discoverable through the matching era entry. NET-C02 spans 868–c.1850 and NET-C03 spans 1377–early nineteenth century, yet each appears only in the “broadly pre-1500” route. The fifteenth–eighteenth-century publishing route includes NET-C04/C05/C06 but omits those East Asian cases. NET-X01 supplies an indirect bridge, and the broad-route caveat avoids a false dating claim; still, this is weaker comparative chronology than the complete case count suggests. Add later-episode memberships or explicit episode links while keeping modern observation/reconstruction dates distinct from operating dates. See `analysis/chronology_routes.json:40–91` and the two case records; [reading-paths.json](reading-paths.json) inventories all periods and memberships.

**R3-INTEGRITY-03 — P3, Markdown inventory navigation.** `GLOBAL_MAP.md:38` says the edge inventory links each relationship to cases, claims and sources. The Markdown generator instead emits plain IDs and no source column (`tools/build_collection.py:223–232`); comparison Markdown also has plain case IDs. The explorer now resolves these paths correctly, so this does not reopen its R2 repair. Link the Markdown IDs to the corresponding explorer/case/evidence views or describe the inventory accurately as an unlinked summary.

Machine-readable decisions and acceptance criteria are in [FINDINGS.json](FINDINGS.json). The frozen edition passes this review's data-integrity and repaired-navigation checks; the historical-map scope remains open.
