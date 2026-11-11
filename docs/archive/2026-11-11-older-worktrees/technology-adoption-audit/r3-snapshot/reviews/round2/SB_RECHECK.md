# Independent SB repair recheck

**Accepted within this bounded recheck: SB01, SB02 and SB03 are closed; the SKL node-scope advisory is addressed.** There are no outstanding required repairs from this review. This verdict does not resolve the remaining scientific uncertainties or accept unreviewed claims and final exports.

Reviewer: `/root/review1_sources`, independent of the SKL/PSY contribution authors and repair implementers, using the inherited Astra model. Date: 5 November 2026. No live research or snapshot files were changed during recheck.

The exact target is the eight files in [sb-repair-snapshot/MANIFEST.json](sb-repair-snapshot/MANIFEST.json), captured at 15:50:36 UTC. Manifest SHA-256: `0292161a2ccb4ce26b255632e19b3d11d6c9b0d316b92aec2c0d6d294e899e1c`. All eight hashes match. All seven PSY files also match the author's stable handoff manifest. Comparisons use the original frozen audit target, not changing live files. The original [eight-claim source audit](SKILLS_BEHAVIOUR_SOURCE_REVIEW.md) supplies the evidence base; it was not repeated or expanded into a full strand audit.

## Dispositions

| Finding | Independent recheck | Verdict |
|---|---|---|
| SB01: unsupported exclusion rules | PSY report, C05, E14, S11, X05 and questions distinguish documented enrolment/grade/distance and school-sampling restrictions from unknown disability, cycling-ability and route representation. The revised wording agrees with manuscript §3.3 and Appendix B, printed pp.9,74–75. It neither invents an exclusion criterion nor asserts universal representation. | Closed |
| SB02: abstract/table interpretation | K20, S11/S14, C05, report and questions explicitly preserve the May manuscript's imprecise pooled aspirations estimates and the final abstract's positive assertion. The main 0.07 (SE 0.05) and appendix 0.06, corrected p=.44/.50, remain correctly attributed. No changed final estimate or positive pooled effect is inferred. | Closed as a disclosure repair; substantive reconciliation remains open |
| SB03: mechanism discrimination | K20's mechanism test is now `underdetermined`; its evidence and proposed discriminator address demand/salience rather than treating pre/post questionnaires or multiplicity corrections as sufficient. `causal-identification` remains confined to randomised effects on recorded indices. Discontinued behavioural games supply no confirmation. | Closed |
| SB-A01: TEA outcome identity | E19 now targets T28, a separate 1975 follow-up build with explicitly partial chronology. E17 and E18 target distinct T29/T30 outcomes, while E16 retains T23 for the earlier network. Existing sources, scope, qualifications and all other edge fields are unchanged. | Addressed |

The manuscript's own opening abstract already uses positive aspirations wording. Therefore the unresolved issue is **abstract versus pooled-table interpretation**, not established evidence that the result changed at publication. The repaired source record and questions explicitly recognise this. Acceptance of SB02 means the difference is visible and appropriately limited, not that inaccessible final tables have been reconciled.

The SKL change adds exactly three nodes and changes only the three named edge destinations. Old nodes and the other sixteen edges are unchanged; the three changed edges retain every field except `to`. The new outcome nodes have no outgoing edges. T30 is explicitly a collection of distinct reported rough-electrode alternatives, not one common experimental configuration. This structural repair preserves the existing propositions and prevents treating the 1975 episode as the earlier network's outcome. It supplies no new historical verification of S10 or causal claim about the two rough alternatives.

## Verification and residual scope

Independent checks confirmed that only PSY-C05, K20, S11/S14, E14 and X05 changed among structured PSY records; E14 changes only its dispute wording. The remaining nineteen claim records, including K18's commute/absence estimates, are unchanged. Manuscript and retained primary-page evidence hashes still match the original review. Text differences were inspected directly; author validation was treated as provenance, not as independent acceptance. [SB_RECHECK_VALIDATE.py](SB_RECHECK_VALIDATE.py) reproduces the byte, record and graph invariants; [SB_RECHECK_CHECKS.json](SB_RECHECK_CHECKS.json) stores its result.

Remaining limitations are substantive rather than repair failures: final Zambia article tables and appendix remain uninspected; no distinct agency/norm mechanism or independent bicycle-component effect is identified; disability/cycling/route applicability remains uncertain; Collins and Harrison (1975) remains footnote-only access. No participant-level reanalysis or new source audit of the earlier TEA network was performed.

This verdict attaches only to the eight frozen files and the repairs above. Final compilation/export parity and whole-synthesis interpretation require their separate checks; the prior 8/38-claim audit denominator is unchanged.
