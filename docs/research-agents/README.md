# Researching in batches with agents

Research runs keep source acquisition, claim extraction, semantic review and dataset integration separate. A quotation appearing on a saved page establishes passage presence. A reviewer must still decide whether that passage supports the date, community, origin and proposed relationship.

The [measured interim model policy](model-policy.json) uses Terra low extraction and tightened Terra medium admission review, with Sol medium proposals and selective dispute escalation. The revised review cleared eight diagnostic and twelve reused confirmation cases in the [small pilot](../reviews/2026-11-10-workflow-pilot/report.md). Those model-based results support an interim choice, not a population error guarantee. Automatic admission remains disabled. The earlier [100-case comparison](../reviews/2026-11-10-workflow-comparison/report.md) remains unchanged.

Read [the data model](../data-model.md), [the research guide](../research-guide.md) and [importance guidance](../importance.md) before preparing records. Regional achievements and independent reinventions belong. Similar names and shared concepts trigger scope review; they do not establish duplication.

| Role | Brief | Output |
| --- | --- | --- |
| Curator | [curator.md](curator.md) | Candidate capabilities and communities, with hypotheses clearly distinguished from evidence |
| Researcher | [researcher.md](researcher.md) | Source-backed claims and complete quotations with locators |
| Supervisor | [supervisor.md](supervisor.md) | Independent, claim-by-claim semantic review bound to exact inputs |
| Scorer | [scorer.md](scorer.md) | Impact and grain assessment against the existing dataset |

## Durable jobs and screening

`tools/cards/workflow.py` provides a SQLite queue API. It does not call models or change the live dataset. Store the queue and artifacts outside `data/`; keep durable research state outside disposable temporary directories.

The stages are `screening → acquire → extract → mechanical → review → integrate`. Enqueueing binds candidate identity to an immutable committed dataset snapshot and stage versions. Include community and era in candidate identity. Record prompt, model, evidence and rubric versions in the appropriate stage version. A changed snapshot invalidates screening and downstream judgments while retaining reusable acquisition/extraction; a changed stage version invalidates that stage and its successors.

A minimal library example, run from the repository root:

```python
import sys
sys.path.insert(0, 'tools/cards')
from workflow import Queue, committed_snapshot

queue = Queue('/absolute/durable/research/jobs.sqlite')
snapshot = committed_snapshot('.')
candidate = {
    'id': 'stable-lead-identifier',
    'name': 'Candidate title',
    'community': 'Community to investigate',
    'era': 'Period to investigate',
}
key = queue.enqueue(candidate, snapshot, versions={
    'screening': {'rubric': 'scope-v1'},
    'extract': {'prompt': 'extract-v1', 'model': 'record-actual-preset'},
    'review': {'prompt': 'review-v1', 'rubric': 'claims-v1'},
}, max_attempts=3)
lease = queue.claim('screen-worker', stage='screening', ttl=300)
if lease:
    result = queue.screen(lease, '.')
    print(result)
```

The default screen defers candidates with inventory matches. An explicit decision and reason may classify a candidate as `new`, `distinct-community`, `extension`, `duplicate` or `defer`. Review the matched record's community, events and scope before resolving it. Fuzzy name matches are navigation aids.

Workers must retain the returned lease token when completing, failing or renewing a job. Expired workers cannot publish. Failures record a reason and bounded retry count; exhausted or deferred jobs require explicit `resume`. `pause_service` records a shared search outage or quota exhaustion so other workers do not repeat failing work. The queue is orchestration infrastructure: a complete job flag alone is not historical acceptance or permission to write records.

Use explicit stable IDs when a candidate's wording may be corrected. Candidate-content changes invalidate old jobs and fence outstanding leases. `defer_pending` records retained missing evidence without inventing an attempt; it cannot replace leased or successful work. `adopt_artifact` imports verified acquisition/extraction artifacts with versions, provenance and source hashes, while fresh screening still blocks dispatch. `resume_retained.py` restored 213 candidates: 181 retained acquisition/extraction pairs and 32 explicitly deferred incomplete source sets, with no research dispatched.

## Source acquisition and extraction

Save a public source with:

```sh
python3 tools/cards/fetch_page.py 'https://example.org/source'
```

The shared cache uses the complete URL hash, content hashes and metadata. Concurrent requests share a URL lock. Blocked, empty, extraction-failed and search-budget-exhausted responses remain failures; they never become historical evidence. Negative-cache cooldowns and service pauses bound repeated retrieval. Import a legacy saved page with `import_saved(url, path, expected_sha256, provenance)`; no new request is needed. Unknown original access dates remain unknown, separate from import time.

Preserve the original source text, content hash, quotation and locator. Extract distinct dated events rather than collapsing earliest evidence, later adoption and community entry into a single date. Leave unsupported facets empty. Keep candidate hypotheses and recalled knowledge separate from sourced claims.

Run the mechanical quotation check on a cards envelope:

```sh
python3 tools/cards/check_quotes.py /absolute/durable/research/cards.json
```

Only complete meaningful quotations pass the gate. Near matches remain diagnostics. The check can acquire missing pages and records the content hash used; a previous unversioned verdict is insufficient.

## Semantic review and staged integration

`tools/cards/gates.py` binds a semantic review to the exact card digest, evidence digest and dataset snapshot. The reviewer must differ from the extractor. The envelope stores reviews under `semantic_reviews[gates.digest_card(card)]`, with accepted claims keyed by card paths and accompanied by source indices and rationales.

Review required identity/description/type/field claims, each preserved event's statement and date, and every nonempty optional facet. Links additionally require explicit relation, direction and context attestations. Priority, independence and contested claims require support from two distinct source groups. These are explicit reviewer attestations; the software does not prove source independence or entailment.

Compile a reviewed envelope without writing records:

```sh
python3 tools/cards/admit.py /absolute/durable/research/reviewed-cards.json
```

Old supervisor verdicts, an `accept` label or quotation matches alone cannot authorize admission. Resolve every semantic or compilation error before integration.

An extension uses `extends: <exact existing discovery ID>` with an accepted `extends` claim. It appends reviewed nonduplicate events or missing optional facets, preserves existing facts/evidence/status, and does not infer a target from a similar name. Unsupported new fields cannot overwrite old ones. Apply requires `--queue` and `--owner` to acquire the shared integrator lease, in addition to isolated staging and all admission checks.

Use the queue's single integrator lease and `stage_integration(repo, snapshot, changes, queue, lease)` to validate exact task-owned bytes in an isolated copy of the committed snapshot. It runs dataset validation and code tests when applicable, and returns a manifest with hashes; it does not stage Git files or publish changes. Recheck the snapshot at the final write boundary, publish only the reviewed manifest, then follow the repository's fetch/rebase/check/direct-push rules. The low-level `admit.py --apply` interface exists, but it is not a substitute for isolated staging or integrator coordination.

## Small experiments before broad comparisons

Use small staged experiments when changing the workflow. Start with a few known failures plus ordinary, duplicate and missing-source controls. Reuse unchanged acquisition and extraction artifacts so each experiment isolates the changed stage. Run independent cases concurrently within a shared call, cost and wall-time budget.

Freeze the cases, source hashes, prompts, model settings and selection rule before dispatch. Compare final claim support and useful admission coverage together: blanket deferral must not win. Verify exact quotations, source references and dates mechanically, then assess the final assertions against original source context with model identities and previous judgments hidden. Retain schema failures and disagreements rather than silently retrying until a pass.

Select a candidate on the diagnostic cases, freeze it, and compare it with the unchanged baseline on disjoint cases chosen without looking at their outcomes. Cases drawn from an earlier benchmark are reused confirmation, not an untouched test set. Expand only when the smaller comparison supports doing so. Report acquisition/extraction reuse, new call cost, evaluation overhead, elapsed time and unresolved judgments separately. A small clean sample does not certify a low population error rate or authorize automatic admission.

See the [small workflow pilot](../reviews/2026-11-10-workflow-pilot/report.md) for the measured iteration after the initial 100-case comparison. The older comparison below remains a frozen historical experiment.

## Frozen workflow comparison

The [comparison preregistration](../reviews/2026-11-10-workflow-comparison/preregistration.json) names exactly 100 retained real candidates, with 20 calibration and 80 held-out cases. Primary strata cover ordinary institutional research, archaeological uncertainty, contested origin/transmission, underrepresented regions, identity/scope controls and genuine missing-evidence cases. Earlier identity controls intentionally overlap committed records.

`tools/cards/prepare_comparison.py` creates that fixture from retained research and the named committed snapshot without model or network calls. It is a preparation tool: do not rebuild or change the registered fixture after benchmark calls begin. The fixture preserves hypotheses separately from source excerpts, committed match context and private hashed original pages. Both arms receive the same saved evidence; missing evidence stays missing. The original pages are private and must accompany a reproducible local run; checked-in excerpts alone do not reproduce every source-reading judgment.

The preregistration records model presets, finite call/time/token/cost guards and separate proposal-generation metrics. Proposal suggestions never enter the fixed admission set. The documented Codex CLI offers effort presets but no strict 25,000 reasoning-token ceiling, so that ceiling is explicitly unsupported. Cumulative guards checked between requests may overshoot with up to four requests in flight.

Freeze source-only reference reviews for all 100 cases before running either arm. Then run the 20 calibration cases, freeze prompts and settings, and run the 80 held-out cases:

```sh
python3 tools/cards/compare.py --split calibration --only reference --workers 4
python3 tools/cards/compare.py --split held_out --only reference --workers 4
python3 tools/cards/compare.py --split calibration --only arms --workers 4
# Freeze prompts and settings before the following command.
python3 tools/cards/compare.py --split held_out --only arms --workers 4
```

The runner defaults to durable state beside the repository in `big_idea-research-state/workflow-20261110/comparison`; `--state` selects another location. Set `BIG_IDEA_EVIDENCE_ROOT` to relocated hash-named source text files on another machine; hashes must match without rewriting the frozen fixture. Check `python3 tools/cards/compare.py --help` before a run. The `--only both` mode exists, but reference-only runs must precede arms for the preregistered comparison. Analysis belongs in `tools/cards/analyze_comparison.py`; pending runs and unreviewed outputs are not results.

`adjudicate_comparison.py` performs blind source assessment. `compare_proposals.py --prepare-inventory`, generation, then `--review-quality` keep proposal text metrics separate from verification. `finalize_comparison.py` rebuilds the completed report without model calls, and `comparison_viewer.py` regenerates canonical Data viewer source. Exact raw requests, provider usage and original sources stay private; public results contain structured answers, quote hashes and bounded judgment labels. The code records one bounded adjudication schema-repair exception, including its original response and cost.

The blinded Astra reference is independent of arm outputs, but remains a model judgment with correlated failure risks. Selective source inspection of disputes does not turn it into independent historical truth. Report unresolved references, coverage, disagreements and sensitivity to reference uncertainty. No winner is supported without sufficient quality evidence; the held-out gates require zero false admissions, zero unsupported links and no more than 5% false rejects among resolved reference admissions.
