# Independent SKL/PSY source review — round 2

**Verdict: three bounded repairs are required before acceptance.** The eight sampled claim statements are supported by the inspected passages at their stated scope; no sampled numerical transcription error was found. The remaining issues concern an unsupported population exclusion, an unresolved publication-version difference, and a mechanism-test label. These findings do not overturn the randomised effects on the recorded Zambia outcomes.

Reviewer: `/root/review1_sources`, independent of both contribution authors, using the inherited Astra model. Reviewed target: the 20 files frozen at `skills-behaviour-snapshot/MANIFEST.json`, captured 5 November 2026 at 15:22:29 UTC. Manifest SHA-256: `430e5e198be4545239452e43ee18ff36d3f21c2aff4f7f75fa65a6cd50d48081`. All hashes matched before and after inspection. Neither live contributions nor the frozen snapshot was edited.

## Denominator and selection

The two strands contain **11 cases, 38 claims, 26 source records and 33 edges**. This audit reopened originals for **8 claims and their 9 distinct source records**, with case/population context for six cases. Three consequential or limited-access claims per strand were selected purposively; one additional descriptive claim per strand was selected by the preregistered SHA-256 rule. Selection was frozen before reopening originals in `SKILLS_BEHAVIOUR_PREREGISTRATION.json`, and the ordinary selection reproduces as SKL-K07 and PSY-K04. This is a risk-oriented sample, not an estimated error rate for the whole collection.

Five original PDFs were independently inspected from preserved author caches after matching hashes, with fresh text extraction and visual checks of nine relevant pages. Two institutional web pages were reopened in full; Collins and Harrison (1975) was accessible only through publisher-displayed footnotes; the final Zambia article was available only as publisher abstract/metadata. Direct Oxford access failed; the complete abstract was returned through the search service's primary Oxford record. No final article tables, participant-level dataset, archival original behind the NPS synthesis, or interview recordings were acquired.

Eight directly linked edges received source/scope checks: SKL-E07/E08/E10/E19 and PSY-E01/E12/E13/E14. SKL-E16/E17/E18 were examined only for shared-node scope context, not counted as reopened-source audits. Author self-audits and structural validation are not independent factual acceptance.

## Required repairs

### SB01 — Distinguish unknown representation from exclusion by design

**Medium; PSY report line 79 and PSY-E14 dispute, graph line 614.** The report says girls unable to cycle and people without usable routes were excluded by design; the edge says disabled girls are not represented. The inspected sampling passages specify school enrolment, grade and distance, with urban and some very remote schools excluded. They do not establish a cycling-ability or disability exclusion rule. See [May 2025 manuscript](https://www.nishithprakash.com/s/Wheels_of_Change.pdf), §3.3 and Appendix B, printed pp.9,74–75 (PDF pages 10,75–76).

Retain documented exclusion of girls outside the enrolled target population. Replace the stronger disability/cycling assertions with uncertainty: disability and cycling-ability representation, outcomes for girls unable to use a standard bicycle, and route accessibility were not established in the inspected evidence. A plausible applicability limit must not become an invented eligibility criterion. PSY-K18's warning that the experiment does not prove all girls can use bicycles is already sound; its effect estimates need no change.

### SB02 — Make the known aspirations version difference explicit

**Medium; PSY-K20, PSY-S14 scope/lineage, report line 75 and PSY-C05 counterevidence.** The May manuscript's pooled aspirations estimate is imprecise: Table 3 reports 0.07 (SE 0.05); Table A.11 reports 0.06 with corrected p-values .44/.50. The [final Oxford abstract](https://academic.oup.com/ej/article-abstract/136/679/2531/8317231) instead states that educational aspirations improved. This is a known difference in wording, not merely an unspecified future full-text check.

Keep the table-based result explicitly attributed to the 7 May 2025 manuscript, record the final abstract's different assertion, and leave reconciliation open until the final tables, outcome definitions and pooled/arm-specific estimates can be checked. Do not infer that the published pooled estimate changed, or replace it with an abstract-based positive effect. The abstract is a later version of the same trial, not independent corroboration. Its commute/absence rounding agrees with the manuscript tables.

### SB03 — Separate a treatment effect on survey answers from a discriminated agency mechanism

**Medium; PSY-K20 test, claims lines 547–554.** The `evaluated` label is attached to a test whose strongest rival is demand, asset salience or family reallocation changing responses without broader norm change. Pre/post questionnaire measurement and multiplicity corrections do not distinguish that rival; the manuscript records that behavioural games were discontinued (§4.4.3, printed p.16). The frozen record itself acknowledges that the intervening mechanism remains unresolved.

Set this mechanism test to `underdetermined`, or split an evaluated test of the package's effects on reported indices from an underdetermined explanation for those effects. Retain `causal-identification` for the bounded randomised effect on measured answers if desired; this finding does not imply that self-report outcomes are intrinsically invalid. It enforces METHODS_ADDENDUM_V2's rule that shared predictions do not discriminate mechanisms. No graph edge currently asserts a separate norm-change effect, so no causal edge needs to be deleted.

## Sampled entailment results

| Claim | Result and consequential boundary |
|---|---|
| SKL-K07, ordinary | Supported. NPS dates patent, contract and testimony separately. S06 p.55 confirms prior piecework/55 occupations. Managerial testimony is not a worker-income or full-cost estimate. |
| SKL-K08 | Supported. S06 p.59 explicitly describes checking working gauges against a separate set; figure 19 and S12 share HAFE 7427. The later ca.1846 Model 1841 object cannot independently prove 1823 practice, output conformity or Hall's rifle-work system. The frozen record preserves this distinction. |
| SKL-K11 | Supported. Grace p.120 and notes 141–142 tie tools to particular work options and narrate Katigiro's 1967–1972 expansion. Business growth precedes later investment in the narrative. Demand, skill and reputation remain entangled with tools; no cohort or asset-effect estimate is claimed. |
| SKL-K18 | Supported within partial access. Publisher footnotes 2,8,10–11 disclose simultaneous changes, teaching demands, repeated power-unit failures and unconsulted written advice. They support competing explanations for delays, not a reconstructed full chronology or a measured causal share. |
| PSY-K03 | Supported. The AER article reports positive but imprecise late-delivery effects, p=.08 for the timing contrast, and timing-choice model misfit. Announced-delay pilots measure purchases, not subsequent use. Present bias remains one explanation. |
| PSY-K04, ordinary | Supported. QJE Table II reports 86%/87% unable to answer pod-size questions among 489 growers; observed practices and baseline timing are separately documented. The wording does not turn measurement-language limits into a universal cognitive deficit. |
| PSY-K18 | Supported. Tables 1/4 use minutes each way and days absent in the previous week, with N=1,879/1,952. Recalculation yields 33.8055% and 28.7129%, matching final 34%/29% rounding. The randomised object is the installed package for eligible enrolled girls; survey attrition and reporting limits remain. SB01 affects surrounding population wording. |
| PSY-K20 | Supported as a May-manuscript result, with SB02/SB03 repairs. Main and controlled-appendix coefficients/corrections match. Reported agency is measured independently of attendance, but no distinct norm mechanism, unrestricted autonomy or later livelihood effect follows. |

## Graph and evidence lineage

The checked graph relationships generally preserve the source boundaries: separate Hall rifle works and main-armory metrology; conditional tool access and independent work; SAFI's seasonal offer without a unique present-bias channel; Zambia's repair support and custody rules without independent component effects. PSY-E14 needs SB01's wording repair.

One non-blocking integration caution remains: SKL-E19's 1975 follow-up shares generic outcome node SKL-T23 with the earlier network and alternative-electrode episodes. Edge scopes distinguish them and there is no outgoing chain or necessity claim. Prefer a separate follow-up node before presenting a combined causal path; do not read all incoming links as one observed build configuration. The three older-network edges were not source-audited here.

Lineage is adequately disclosed in the sampled records. The NPS history and Hall page inherit overlapping Smith-family scholarship; the museum record is the same gauge set as the report illustration. Grace's historical interviews and participant observations belong to one research programme. Collins's follow-up is not an independent general theory test. The Zambia manuscript and article abstract share one trial. SAFI's related agronomic work and pilots must not be counted as unrelated replications.

## Acceptance boundary

After SB01–SB03 are repaired and changed bytes reconciled to the final generation, the inspected statements can be accepted at the scopes above. Unselected claims remain outside this audit. The first-round source audit is separate and was not repeated. The audit JSON, provenance, preregistration, evidence hashes and validator preserve the exact target and inspection limits; no raw-data replication or final Zambia full-text audit is claimed.
