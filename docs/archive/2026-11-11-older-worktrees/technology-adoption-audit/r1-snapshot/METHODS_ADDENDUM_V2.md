# Contribution contract v2 — design-review repairs

Effective 5 November 2026, before integrated synthesis. This addendum extends METHODS.md in response to external design review D01–D06, preserved at reviews/external-design/DESIGN_REVIEW.md. Unknowns with reasons are legitimate; do not fabricate precision to fill fields. Parent owns integration, comparison coverage and occupational-transition synthesis. Researchers own migrations in their assigned directories.

## Cases: episode, actor and labour evidence (D01, D06)

Add three required objects to each case:

```
"episode": {
  "technology_configuration": "bounded system/configuration under study",
  "task": "contemporary task or purpose, possibly contested",
  "population": "whose adoption/use/outcomes are observed; unknown with reason allowed",
  "interval": "episode interval, approximate where needed",
  "contemporary_alternatives": ["named alternatives; distinguish unavailable from rejected"],
  "adoption_measure": "actual measure or qualitative proxy; denominator/window or why unavailable",
  "observation_limits": "preservation, sampling, ownership/use distinction, missing denominator, etc."
},
"actors": {
  "chooser": "who decides and on what evidence",
  "payer": "who supplies money/resources",
  "operator_maintainer": "who operates/repairs, including unpaid work",
  "affected_nonchooser": "workers, households, communities, etc.",
  "ability_to_refuse": "actor-specific evidence of choice, compulsion, dependence, unavailable alternatives, or unknown"
},
"labour": {
  "tasks": "tasks created/displaced/reorganised; paid/unpaid where known",
  "entry_barriers": "skills, assets, credentials, discrimination or unknown",
  "bargaining_ownership": "who controls gains/technology/work or unknown",
  "transition": "duration and individual/cohort evidence or unknown",
  "distribution": "observed outcomes by group; do not infer from aggregate productivity",
  "evidence_limit": "what this case cannot establish about livelihoods"
}
```

If a case contains several incompatible episodes/populations, split it or explicitly identify the subepisodes within these fields. Do not collapse mandates into consent or objects surviving into a diffusion curve.

## Claims: discriminating evidence (D03)

Add `test` to each claim. A purely descriptive claim may use `{"status":"descriptive-only","reason":"..."}`. Every mechanism-supported, causal-identification, contested or hypothesis claim must instead record:

```
"test": {
  "status": "evaluated / underdetermined / proposed",
  "mechanism_chain": "initial condition -> actor action -> intermediate change -> scoped outcome",
  "strongest_rival": "credible rival and its different or shared prediction",
  "discriminating_observation": "observation that would distinguish accounts",
  "evidence_sought_found": "what was actually sought/read and found, with source IDs",
  "remaining_ambiguity": "why evidence may still fit both; reverse/reciprocal causation where relevant",
  "hypothesis_timing": "pre-search candidate / emerged during research / retrospective synthesis"
}
```

Do not relabel causal assertions as descriptive to avoid testing. If both accounts predict the evidence, say underdetermined. Absence counts against a claim only when evidence would plausibly survive and be found. Psychological claims need independently observed beliefs/behaviour.

## Graph: bounded meaning (D02)

Add to every edge: `basis`, `scope`, `alternatives`, `joint_inputs`, `necessity_rationale`, `dispute`.
- `basis`: one of `technical-possibility`, `observed-contribution`, `documented-transmission`, `inferred-transmission`, `bounded-necessity`, `hypothesis`.
- `scope`: {`case_id`: an existing case ID, `stage`: a stage or explicitly named episode, `configuration`: exact local technology/task conditions}.
- `alternatives`: array of strings naming substitutable routes or documenting that alternatives are unknown.
- `joint_inputs`: array of node IDs only where the edge is part of a specified joint-input bundle; empty means no bundle claim, NOT sufficient cause.
- `necessity_rationale`: bounded counterfactual reason if claiming necessity; otherwise `"No necessity claim"`.
- `dispute`: contestation/uncertainty beyond generic confidence.

`depends-on` is reserved for `bounded-necessity`. Downgrade to `complements`, `enables` or `constrains` when only a contribution is observed. Chronology is not transmission. Technical possibility is not actual contribution. No transitive causal closure across episodes. Multiple incoming edges alone assert neither joint necessity nor substitutability. Preserve locally different configurations as distinct nodes; similarity is not identity.

## Comparisons and lineage (D04, D05)

Add `evidence_lineage` (string) to every source: identify original records/dataset/material, inherited account, or unknown; distinguish multiple analyses of shared evidence from independent corroboration. Do not pretend complete intellectual genealogy has been reconstructed.

Create `comparisons.json` (array) with a few consequential comparisons, not a quota. Fields: `id` (PREFIX-X01 etc.), `question`, `case_ids` (array), `useful_similarities`, `important_differences`, `evidence_comparability`, `connections_nonindependence`, `omitted_countercases`, `conclusion_limit`. Fields other than IDs may be strings or arrays. Empty is valid for a purely methodological contribution. Compare cases within your strand now; parent will add cross-strand comparisons. Include stable niche, continued older practice or non-exposure where it discriminates a proposed mechanism.

## Acceptance

Structural checks ensure fields and references survive export. Independent review must still judge whether actor scope, edge semantics, rivals and lineage are substantively adequate. Primary synthesis claims will be selected for consequential/contested/weak-access audits, with a disclosed ordinary-claim sample. Counts of links, agents or claims do not provide corroboration by themselves.
