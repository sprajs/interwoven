# Parallel quality sweep: six review settings, forty candidates

The same source evidence, current dataset screen and Terra-low extraction were given to all six reviewers. Twenty-four cases were outside the earlier 100-case comparison and sixteen were regression controls. Source judgments are blinded model readings, not independently verified historical truth.

## Source quality and coverage

One case about high-fired glazed stoneware has contradictory reference and extension labels: all four reference readings reject a duplicate, while five reviewers propose a source-supported Zhou expansion event. The matched record already mentions Zhou spread in its description but has only a Shang dated event. The data model and research guide support separately dated adoption/spread events, so a bounded Zhou extension fits the existing policy. The model reference labels applied that policy inconsistently; this is a grading-consistency issue, not a proven factual error. Its six raw rows remain available; all six are excluded uniformly from the comparative quality ranking below. That 39-case ranking is a post hoc sensitivity, not the preregistered full-set gate. The corrected full 40-case metrics are in `result.json` under `raw_summaries`; `primary-raw.json` is the preserved initial analysis snapshot and its derived metrics are superseded.

| Review setting (39 cases) | Mechanical failures | Source flags (either judge) | False rejects (either) | Useful records (both) | Usable supported claims (both) | Reviewer cost, 40 cases observed cache USD | Reviewer cost, 40 cases no-cache USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| astra_medium | 0 | 0 | 0 | 26 | 56 | $3.8144 | $4.8743 |
| astra_low | 0 | 0 | 0 | 26 | 54 | $3.5765 | $4.7746 |
| terra_high | 0 | 0 | 1 | 25 | 55 | $0.3617 | $0.4930 |
| sol_medium | 0 | 0 | 1 | 25 | 52 | $0.9250 | $1.0028 |
| terra_medium | 0 | 0 | 3 | 23 | 46 | $0.3226 | $0.4685 |
| sol_high | 0 | 1 | 2 | 24 | 50 | $1.0770 | $1.1743 |

The fresh and regression case breakdowns, reviewer-specific flags, disagreements and latency distributions are in `result.json`.
The order prioritises source quality and useful coverage; cost breaks quality ties. A flag is counted when either judge flags an admission or finds an unresolved/unsupported retained claim. The disputed case is excluded equally for every setting; raw judge labels are unchanged. The 39-case quality gates are exploratory sensitivity checks, not full-set certification. Source decision and claim-label disagreement counts remain in `result.json`; no vote converts model readings into truth.

## Timing and cost

480 new provider calls with 480 unique response usage IDs. Total $21.1179 standard API-equivalent including shared extraction and both evaluation readers. Wall time from first request start to last end: 980.8 s; serial sum of call latencies 9067.8 s. Up to twelve calls were allowed per stage; review/judge handoff overlapped briefly and observed peak was 13. This is a scenario estimate, not observed billing.

Review-only costs above include observed prompt cache discounts; the no-cache column applies full input rates to all input tokens to reduce warm-cache-order distortion. The [official model pricing](https://developers.openai.com/api/docs/pricing) supplies per-token rates. Shared extraction and independent source reading are separately included in `result.json` accounting.

## Boundaries

The cases, current committed dataset snapshot, saved source hashes, prompts, models, judges, selection order and finite limits were registered before model calls. The event-grain exclusion is a later sensitivity decision, recorded with its original labels. Original source passages, raw prompts, full answers, rationales and usage response IDs remain private; public case rows contain only bounded scalar labels and costs. Missing source access and uncertain reference decisions remain explicit. Neither model reader is a historian or independent historical ground truth.


## Repeated calls

Eight repeat case IDs were chosen by a deterministic fresh/regression hash rule; the original Astra-medium/Astra-low pair was repeated. The repeat-plan file was reconstructed from immutable call records after dispatch, and says so explicitly. Eight additional Terra-medium repeat review calls were initiated during score correction; their outputs are retained and costed, but have no new blind judgments and do not enter repeat quality metrics. These are stability checks, not independent cases. See `result.json` for counts.
