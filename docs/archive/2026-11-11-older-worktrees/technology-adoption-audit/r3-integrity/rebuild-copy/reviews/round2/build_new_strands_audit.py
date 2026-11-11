"""Record this review's judgments and immutable evidence, without changing research."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAP = HERE / "wave2-source-snapshot"
EVIDENCE = HERE / "new-strands-evidence"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_digest(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def write(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


prereg = read(HERE / "NEW_STRANDS_PREREGISTRATION.json")
all_claims = {}
all_sources = {}
all_edges = {}
all_cases = {}
for strand in ("ENE", "OCE", "POL"):
    base = SNAP / "contributions" / strand
    all_claims.update({v["id"]: v for v in read(base / "claims.json")})
    all_sources.update({v["id"]: v for v in read(base / "sources.json")})
    all_cases.update({v["id"]: v for v in read(base / "cases.json")})
    all_edges.update({v["id"]: v for v in read(base / "graph.json")["edges"]})

source_checks = {
    "ENE-S01": {
        "access_actual": "Complete cached original PDF; independently extracted and relevant pages read, including visual checks.",
        "edition": "Energy Policy 34 (2006), 3218–3232; PDF retains ARTICLE IN PRESS header.",
        "evidence_files": ["ENE-S01.pdf", "ENE-S01.txt"],
        "passages_inspected": ["§§1.2–2.1, printed pp. 3221–3222", "§§3.1–3.2, pp. 3224–3225", "Tables 2–3 and §4.3, pp. 3226–3227"],
        "lineage_independently_observed": "The cost input uses two world PV price surveys (Maycock and Strategies Unlimited). Buyer/quality/concentration examples cite Moore, Christensen, Wohlgemuth, Wolf, Roessner and Maycock; silicon discussion cites Menanteau. Those inherited originals were not separately inspected.",
        "access_or_lineage_discrepancy": "No access overstatement found. Worldwide outcome and US market examples require explicit separation in ENE-K01.",
    },
    "ENE-S02": {
        "access_actual": "Complete cached original PDF; fresh extraction and visual checks of Tables 3 and associated text.",
        "edition": "Energy Policy 123 (2018), 700–710.",
        "evidence_files": ["ENE-S02.pdf", "ENE-S02.txt"],
        "passages_inspected": ["§4.1 and Table 3, pp. 705–706", "§4.2, pp. 706–707", "Table 1 input reconstruction referenced by §4.1"],
        "lineage_independently_observed": "Explicitly compares with and uses Nemet; semiconductor account cites Woditsch/Koch, Sarti/Einhaus, Swanson and Fisher. Shared historical series and method prevent treating the two cost reconstructions as independent policy-effect replications.",
        "access_or_lineage_discrepancy": "No material discrepancy. Input reconstruction changes as well as model structure.",
    },
    "ENE-S11": {
        "access_actual": "Archived original web PDF extraction, six source-labelled segments; fresh RSC HTML/PDF attempts failed 403 and MIT PDF failed 429. No complete local original PDF acquired by this reviewer.",
        "edition": "Published Energy & Environmental Science 14 (2021), 6074–6098, DOI 10.1039/D1EE01313K; archive identifies publisher PDF with June 2026 download footer.",
        "evidence_files": ["ENE-S11-archived-original-extracts.txt", "ENE-S11-acquisition.json", "ENE-S11-repository-discovery.txt", "ENE-S11-download-route.txt", "web-access-initial.txt"],
        "passages_inspected": ["Original extraction lines 353–440: periods, cell definition and cost equation", "lines 1492–1539: representative periods and model-cost comparison", "lines 1730–1751 and 1797–1888: R&D definitions, baseline shares, assignment sensitivity", "lines 1991–2032: chemistry/materials research allocation context"],
        "lineage_independently_observed": "The model assembles historical technical and price estimates; it explicitly follows the previous PV allocation approach. These are not sampled factory accounts or independently identified funding effects. Supplementary assignments and raw data were not re-estimated.",
        "access_or_lineage_discrepancy": "Frozen partial-text designation is accurate. The archive is original tool-extracted source text, not the contributor's summary or self-audit.",
    },
    "OCE-S05": {
        "access_actual": "Complete cached original nomination PDF; new extraction; printed pp. 68–69 visually inspected.",
        "edition": "Budj Bim Cultural Landscape nomination, December 2017; printed pp. 68–70 correspond to PDF pp. 86–88.",
        "evidence_files": ["OCE-S05.pdf", "OCE-S05.txt"],
        "passages_inspected": ["The rebirth of Tae Rak and renewal of water flow, printed pp. 68–70", "Notes 289–295"],
        "lineage_independently_observed": "Drainage account cites Gunditjmara 2010 and Richards 2011; lake-margin operation cites Gunditjmara 2010:65. Restoration note 292 cites the Gunditj Mirring project page. The two selected sources overlap; opposition letters and hydrological studies were not inspected directly.",
        "access_or_lineage_discrepancy": "No material discrepancy. Institutional statements are not an independently reconstructed flow/catch series.",
    },
    "OCE-S06": {
        "access_actual": "Complete cached original community project HTML; independently parsed with the Python HTML parser.",
        "edition": "Undated Lake Condah Restoration Project page cached on the contribution's acquisition date; publication date is not invented.",
        "evidence_files": ["OCE-S06.html", "OCE-S06.txt"],
        "passages_inspected": ["Opening history paragraphs, extracted lines 33–46: 1946 floods, 1954 completion, unsuccessful trial, plans, studies and construction"],
        "lineage_independently_observed": "Community project's institutional retrospective, partly reused by the nomination. A distinct source file is not an independent observation of the same historical events.",
        "access_or_lineage_discrepancy": "No material discrepancy.",
    },
    "OCE-S08": {
        "access_actual": "Complete cached original PMC HTML of the research paper; independent extraction, full relevant Results and Materials and Methods read.",
        "edition": "PNAS 109(26), 10287–10292 (2012), DOI 10.1073/pnas.1204585109; PMCID PMC3387077.",
        "evidence_files": ["OCE-S08.html", "OCE-S08.txt"],
        "passages_inspected": ["Introduction and Results, extracted lines 174–272", "Rainfall coefficients, lines 430–462", "Customary rights and public goods, lines 588–598", "Burn-age map, regime definition, sample and rainfall source, lines 600–615"],
        "lineage_independently_observed": "Original remote imagery, ethnography and climatic analysis within an overlapping Martu research programme; foraging claims cite earlier programme publications. Field notes and imagery were not re-coded. The 90% check validates burn ages, not ignition identity.",
        "access_or_lineage_discrepancy": "No source-access discrepancy. OCE-K11's validation summary needs its precise object; realistic environmental-selection rival remains unresolved.",
    },
    "POL-S04": {
        "access_actual": "Complete cached accepted-manuscript PDF; original pp. 26–28 and Figure 6 read and visually checked. Publisher's corrected Figure 6 discussion and note 45 were additionally reopened online.",
        "edition": "Accepted manuscript hosted by Hoover, contrasted explicitly with Wiley's published text carrying 7 March 2024 correction. No silent edition substitution.",
        "evidence_files": ["POL-S04.pdf", "POL-S04.txt", "POL-S04-published-version-comparison.txt", "POL-S04-replication-access.txt", "POL-S04-rate-reconciliation-search.txt"],
        "passages_inspected": ["Price indexes, manuscript pp. 26–28, Figure 6 and notes 44–45", "Publisher Figure 6 discussion and correction notice, saved lines 259–265 and 711–712", "Manuscript replication-package link, p. 60"],
        "lineage_independently_observed": "Price observations are inherited from Li pp. 12–71, interpolated/extrapolated into weighted baskets by Guan/Palma/Wu. Multiple indexes share those observations. No new transcription of Yuan records or reconstruction of the CPI was performed.",
        "access_or_lineage_discrepancy": "The manuscript contains a doubling-interval typo corrected by the publisher. The selected frozen claim does not repeat it. Data landing page exposed only a loading screen; direct fetch returned 403, so no replication is claimed.",
    },
    "POL-S07": {
        "access_actual": "Complete cached original accepted-manuscript PDF; new extraction; Tables 1 and 3 visually checked.",
        "edition": "AEA-hosted accepted manuscript, title and authors match frozen source; untypeset page headers retained.",
        "evidence_files": ["POL-S07.pdf", "POL-S07.txt"],
        "passages_inspected": ["Data and treatment construction, pp. 10–14", "DID and event study, pp. 15–18", "Selection, spillover and network checks, pp. 18–22", "Tables 1 and 3, pp. 39 and 41", "Trading context, pp. 9–10"],
        "lineage_independently_observed": "Qing official grain-price reporting compiled by Wang; telegraph map, histories and gazetteers; inherited weather compendium. The institutional discussion cites Yoon, including line-cost claims. No microdata re-estimation, reporting-register audit or modern staggered-DID replication was conducted.",
        "access_or_lineage_discrepancy": "No material discrepancy. 47,436 observed prefecture-months differ from the theoretical 130×420 frame; the frozen claim does not state that the panel is complete.",
    },
    "POL-S08": {
        "access_actual": "Live publisher abstract and visible footnotes/references; no body text.",
        "edition": "Modern Asian Studies 49(3), 832–857 (2015); online 23 October 2013, DOI 10.1017/S0026749X13000309.",
        "evidence_files": ["web-access-initial.txt"],
        "passages_inspected": ["Publisher abstract, saved lines 450–453", "Thesis-origin note and reference 6, lines 475–502"],
        "lineage_independently_observed": "Developed from Yoon's 2008 thesis. Reference 6 identifies Zongli Yamen, Youchuanbu and Grand Council archives. Those records were not inspected; Gao/Lei draws on Yoon for historical background.",
        "access_or_lineage_discrepancy": "Frozen abstract-only and low-confidence hypothesis labels accurately reflect what can be verified.",
    },
}

findings = [
    {
        "id": "NSSR-01", "severity": "moderate", "required": True,
        "claim_id": "OCE-K11",
        "target_fields": ["test.status", "test.evidence_sought_found", "test.discriminating_observation"],
        "finding": "An evaluated test is asserted against a realistic environmental-selection rival which remains compatible with the observed proxy-regime comparison. The stated 90% validation omits that only estimated burn age, not ignition source, was checked.",
        "evidence": ["OCE-S08 Results rainfall coefficients", "OCE-S08 Materials and Methods: proximity classes, centroid attribution, one climate station, accessible 50-point burn-age check"],
        "repair": "Set the mechanism test against that rival to underdetermined, and specify burn-age mapping at 50 points within 500 m of a road/track. Keep the observed pattern. An evaluated narrower climate-only test may instead be separately scoped while the environmental-selection rival remains unresolved.",
        "affected_edge_ids": ["OCE-E10", "OCE-E12"],
        "edge_disposition": "No required edge mutation: current scoped contribution and confounding qualifications are compatible with the repaired claim; do not promote them to necessity or unqualified identified effect.",
        "acceptance_check": "Read revised canonical OCE-K11 plus linked prose/edges. Confirm precise burn-age wording and that status no longer implies selection-rival discrimination.",
    },
    {
        "id": "NSSR-02", "severity": "low", "required": True,
        "claim_id": "ENE-K01",
        "target_fields": ["statement", "test.evidence_sought_found", "linked episode measurement scope if changed"],
        "finding": "The statement's US label blends US market examples with Nemet's explicitly worldwide price outcome.",
        "evidence": ["ENE-S01 §§1.2–2.1: worldwide data and two world price surveys", "ENE-S01 §§3.1.1–3.1.4: US buyer, concentration and standardization examples"],
        "repair": "Explicitly distinguish worldwide PV cost/price reconstruction from the partly US market evidence used to interpret it. Retain underdetermined causal allocation and the limit on the early residual.",
        "affected_edge_ids": [],
        "edge_disposition": "No graph edge cites ENE-K01 in the frozen target.",
        "acceptance_check": "Verify revised canonical claim and any linked case/report phrasing preserve worldwide price geography and bounded US examples.",
    },
]

claim_notes = {
    "ENE-K02": {
        "verdict": "supported-as-scoped",
        "passage_entailment": "The 43%, 8% and 36% entries and bounded semiconductor supply/process history match the cited tables and discussion.",
        "population_and_measure": "Worldwide crystalline-silicon module cost reconstructions, matching 1980–2001 and distinct 2001–2012 intervals; shares of modeled cost change, not adopter shares or installed electricity cost.",
        "rival_and_diagnosticity": "Different model structures and reconstructed inputs jointly explain why allocations can differ; no controlled decomposition isolates equation change alone. The claim is descriptive rather than a policy-effect estimate.",
        "remaining_limit": "Neither model was re-estimated; original industry inputs and upstream semiconductor records remain inherited. Advisory: say model-and-input sensitivity.",
        "finding_ids": [],
    },
    "ENE-K15": {
        "verdict": "supported-with-disclosed-partial-access",
        "passage_entailment": "Archived original passages explicitly contain the baseline shares, inclusion of pilot/nonroutine work in R&D and the reported alternative-assignment exercise.",
        "population_and_measure": "Representative high-energy 18650 cells for 1995–2000 versus 2010–2015; modeled cost per Wh. Neither packs nor all battery services nor workers' contribution shares.",
        "rival_and_diagnosticity": "Intertwined process research and routine manufacturing remain a credible classification rival. The observed sensitivity test changes selected material-price/hardware assignments, not every plausible process classification. Underdetermined is appropriate.",
        "remaining_limit": "No full PDF acquired in this review and no supplement/model replication. Public/private R&D policy effects cannot be inferred.",
        "finding_ids": [],
    },
    "ENE-K01": {
        "verdict": "supported-after-population-clarification",
        "passage_entailment": "The reported market and product changes match; the dependent price/cost series is worldwide rather than exclusively US.",
        "population_and_measure": "US evidence about market structure is interpreted alongside worldwide module prices. The frozen wording needs to keep those populations distinct.",
        "rival_and_diagnosticity": "Manufacturing learning, changing quality, margins and standardization can operate together. Residual engineering-model error alone cannot allocate their contributions. The frozen underdetermined status is retained.",
        "remaining_limit": "The wider real rival is a joint account, not simply zero market change. No matched unchanged-product counterfactual was reconstructed.",
        "finding_ids": ["NSSR-02"],
    },
    "OCE-K06": {
        "verdict": "supported-as-scoped",
        "passage_entailment": "The nomination supports opposition, rapid water recession and flood-limited trap function; the community project text gives 1954 completion.",
        "population_and_measure": "Tae Rak lake-margin structures and their operating water conditions, not all fishing by all Gunditjmara and not a measured catch or employment effect.",
        "rival_and_diagnosticity": "Independent livelihood or preference change cannot alone explain observed loss of hydraulic opportunity and documented objections. It can still affect labor/catches. The bounded disabling claim is supported without identifying all outcomes.",
        "remaining_limit": "Shared project/heritage lineage, no original opposition letters, independent flow records or catch time series. Grazing beneficiaries are not evaluated.",
        "finding_ids": [],
    },
    "OCE-K11": {
        "verdict": "observations-supported-test-calibration-required",
        "passage_entailment": "Fire-size, clustering and reported rainfall relations match. The ground check is burn-age classification, and no environmental-selection exclusion is established.",
        "population_and_measure": "1999–2010 spinifex region; proxied Aboriginal and lightning regimes cover approximately 10% and 50% of the area, leaving mixed/unclassified areas outside that comparison. Fire centroids determine assigned regime.",
        "rival_and_diagnosticity": "Track/community siting and environmental heterogeneity can affect both exposure classification and fire behavior. Broad vegetation similarity and a shared rainfall record do not eliminate that rival. Separate significant/nonsignificant coefficients do not test a between-slope difference.",
        "remaining_limit": "No imagery reclassification, spatial-control reanalysis or independent ignition census; no direct mammal population or welfare outcomes.",
        "finding_ids": ["NSSR-01"],
    },
    "OCE-K20": {
        "verdict": "supported-as-scoped",
        "passage_entailment": "The published ethnographic description includes restricted burning rights, possible retribution and social rewards for caring for Country.",
        "population_and_measure": "Contemporary observed Martu context; an account of norms and meanings rather than a census of adherence or sanctions.",
        "rival_and_diagnosticity": "Descriptive correction to an institution-free reading. It does not assign a causal weight between immediate hunting returns, obligations and reputation; those motives may coexist.",
        "remaining_limit": "No quantified independent enforcement dataset or individual longitudinal motivation study. Same paper as K11 is not independent corroboration.",
        "finding_ids": [],
    },
    "POL-K11": {
        "verdict": "attribution-supported-causal-account-underdetermined",
        "passage_entailment": "The complete publisher abstract advances the stated dividend, investment, tariff and limited-use account.",
        "population_and_measure": "Late-Qing Telegraph Administration as interpreted by Yoon; abstract supplies neither a customer denominator nor tariff elasticity or investment series.",
        "rival_and_diagnosticity": "Capital scarcity, technical difficulty and low demand could also produce high tariffs and restrained investment. Frozen low-confidence hypothesis and underdetermined test correctly preserve this.",
        "remaining_limit": "No body text or underlying administrative records audited. Price effects among traders do not refute restricted mass direct usage.",
        "finding_ids": [],
    },
    "POL-K13": {
        "verdict": "reported-estimate-and-conditional-design-supported",
        "passage_entailment": "Table 3 high-quality-rice coefficients divided by Table 1 mean reproduce the reported range; data and methods establish the stated outcome and frame.",
        "population_and_measure": "47,436 observed prefecture-months in 130 prefectures/nine provinces over a 420-month frame, 1870–1904; monthly reported wholesale maxima, not consumer means or national welfare.",
        "rival_and_diagnosticity": "Pretrends, fixed effects/trends, transport/port controls, selected-location exclusions and network predictions test concrete alternatives. Unmeasured concurrent changes, reporting response, timing and staggered-treatment assumptions remain. The label is conditional source-design evidence, not randomized or replicated proof.",
        "remaining_limit": "No original regressions, microdata or staggered-DID re-estimation. Shared institutional narrative with Yoon does not turn two papers into independent tests of dividend causality.",
        "finding_ids": [],
    },
    "POL-K06": {
        "verdict": "reported-estimate-supported-no-independent-reconstruction",
        "passage_entailment": "Both inspected editions report 11.0%, 1.8% and 4.5% for the stated intervals, and explain sparse observations and interpolation. Publisher confirms a separate interval typo correction absent from the frozen claim.",
        "population_and_measure": "A reconstructed seven-product respectability index from inherited market-price observations; rates are not a continuous national price census or household-specific cost-of-living series.",
        "rival_and_diagnosticity": "Uneven preservation, basket weights and interpolated prices can affect rate magnitudes. This is a descriptive attributed reconstruction, not an identified causal account of currency change.",
        "remaining_limit": "No underlying Li data or CPI replication. The source's corrected doubling interval is documented rather than silently importing another edition.",
        "finding_ids": [],
    },
}

edge_notes = {
    "ENE-E01": "Published histories support bounded semiconductor supply/process contribution; inherited documentation, not proof of timeless necessity or a measured policy effect.",
    "ENE-E16": "The source model supports the scoped density/material contribution to cost per Wh; qualification preserves model status and avoids a causal funding claim.",
    "OCE-E05": "Hydrological constraint on retained water is supported by source account; no independently estimated flow/catch effect.",
    "OCE-E06": "Technical possibility at specified elevations is appropriate; available water does not establish actual operation or yield.",
    "OCE-E10": "Burning contributes to local fuel-age patterns as a scoped observational proposition; comparative causal magnitude remains confounded. NSSR-01 must not be erased on export.",
    "OCE-E12": "Source directly discusses tracks and vehicle-mediated contemporary access; edge keeps walking alternatives and denies a historical vehicle prerequisite.",
    "OCE-E19": "Published rights/retribution description supports a scoped constraint; no quantitative enforcement effect is asserted.",
    "POL-E08": "Shareholder interests in the inspected abstract support the narrow finance/governance presence. Low confidence and abstract-only qualification are required; POL-S09 body was not independently audited.",
    "POL-E09": "Hypothesis basis correctly preserves the financing mechanism's unresolved capital/demand rival.",
    "POL-E10": "Gao/Lei trading context supports slower letters/messengers as alternatives; no complete displacement or comparative volume is established.",
    "POL-E11": "Existing trade/waterway mechanism is supportable as a bounded complement. Price evidence is indirect regarding all physical trade flows and household welfare.",
}

claim_audits = []
for strand, selection in prereg["strands"].items():
    for cid in selection["selected"]:
        claim = all_claims[cid]
        claim_audits.append({
            "claim_id": cid,
            "selection": "ordinary-hash" if cid == selection["ordinary_selected"] else "purposive",
            "frozen_record_sha256": record_digest(claim),
            "source_ids": [v["source_id"] for v in claim["sources"]],
            "case_ids": claim["case_ids"],
            "incident_edge_ids": [eid for eid, edge in all_edges.items() if cid in edge["claim_ids"]],
            **claim_notes[cid],
        })

edge_audits = [{
    "edge_id": eid,
    "frozen_record_sha256": record_digest(all_edges[eid]),
    "basis": all_edges[eid]["basis"],
    "verdict": "retain-current-bounded-proposition",
    "assessment": note,
    "source_audit_limit": "Only the selected-claim proposition is checked. Other cited claims/sources are not automatically accepted.",
} for eid, note in edge_notes.items()]

for sid, detail in source_checks.items():
    detail["source_id"] = sid
    detail["url"] = all_sources[sid]["url"]
    detail["frozen_source_record_sha256"] = record_digest(all_sources[sid])
    detail["evidence_file_hashes"] = {name: digest(EVIDENCE / name) for name in detail["evidence_files"]}

audit = {
    "schema_version": 1,
    "review_id": "NEW_STRANDS_R2_SOURCE_REVIEW",
    "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "reviewer": "/root/precision_repair_skills",
    "independence": "Authored SKL only; no authorship of ENE/OCE/POL. Contributor self-audits are not acceptance evidence. No subagents used.",
    "target": {
        "manifest": "wave2-source-snapshot/MANIFEST.json",
        "manifest_sha256": digest(SNAP / "MANIFEST.json"),
        "manifest_files": 27,
        "target_is_frozen": True,
        "live_research_edited": False,
    },
    "registration": {"path": "NEW_STRANDS_PREREGISTRATION.json", "sha256": digest(HERE / "NEW_STRANDS_PREREGISTRATION.json")},
    "denominators": {
        "reports_read": 3, "reports_in_target": 3,
        "claims_audited": 9, "claims_in_target": len(all_claims),
        "purposive_claims": 6, "ordinary_hash_claims": 3,
        "source_records_reopened": len(source_checks), "source_records_in_target": len(all_sources),
        "source_records_complete_original_available": 7,
        "source_records_archived_partial_original": 1,
        "source_records_abstract_only": 1,
        "additional_edition_checks_not_additional_sources": 1,
        "episode_records_checked": 6, "case_records_in_target": len(all_cases),
        "incident_edges_audited": len(edge_audits), "edges_in_target": len(all_edges),
        "interpretation": "Purposive audit plus three deterministic ordinary checks. No general error rate or acceptance of unaudited records follows.",
    },
    "overall_verdict": "Seven selected claims retainable within limits; two require narrow revisions. No selected numerical transcription error found. All eleven audited incident propositions retainable with their existing scope; no whole-programme or final-synthesis acceptance.",
    "findings": findings,
    "claim_audits": claim_audits,
    "source_inspections": list(source_checks.values()),
    "edge_audits": edge_audits,
    "advisories": [
        {"id": "NSSR-A01", "target": "ENE-K02/report", "required": False, "text": "Model sensitivity also includes changed historical input reconstructions. Nemet's 1980 plant size is 125 kW/year; Kavlak's is 1 MW/year. Do not infer that changing the equation alone caused the allocation difference."},
        {"id": "NSSR-A02", "target": "ENE-K15", "required": False, "text": "Keep the sensitivity exercise bounded to the active-material price and hardware assignments actually tested; it is not unrestricted reassignment of all process work."},
        {"id": "NSSR-A03", "target": "POL-S04", "required": False, "text": "Add the known publisher correction to the source ledger if useful; preserve accepted-versus-published edition distinction. The selected claim's numbers are unchanged in both editions."},
        {"id": "NSSR-A04", "target": "POL-K13/episode denominator", "required": False, "text": "For precise future reproduction, record 47,436 observed prefecture-months within the 130×420 frame. Current phrasing does not claim a complete panel."},
    ],
    "rejected_candidate_findings": [
        {
            "target": "POL-K06", "candidate": "Accepted manuscript's doubling interval conflicts with Figure 6, so the frozen inflation claim may be wrong.",
            "resolution": "Publisher explicitly corrected the separate interval from 1260–1355 to 1346–1355 on 7 March 2024. The frozen claim excludes that sentence; its three attributed rates appear unchanged in the corrected published version. Do not report a transcription error or fabricate corrected rates from a plotted line.",
            "evidence": "POL-S04-published-version-comparison.txt",
        }
    ],
    "limits": [
        "Original technical inputs, archival letters, raw imagery/field observations and econometric microdata were not independently reconstructed.",
        "Full-text file availability is distinct from complete text audit; only listed passages were inspected.",
        "ENE-S11 conclusions depend on original archived partial source extracts after fresh download failures; POL-S08 remains abstract-only.",
        "Multiple records or papers sharing the same evidence are not independent corroboration.",
        "No prevalence, national representativeness, livelihood-transition or welfare inference follows from the selected cases.",
        "Future synthesis/export changes require version comparison and verification; this review addresses only the frozen manifest.",
    ],
}

write(HERE / "NEW_STRANDS_SOURCE_AUDIT.json", audit)

provenance = read(HERE / "NEW_STRANDS_SOURCE_PROVENANCE.json")
provenance["finalized_utc"] = audit["completed_utc"]
provenance["source_records"] = [{k: v for k, v in s.items() if k not in ("lineage_independently_observed", "access_or_lineage_discrepancy")} for s in source_checks.values()]
provenance["archived_original_extraction"] = {
    "upstream_file": "contributions/ENE/cache/web-inspections.json",
    "upstream_sha256": "f1c1ad79a07a39acffbe3867bad8f068ad7e3ba2b418261cc6a712311a2bcda7",
    "selection_rule": "Recursively enumerate string values; split at ten or more hyphens; retain segments whose first 1800 characters include d1ee01313k case-insensitively. Preserve response key, source header and original line numbers.",
    "output": "new-strands-evidence/ENE-S11-archived-original-extracts.txt",
    "output_sha256": digest(EVIDENCE / "ENE-S11-archived-original-extracts.txt"),
    "segments": 6,
    "not_author_summary": True,
}
provenance["numerical_check"] = {
    "description": "Recompute displayed percentage magnitudes from Gao/Lei Tables 1 and 3; not a regression replication.",
    "high_quality_mean": 217.244,
    "coefficients": [-9.216, -11.390, -11.950],
    "percentage_magnitudes": [100 * x / 217.244 for x in (9.216, 11.390, 11.950)],
    "observations": 47436,
    "frame_prefecture_months": 130 * 420,
}
provenance["rendering"] = {
    "tool": "pdftoppm; maximum dimension 1800; PNG, one source page each",
    "visually_inspected_pages": {
        "ENE-S01": [7, 8, 10], "ENE-S02": [7, 8], "OCE-S05": [86, 87],
        "POL-S04": [27, 28], "POL-S07": [39, 41],
    },
    "purpose": "Check original source table labels, page locations and surrounding qualifications, not the research site's visual design.",
}
provenance["evidence_file_manifest"] = {
    str(p.relative_to(HERE)): {"sha256": digest(p), "bytes": p.stat().st_size}
    for p in sorted(EVIDENCE.rglob("*")) if p.is_file()
}
write(HERE / "NEW_STRANDS_SOURCE_PROVENANCE.json", provenance)

print(json.dumps({"claims": len(claim_audits), "sources": len(source_checks), "edges": len(edge_audits), "required_findings": len(findings), "audit": str(HERE / "NEW_STRANDS_SOURCE_AUDIT.json")}, indent=2))
