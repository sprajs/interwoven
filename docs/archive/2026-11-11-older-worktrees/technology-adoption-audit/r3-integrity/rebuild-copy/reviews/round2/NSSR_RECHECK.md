# Independent recheck of the NSSR corrections

5 November 2026. Reviewer: `/root/precision_repair_skills`, the independent ENE/OCE/POL source reviewer. This is a targeted correction check, not a new review of the full strands or final exports.

**NSSR-02 is accepted. NSSR-01's requested status and validation corrections are accepted, with one small residual in the newly written test-design sentence.** The added ENE-K02 reconstructed-input qualification is also accepted. None of these results changes the underlying observed historical patterns.

## Frozen target and checks

The target is [nssr-repair-snapshot/MANIFEST.json](nssr-repair-snapshot/MANIFEST.json), SHA-256 `1b9dcf4c0d19f279e01ce67186be3e1794866e9540f98281989401861b8924fc`. All **5/5 files** match. Each parent-recorded before hash matches the earlier independently reviewed snapshot, and each after hash matches this target. No snapshot or live contribution file was edited.

All five files were diffed against [wave2-source-snapshot](wave2-source-snapshot/MANIFEST.json). The JSON changes are confined to ENE-C01, ENE-K01, ENE-K02 and OCE-K11; no IDs were added or removed. The two report changes concern the corresponding PV and Martu passages. The recheck reopened the cached original Nemet PDF/text, Kavlak PDF/text and Martu HTML/text. It does not claim a new live download or raw-data reanalysis. Source hashes, changed-record inventories and exact dispositions are preserved in [NSSR_RECHECK.json](NSSR_RECHECK.json).

## Dispositions

| Item | Verdict | Basis and boundary |
|---|---|---|
| NSSR-02, ENE-K01 | Accepted | Claim, source support, episode configuration, measurement field and report now distinguish the worldwide module-price reconstruction from partly US market examples. The claim retains its underdetermined test and does not allocate the early residual causally. The report explicitly identifies price as a cost proxy. Nemet's §§1.2–2.1 establish the worldwide data and two survey inputs; §§3.1.1–3.1.4 supply the market context. |
| NSSR-01, OCE-K11 status and validation | Requested corrections accepted; one residual below | The test is now underdetermined; the mechanism is explicitly a hypothesis; nonrandom environment and settlement/track selection remain unresolved. The 90% check is correctly identified as estimated burn age at 50 points within 500 m of a road or track. Proxy regimes, centroid assignment and the single weather station are disclosed. The report also makes clear that separately significant/nonsignificant slopes do not establish a difference. |
| ENE-K02 reconstructed-input addition | Accepted | The new inference limit states that reconstructed inputs and model definitions both change. Nemet's Table 2 uses 125 kW/year for the 1980 plant-size input; Kavlak's account begins at 1 MW in 1980. Their different allocations therefore cannot be attributed to changing the cost equation alone. The claim remains descriptive and the published 43%, 8% and 36% allocations are unchanged. |

The corrected OCE claim's retained statement about weaker rainfall-related expansion is acceptable as a report of the observed fitted associations, read with its explicit qualifications. This acceptance does not establish a causal difference between ignition regimes.

## NSSR-RC-01 — Distinguish a slope test from selection control

**Target:** OCE-K11 `test.discriminating_observation`. **Priority:** P3, narrow methodological wording. **Status:** residual.

The new sentence says that a matched environmental comparison **or** a direct between-regime interaction contrast could separate the fuel-mosaic mechanism from selection. A direct interaction contrast would test whether the fitted rainfall slopes differ. On its own, it cannot distinguish fuel mosaics from environmental selection: different substrates, vegetation or settlement locations could themselves generate different rainfall slopes. The following sentence correctly rejects the inference from separate significance tests, and the remaining-ambiguity field correctly retains confounding, but those qualifications do not make the proposed direct contrast a sufficient selection test.

A concrete repair is:

> A direct between-regime interaction contrast would test whether the rainfall slopes differ. Separating the fuel-mosaic mechanism from environmental selection additionally requires environmental comparability or a defensible causal design.

A matched observational comparison would still depend on measured covariates, overlap and assumptions about unmeasured differences. No new empirical research is required to repair this sentence. The frozen residual should be closed against a separately identified changed record; this report and its target should remain immutable.

## Acceptance boundary

This check covers three claim records, one linked episode's changed fields and two changed report passages within five files. It reopens three original sources for those exact propositions. It does not re-audit the remaining claims, infer new graph support, validate the final JSON/CSV/HTML transport or accept the whole edition. Original graph-edge conclusions remain those of [NEW_STRANDS_SOURCE_REVIEW.md](NEW_STRANDS_SOURCE_REVIEW.md); no graph file is part of this correction snapshot. Final integration must preserve the accepted qualifications and close NSSR-RC-01.
