# ENE local research record

5 November 2026. Read CHARTER.md, METHODS.md and METHODS_ADDENDUM_V2.md before drafting. Ownership limited to contributions/ENE; no subagents or external writes/publication.

## Candidate tests before search

- Production experience versus R&D, factor prices and investment scale.
- Country-level nuclear costs versus site/configuration/institutional differences.
- Technical novelty versus procurement and repeatable fabrication.
- Newer batteries versus older batteries matched to price and use conditions.

## Evidence acquired and inspected

The download attempt is reproducible with acquire.py and its results are retained in cache/download_manifest.json. Nine nonempty full originals were acquired and text-extracted. Five requests were denied/rate-limited or empty; the web parser provided substantive article sections subsequently inspected. No failed download is classified as acquired full text. cache/web-inspections.json retains returned sections and discovery context; source records give locators for actual use.

Inspection included:

- Nemet 2006: scope, early-period residual, customer/standardization changes, Tables 2–3, plant-size/efficiency/silicon arguments and sensitivity.
- Kavlak et al. 2018: cost model, Table 3, attribution definitions and sensitivity, material/yield/scale changes, policy-attribution assumptions.
- De la Tour et al. 2010 HAL v1: demand/production distinction, segment structure, equipment and labour mobility, interview/patent appendices. Preserved as the actual preprint read.
- Lovering et al. 2016: country data provenance, completed-project frame, excluded prototypes, OCC definition, start-date cohorts, Korean discussion and Table 1, limitations.
- Grubler 2012 chapter: coordinated French programme, Table 1, cost trends/definitions and the broad negative-learning claim. The latter is challenged rather than adopted.
- Eash-Gates et al. 2020 manuscript: EEDB account decomposition, indirect cost definitions, allocation assumptions and data section. No new prediction copied from prospective modeling.
- Hoerni patent: specification opening and retained-coating claim. Museum account: prototype/commercial dates and continued failure modes.
- NASA history: Apollo gate-choice rationale and narrow-period purchasing estimate; underlying procurement note not acquired.
- Irwin–Klenow: Dataquest sample, structural assumptions, country/spillover tests, selection sensitivity, adjacent-generation results. No raw-data replication claimed.
- Yoshino: development materials, rejected configurations, comparative impact tests and commercialization date. Forecast passages not used.
- Ziegler et al.: fixed-format/high-energy service definition, 1995–2000 versus 2010–2015 windows, cell/material decomposition, classifications and sensitivity.
- Weinert et al.: survey/plant methodology, product/supplier architecture, regulatory heterogeneity and continued lead-acid. Forecast passages and questionable illustrative outlet-voltage statement not used.
- Cherry et al.: partial inventory boundaries, lead-flow lineage, regional power/mode contrasts, Tables 2/6, battery comparison and health-measurement limit.

## Changes prompted by evidence

- Elevated the Nemet/Kavlak same-period allocation disagreement into an explicit claim instead of averaging estimates.
- Restricted nuclear claims to cohort/accounting contrasts; no aggregate adoption rate, cross-country welfare ranking or universal learning law.
- Separated early planar/Apollo from later DRAM episodes in fields and graph; no chronological transitive causation.
- Treated Li-ion/lead-acid coexistence as direct evidence and liquidity/credit motives as unanswered hypotheses.
- Recorded two source inconsistencies: Korean record/table counts and Chinese PV interview descriptions versus appendix. Avoided precise claims using those inconsistent counts.
- Preserved report_v1.md before local validation/review. Build script materializes all structured records without modifying other contributions.

## Validation boundary

validate.py checks JSON structure and foreign references, v2 fields, graph semantics and report coverage. It cannot prove causal claims, verify historical truth, reconstruct inaccessible source datasets or certify net welfare.
