# R1 bounded graph, measurement and rival-test review

Reviewed 5 November 2026 against the frozen `r1-snapshot`, including METHODS and METHODS_ADDENDUM_V2. The main collection was neither inspected nor changed. This is a bounded review of an active research programme, not a certification that unfinished contributions are complete.

**Decision:** the v2 records largely preserve the intended distinctions. One substantive graph-identity repair is needed before treating the graph as a reusable model. IND remains provisional for this frozen export because its questions file is absent. No reviewed edge requires a claim of universal necessity, automatic transmission, free worker consent or transitive causal closure.

## Scope and denominators

Structural checks cover all **23 cases, 78 claims, 49 source records, 93 nodes, 72 edges and 13 comparisons** in MAT/ANC/IND/LBR. All case v2 objects, claim-test structures, graph fields/references, source-lineage entries and comparison fields were screened; the machine results preserve exact IDs and JSON pointers. This denominator is not a source-entailment audit.

The detailed purposive sample is **10/72 edges**, linking **11/78 claims** and **10/49 source records**: ANC-E06, ANC-E07, ANC-E11, IND-E01, IND-E09, IND-E27, IND-E28, MAT-E06, MAT-E08 and LBR-E01. Selection targets cross-episode node identity, a normal physical necessity, coerced labour/funding, a joint-input bundle, ancient/experimental evidence, and weak-access causal interpretation. The sample was selected adaptively by risk; it cannot estimate an error rate.

Actual source passages were independently inspected for **3/49 source records**, supporting **4/10 sampled edges**: ANC-S05 → ANC-E06/E07, ANC-S07 → ANC-E11, and the LBR-S01 author abstract → LBR-E01. No full MAT or IND source audit was duplicated. Detailed sample records, assessments, claim tests and source-check locators are in [edge_audit.json](edge_audit.json).

## G01 — P2: preserve distinct local configurations as distinct nodes

The v2 contract explicitly requires local configurations to retain distinct nodes. Two identities fail that requirement even though their edge scope text is careful:

- **IND-T02**, `contributions/IND/graph.json#/nodes/1`, is “Dependable accessible waterpower” shared by IND-C01 and IND-C03. IND-E01 (`/edges/0`) concerns sixteenth-/seventeenth-century central-European mine pumping. IND-E09 (`/edges/8`) concerns British textile mills. This creates the directed adjacency IND-E09 → IND-E01; other cross-case adjacencies are IND-E10 → IND-E01 and IND-E11 → IND-E01. In particular, the latter is an enables/enables route from proposed British reservoirs to central-European mine pumping through one generic waterpower node. The fact that both edges describe waterpower does not establish identity of the physical resource or operating configuration.
- **MAT-T28**, `contributions/MAT/graph.json#/nodes/25`, explicitly combines “Later/post-Meroitic bloomery process and its modern replica.” MAT-E08 (`/edges/7`) targets it on ancient Meroe/Hamadab charcoal evidence; MAT-E06 (`/edges/5`) leaves it under a modern experimental primary-reduction counterfactual. The shared node joins ancient fuel selection to a modern experiment, although MAT-C04.episode and the individual edge scopes distinguish them.

This does **not** mean the explorer currently computes invalid causal closure: it renders scoped edge cards, explicitly warns against transitive inference, and contains no path-inference engine. Nor is a competes-with/depends-on path equivalent to an enables chain. The problem is the exported identity relation itself and future traversal/reuse. Generic warnings do not implement the separate-node requirement.

**Repair:** split IND-T02 into central-European mine-waterpower and British textile-waterpower nodes, and MAT-T28 into the ancient operating configuration and modern replica configuration. Retarget local edges; add a separately evidenced comparison or reconstruction relation only if the permitted schema can express it without implying identity/transmission. Review IND-T01 and IND-T14 as further multi-case-node flags; sharing a case is not automatically an error, and those were not adjudicated as equivalent defects here.

**Re-review:** inspect all incident edges, then rerun reference checks and inspect same-case cross-subepisode paths as well as cross-case paths. Check that MAT-E08 no longer shares an operation node with MAT-E06, and that IND-E11 can no longer reach mine pumping solely through a generic waterpower identity. Do not ban every multi-case node mechanically; require a documented identity argument where one is retained.

## R02 — provisional handoff: frozen IND completeness and export metadata disagree

`contributions/IND/questions.md` is absent. The frozen `data/validation.json` labels IND completed while recording `contributions/IND/report.md -> questions.md` as broken. That metadata has broader programme counts and must not be used as this snapshot's verified denominator.

Rebuilding an **unmodified temporary copy** with frozen `tools/build_collection.py` classifies IND as incomplete through lines 43–47 and exports 15 cases, 53 claims, 33 sources, 61 nodes, 42 edges and 9 comparisons. Thus this particular frozen rerun excludes all IND-C01–C08, IND-K01–K25, IND-S01–S16, IND-T01–T32, IND-E01–E30 and IND-X01–X04. The completeness gate is intentional and appropriate for unfinished work; this is not inherently a data-loss bug or proof that the current main collection is faulty. Treat IND as provisional until its actual handoff is complete and validated.

A second **controlled temporary-copy run** added only an explicit audit-only placeholder for the missing questions file. This was solely to test data transport, not to supply or approve research content. All 23 cases/78 claims/49 sources/93 nodes/72 edges/13 comparisons then survived JSON export exactly apart from the intended contribution metadata. CSV nested fields round-tripped with no field mismatches. The explorer's embedded JSON exactly matched all six compiled payloads; static render code exposes episode, actors, labour, tests, edge scope/basis/alternatives/joint inputs/necessity/dispute, and source lineage. Both copy runs still report two external-design Markdown links omitted from this frozen audit scope; these do not establish live-collection broken links.

**Re-review:** after the researcher completes the real IND handoff, regenerate validation and exports, assert the intended contribution/ID denominator, and check the final explorer against that generation. A successful explorer build alone is insufficient: frozen `build_explorer.py` reads validation metadata but does not reject its errors. No visual/browser behaviour was independently tested here.

## What the substantive checks support

The actor fields generally separate owners' investment decisions from operators' consent. ANC-C03 identifies enslaved workers without interpreting translated expense terminology as voluntary employment. IND-C04 names poor-law, prison and household dependence; IND-C05 distinguishes colonial tariff authority and enslaved commodity labour from producer choice. IND-C06 records employer equipment choice while leaving freedom to exit unknown. LBR-C01 separates company decisions, incumbents and future cohorts. Archaeological cases explicitly acknowledge unknown rights and pay; those unknowns are legitimate, not empty evidence.

Measurement fields also mostly avoid inappropriate denominators. MAT-C01 distinguishes 801 selected samples and 722 interpreted lipid samples from households/meals; MAT-C04 separates experimental yields from ancient output; ANC-C02 separates an installation and sampled flumes from diffusion; IND-C06 separates supplier orders from installed/used machinery; IND-C08 separates motor horsepower from unit-drive prevalence; LBR-C01 separates incumbent and entrant designs; LBR-C02 separates title shares/imputed employment from directly counted workers. These are substantive limitations rather than generic boilerplate. The review did not independently recompute those numerical datasets.

Across the 78 claims, 31 tests are descriptive-only, 39 underdetermined and 8 evaluated. The sampled explanatory claims name rivals, distinguishing observations, inspected evidence and remaining ambiguity. In particular IND-K24 identifies demand/new capital as an alternative to electrification/redesign effects; IND-K08 states that a reservoir coordination argument remains abstract-only; MAT-K12 admits coupled experimental changes. “Evaluated” therefore need not mean isolated causal identification. The descriptive claims inspected report bounded textual/configurational findings or attributed estimates; no clear causal assertion relabelled descriptive to escape testing was found in the detailed sample.

The graph has 42 observed-contribution, 12 hypothesis, 8 bounded-necessity and 10 technical-possibility edges; no documented-/inferred-transmission edges are asserted. All eight depends-on relations use bounded-necessity. All references resolve. Nonempty joint-input lists occur only at ANC-E01/E02 and IND-E27/E28. The detailed IND pair names reciprocal complementary inputs, retains onsite supply as an alternative, and explicitly disclaims necessity; neither paired edges nor their joint lists prove sufficiency. Empty lists elsewhere correctly mean no bundle assertion.

The 49 source lineages and 13 comparisons usually identify real shared evidence: Barbegal specimen reuse; Frontinus reused by legal scholarship; Meroe project overlap; Ile-Ife excavation/research overlap; British engine histories; shared India-trade series; and US census/cutover constructions. Counts are expressly not independent confirmation counts. No lineage-count misuse was found in the reviewed graph exports or comparisons. These textual lineage assessments are not a reconstructed citation network.

## Source-passage controls

ANC-E06/E07 are supported as reported arrangements: Frontinus names the two enslaved gangs and specialist duties, then specifies treasury receipts and imperial funding. His report also describes diversion of workers and proposed discipline; it cannot establish achieved reliability or free labour. [Frontinus, Book II §§116–118](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Frontinus/De_Aquis/Bennett/2%2A.html).

ANC-E11 is an ordinary correct bounded necessity. Procopius describes current driving wheels between boats. The qualification appropriately separates that physical relationship from the narrative's unmeasured assertion of adequate city supply. [Procopius, Wars V.19.19–28](https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Procopius/Wars/5C%2A.html).

LBR-E01 accurately attributes the abstract's account of adaptation, interdependence and profitable market scale. Its underdetermined test and explicit weak-access dispute prevent treating the author summary as an independently identified organisational effect. The full article's internal evidence remains unaudited here. [Feigenbaum and Gross, author abstract](https://jamesfeigenbaum.github.io/research/att/).

## Nonblocking follow-ups

**Confidence propagation:** automated checks flag several edges rated above every linked claim. This is not automatically an error: ANC-E11 is a narrower physical counterfactual than the whole historical account, and LBR-E02's direct task displacement is narrower than net labour effects. MAT-E03 and MAT-E12, however, are both high while their sole linked claims MAT-K04 and MAT-K10 are medium; no explicit confidence-upgrade rationale is given. Reconcile those labels or explain the narrower proposition. These two are supplementary record-level flags, not additional source-audited sample edges. Do not mechanically cap every edge at the weakest linked claim.

**Validator hardening:** three negative probes in temporary copies show that the frozen validator accepts an invalid non-descriptive test status, a string in edge alternatives, and an empty necessity rationale. The real frozen records pass these stronger checks, so this is future protection, not evidence of present corrupted data. Add enum/type/nonempty checks if relying on the validator for v2 acceptance.

All manifest-listed frozen input hashes still match. The only persistent writes are this reviewer directory. [structural_results.json](structural_results.json) records counts, IDs, JSON pointers, all detected cross-case adjacencies, confidence flags, export results and negative probes. [check_structure.py](check_structure.py) reproduces them using temporary copies; [write_edge_audit.py](write_edge_audit.py) persists the human-reviewed sample without generating automatic historical truth scores.
