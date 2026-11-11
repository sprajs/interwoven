# Methods and evidence contract

## Design
This is mechanism-oriented comparative historical research. Selection deliberately includes successes, partial and delayed uptake, reversals, alternatives, coercive adoption and cases where invention did not yield a scalable system. The case library is purposive; case counts cannot estimate the prevalence of a mechanism or a historical success rate. Cross-case recurrence is hypothesis support, not independent causal identification.

The unit of analysis is a specified technology or system, actor population, place and interval. Avoid timeless units such as “printing succeeded” or “VR failed.” A case may contain subepisodes but must state them. Dates are approximate when records warrant it. Modern market claims require a dated measure and denominator.

## Stages
- Invention: documented conception or an artifact; often many claimants and surviving-record bias.
- Feasibility: repeatable operation under stated conditions, not just a demonstration.
- Deployment: operational installation or use by specified adopters.
- Diffusion: changing use across a defined population, region or task; qualitative evidence is labelled.
- Scaling: sustained expansion of output, reach, complementary capacity or affordability.
- Non-adoption/niche: use absent or bounded relative to a stated comparator; absence of surviving evidence is not proof of absence.
- Displacement/reversal: loss of use or replacement, with coexistence and institutional change considered.

## Causal discipline
Start with a contemporary choice set and explicit actor constraints. Separate technical possibility, economic viability, institutional permission, distribution and experienced utility. Identify a pathway, competing explanation and potential falsifier. Prefer within-case sequencing, matched regional/task contrasts, archival records, archaeological analysis, experiments and defensible quasi-experiments where available. State identification limits. Avoid inferring preferences solely from outcomes or institutional capacity solely from eventual success.

## Sources
Prefer original records, official measurements, archaeological or experimental research and scholarly historical analysis. Scholarly historians' own research is primary scholarship; distinguish it from historical primary records. Use museum or institutional syntheses with scope qualifications. A secondary source may generate a lead but must not masquerade as an inspected original. Search snippets alone are weak access and do not establish detailed claims. Record exactly what was read. Do not reproduce long copyrighted passages.

Confidence labels describe support for a bounded statement, not numerical probability: high (direct, appropriate and corroborated evidence), medium (credible but limited/contested/generalised), low (indirect or fragile). Causal status is independent: descriptive, mechanism-supported, causal-identification, contested, or hypothesis. Evidence type: historical-primary, archaeological, scholarly-analysis, official-statistics, experiment, institutional-synthesis, synthesis-inference.

## Structured contributions
Each researcher owns one contributions/<prefix>/ directory and writes:
- report.md: substantial readable investigation, using stable case and claim IDs, inline source links and sections/locators.
- cases.json: array of case records.
- sources.json: array of source records.
- claims.json: array of claim records.
- graph.json: {nodes: [...], edges: [...]}.
- questions.md: blind spots, rival explanations, follow-up searches and important inaccessible sources.

Every record uses a unique prefix (e.g. MAT-C01, MAT-S01, MAT-K01; MAT-T01 for graph nodes; MAT-E01 edges). Sources may duplicate works across contributors; preserve original identifiers and later add canonical aliases rather than silently conflating editions.

Case fields: id, title, region (array), period, domain (array), outcome (array), summary, stages (object keyed by stage), mechanisms (array), counterevidence, claim_ids (array), source_ids (array).
Source fields: id, title, authors, year, url, source_type, access (full-text/partial-text/abstract/metadata/search-excerpt), locator, scope_limit, accessed (YYYY-MM-DD).
Claim fields: id, case_ids (array), statement, evidence_type, confidence, causal_status, sources (array of {source_id, locator, supports}), counterevidence, inference_limits.
Graph node fields: id, label, kind (technology/complement/institution/resource/practice), case_ids.
Graph edge fields: id, from, to, relation (enables/depends-on/complements/competes-with/displaces/constrains), case_ids, claim_ids, source_ids, confidence, qualification. Edge direction is literal: A depends-on B is opposite semantic direction to B enables A. This is a typed multigraph, not a genealogical family tree. All edges are scoped, not universal necessities.

## Review and validation
Review independence is protected through different prompts, explicit disconfirmation tasks and no requirement to endorse the synthesis. Track reviewer findings with severity, response, changed artifact and residual uncertainty. Audit source access and claim entailment, stage conflation, selection/survivor bias, presentism, geographic omissions and causal overreach. Machine checks validate schemas, ID uniqueness, references and local links; they cannot validate historical truth. Source audits are reported with denominators and selection method.
