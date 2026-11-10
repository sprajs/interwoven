# Research more efficiently without weakening the evidence

Review prepared 10 November 2026. Evidence window: 9 November 19:00 to 10 November 09:40, Europe/London (UTC). Recommendations are proposed; this review does not change the research pipeline or admit discoveries.

## The recommendation

Use model knowledge to propose candidates, a persistent queue to decide what is worth researching, shared source retrieval to obtain evidence once, Luna for bounded extraction, Terra for an evidence-based admission review, and Sol/Astra for exceptions. Run breadth and depth as separate programmes. Replace the expensive conversational coordinator with deterministic scheduling and a small, bounded coordinator.

Your suggested strong-model → cheap-verifier → stronger-reviewer architecture is directionally right. The important refinement is that the cheap stage should extract from actual source passages, rather than decide historical truth from memory. A second model agreeing with the first is not independent evidence. The strongest model need not inspect every uncomplicated record.

There is no evidence here establishing that Astra knows more relevant historical facts than Sol, or that Luna can safely do all historical verification. Those model assignments need a controlled comparison. The architecture recommendation is firmer than the exact model choice.

## What the logs establish

The audit processed 131 local session files with usage in the window: 21 Codex sessions and 110 Claude sessions. It examined the main research conversation, its workers, four other project chats, Claude workflow scripts and journals, retained input/cards/review files, repository history, admission tooling, and 13,084 matching Codex runtime log rows. The two additional Claude worktree log directories contain no assistant activity in this window. This is the accessible local record, not a guarantee that every remote request or provider charge was logged.

The main Codex research campaign comprises 17 sessions with recorded usage. It ran approximately 21:17–00:49. The later Claude work included candidate curation, scoring, retrieval, supervision and application work through the morning. These are different workloads; their aggregate totals are not a fair model benchmark.

- **Codex research campaign:** 5,927 responses; 1,260,411,107 input presentations, including 1,242,169,600 cached; 2,284,005 output tokens.
- **Other Codex project chats:** 225 responses; 33,653,271 input presentations, including 33,038,208 cached; 213,857 output tokens.
- **Claude project activity, including app work:** 2,315 responses; 436,521,178 input presentations, including 419,233,363 cached; 5,395,160 output tokens.

“Input token presentations” counts the input reported on every response, including reused history. It does not mean that 1.26 billion unique words were researched. In the Codex campaign, 98.55% of input was cached; uncached input was 18,241,507 tokens. Reasoning is already included in output and must not be added again. Claude cache creation is included in its input column and is a separate charge category.

Two accounting traps materially affect this review. Codex cumulative counters can lag the final per-response records, so the audit counts unique response IDs. Claude repeats an entire message's usage on multiple content-block rows: 3,266 such repetitions were removed, with no changes in the repeated counters in this run. Goal counters, workflow totals, and child-session totals were not added on top of the same response records.

Exact calculations and a source-file hash manifest are retained in `audit.json`; `calls.csv` contains timestamps, models, roles and usage without conversation text. The Python auditor recreates both.

## The expensive coordinator is the first thing to change

The Astra coordinator made 937 responses, all at xhigh reasoning. Its median logged input was 161,798 tokens per response. It generated 209 follow-up calls and 101 messages to agents, and also made 116 web-tool invocations itself. Those actions include legitimate integration and historical review; their count alone does not establish that every action was unnecessary. It does establish that the coordinator was doing much more than scheduling cheap workers.

Using current standard OpenAI API token rates, the campaign's logged token mix is equivalent to approximately $257.62, excluding search/tool charges, cache-write ambiguity, long-context adjustments, and any plan-specific treatment. The coordinator contributes $174.57, or 67.8%. This is a comparison scenario, not last night's invoice or a reconstruction of subscription credits. [Official OpenAI pricing](https://developers.openai.com/api/docs/pricing) supplies the rates.

Repricing that same coordinator token mix as Sol gives $20.79. Holding every other response unchanged would reduce the campaign's modeled token cost by 59.7%. This isolates price sensitivity; it does not demonstrate equal quality or predict the cost of a rewritten pipeline. There is no basis for promising a tenfold overall improvement yet.

Use code for queue ownership, leases, retries, source-cache lookup, status counts, validation, file packaging and Git integration. Use a short Sol session for selecting the next work and resolving exceptional integration questions. Give it a bounded status summary, not every source page and every worker conversation. Reserve Astra for contested interpretations, research design, difficult cross-cultural concept reconciliation and periodic coverage critique. Start ordinary extraction and routine coordination at low/medium reasoning, increasing it when measured failures justify doing so.

Caching is already working well. The next gain comes from fewer expensive responses and less carried history, while retaining stable reusable instruction prefixes within bounded jobs. Shortening a prompt can also lose caching benefits; compare price-weighted usage rather than optimizing cache percentage alone. [OpenAI's prompt-caching guidance](https://developers.openai.com/api/docs/guides/prompt-caching) explains the distinction.

## The later run already tested much of your idea

Claude used nine curator agents without web research, small-model researchers, deterministic quotation checks, and stronger supervisors. The repository now contains briefs and admission tools for that pattern. Reuse and improve this work rather than build another parallel system.

The pilot researched six leads before adequate deduplication. Three rejected cards explicitly repeated existing records; a fourth could not be sourced. Only two were admitted. The subsequent deduplication pass classified 266 leads as 219 new, 33 duplicates and 14 extensions, and identified repeated leads within the new list. The final research queue contained 213 leads in batches 101–116 and 201–220. Candidate generation and queue admission must be separated by a mandatory deduplication step against a named dataset snapshot.

For the 96 leads in batches 101–116, supervisors accepted 81 with changes and rejected 15: an 84.4% acceptance yield. All accepted cards carry `accept_with_changes`; this is a workflow verdict, not proof that 100% originally contained factual errors. Inspection of batch 101 shows substantial revisions to dates, source scopes, capability names, and interpretations. Removing semantic review now would be premature.

At the cutoff, the retained files contain researcher cards for 111 of the 117 leads in the next wave, but no supervisor output files for those batches. The filesystem and workflow journals therefore preserve useful unfinished work. Resume those stages from artifacts rather than researching the 111 leads again. Old input files from an earlier pilot plan also remain; file counts alone overstate the active queue.

## Search availability was a bottleneck

The Claude transcripts contain 86 tool results matching search-limit/unavailability language and 56 matching blocked-page language. These are overlapping diagnostic counts, not independent incident counts. More concretely, nine of the 15 first-wave rejection explanations explicitly mention unavailable/exhausted search. These are unsatisfied leads, not evidence that the historical achievements did not occur.

The source fetcher retries failed pages on subsequent calls and can cache bot-check text as if it were a document; supervisors manually removed some such cached pages. Spawning more researchers while a shared search allowance is exhausted increases contention without supplying evidence.

Add a source-acquisition queue with explicit statuses: fetched, blocked, search-budget-exhausted, extraction-failed, and unsupported-claim. Pause dispatch into an unavailable service while other jobs continue from saved sources. Put time-limited negative caching and bounded retries in code; retry transient failures later, and use permitted alternative institutional repositories. Do not repeatedly send a blocked page to several models.

The matching Codex runtime logs contain four stream-retry warnings, six plugin-icon warnings, and one nonexistent-agent-path error. These logs do not suggest a large infrastructure retry storm. Search restrictions, large histories and conversational work are better-supported priorities than transport tuning.

## Collect less per candidate, while keeping the long-term scope

Everything can still belong eventually. Efficient collection means sequencing, not excluding regional achievements or less famous fields.

At commit `eed7790`, there were 304 discoveries and 665 sources. The final committed Codex research batch (`32cf878`) had 803 discoveries and 1,486 sources: 499 additional discoveries, 260 quantitative measures and 652 event contributions. The morning committed state (`a51b7e9`) had 886 discoveries. The preserved working tree has 899, including 13 unfinished new discoveries. Do not conflate committed, uncommitted and independently reviewed output.

The broad catalogue made substantial progress. It is not yet a sufficient panel for studying who gains technological agency: the morning committed state has measures on 187 of 886 records, and 636 lack an assessed origin. These absences are useful prioritization signals, not an instruction to fill every facet on every record.

- **Candidate:** collect capability, community/region, broad era, aliases, reason to investigate and uncertainty. Defer exact dates, biographies, invented bibliographies, polished prose and detailed impact scores.
- **Minimal sourced record:** collect a precisely bounded achievement, supported date/range, supported place, concept proposal, and one adequate source passage with provenance. Defer an exhaustive lifecycle, every actor, repeated narrative and numerical adoption series.
- **Mechanism case:** collect funding, capital/equipment/skills, developers/manufacturers/operators/users/controllers, access barriers and changing denominators. Defer unrelated biography, decorative object details and speculative influence edges.
- **Evidence synthesis:** collect comparable measures, contradictions, exceptions, and dependence/transmission where directly supported. Exclude automatically inferred causal claims and missing-as-zero values.

Require more than one independent source when a contested priority, transmission, independence or causal claim needs it. A second source is not automatically useful for an uncomplicated descriptive fact. Prefer a minimal honest record over several extra events carrying the same unexamined date bracket.

Keep institutional dates, original units/currencies, adoption denominators and source context when they matter. Do not spend the initial pass finding birth/death dates, exact coordinates for vaguely located achievements, detailed impact scores, repeated source biographies, or a complete network of links. Preserve such material when a source supplies it cheaply, but do not open separate research jobs merely to make records look complete.

Source-record duplication is currently modest: 14 redundant exact-URL rows among 1,586 committed sources. It is worth centralizing source IDs, but this is not the dominant waste. Distinct citations to different editions or passages can be legitimate.

## Run two coordinated research tracks

The breadth track establishes a global capability catalogue across the existing taxonomy, regions and eras, with independent origins and meaningful transformations preserved. Use explicit coverage cells and gaps, not a demand that every cell have the same number of records. A filled field is not evidence of completeness, and a missing record is not evidence of historical absence.

The depth track selects a manageable set of technology transitions that can test the original question about institutions, falling participation costs and individual agency. For example, navigation, printing, powered manufacturing, electricity, computing and internet production provide different mechanisms and counterexamples; this is a proposed case-selection framework, not a new historical finding. Include reversals, failure, exclusion and shared infrastructure. Distinguish the ability to use a capability from the ability to build, modify, finance or control it.

For each selected transition, define the comparison first. Counts of telephones, shares of households with refrigeration, enterprise AI use and individual generative-AI use have different populations and cannot simply be combined into one adoption curve. The existing reference pilots correctly preserve these distinctions. Expand a panel only when it answers a defined comparison; do not systematically download adjacent datasets just because they are available.

## Use knowledge and sources together

Model memory is an effective proposal engine. It is neither a comprehensive catalogue of human knowledge nor a reliable citation database. Ask for short candidate lists by coverage cell, explicitly allowing unknown dates and uncertain independence. Disable web tools for that bounded generation stage, but provide a compact current inventory so the model can avoid duplicates. Tool-free generation does not mean the scheduler must avoid local deduplication and validation.

Use Sol as the first candidate generator to test. Ask Astra to critique omissions in sparse or difficult cells, rather than regenerate the entire list. Compare their marginal novel, useful candidates at the same output budget. The nine Claude curators consumed 805,907 output tokens, including 569,873 reasoning tokens, to produce the retained curation work. Having no web research therefore did not make that stage automatically cheap.

Combine this with source-led harvesting: scholarly histories, museum catalogues, bibliographies, archaeological reviews and structured source collections can yield several candidates and passages from one retrieved document. This is also how to find achievements and non-English evidence that an English model-memory list might miss. Crawl defined collections with licenses, rate limits and access conditions respected; do not attempt an undefined scan of “all the internet.” Keep memory-led and source-led discovery as complementary routes.

Retrieve once, retain a content hash and access timestamp, extract text once, and index passages. Send the extractor only the candidate and relevant passages with enough surrounding context to preserve qualification. The current fetcher does cache successful text, so this improves and hardens an existing facility; it is not a claim that every quotation check downloads the page again.

## The proposed admission pipeline

1. **Plan:** Sol proposes short candidates from a compact coverage inventory; occasional Astra critique supplies missing leads. Memory fields remain hypotheses.
2. **Deduplicate and claim:** code checks IDs, aliases, concepts, communities and time scope; ambiguous semantic matches go to a bounded model decision. A durable lease prevents two workers claiming the same lead.
3. **Acquire sources:** a shared retriever prefers saved material and known authoritative catalogues, then performs targeted search. Failure reasons and costs are recorded.
4. **Extract:** Luna receives one candidate or a small related batch and source passages. It returns structured claims, verbatim support, locators, and unresolved items, with no unsupported filler.
5. **Check mechanically:** validate schema, references, date ranges, conversions, passage presence and source hashes. This stage cannot establish that a quotation entails a historical claim.
6. **Review semantically:** Terra examines every proposed admission initially against the original passage context. It returns accepted claims and a small patch/reason, rather than rewriting every unchanged field. Sol handles ambiguous grain/origin/transmission cases; Astra handles unresolved consequential disputes.
7. **Integrate:** code compiles accepted cards into a staging snapshot; validate that snapshot, run checks affected by tooling/schema changes, and commit coherent batches through one integrator. Reuse valid results unless the evidence or policy changes.

Maintain claim-level checks: quotation text found, date interpretation checked, place checked, origin checked, and relation checked are different outcomes. A single `sourced` label must not imply all of them.

Two current shortcuts particularly need attention before scaling: the quote checker treats a 60% contiguous word match as `near`, and admission treats `near` like `exact`. Admission can also establish a link on that match. A quotation containing some of the right words does not prove its date, qualification, direction of influence, or the link's interpretation. Require exact normalized matching or explicit reviewed discrepancy, plus semantic acceptance. Retain original source context so an excerpt-location heuristic cannot save an unrelated four-word match.

## Bounded jobs and durable state

Begin with one candidate per extraction job or up to six when they share sources. As trial limits, use approximately 8–16k input tokens for a normal job, 1–2k output, and at most three targeted searches before deferral. These are proposed starting budgets, not measured optimal limits; complex sources may justify escalation. Prefer removing unnecessary prose over truncating necessary evidence. A small-reasoning model doing a large autonomous browsing task can still be expensive and unreliable.

Store leads and jobs durably: candidate ID, dataset revision, assigned stage, lease owner/expiry, source hashes, prompt/model version, attempt number, completion artifact, rejection reason and token/tool/elapsed usage. The system should restart a missing stage, not replay successful acquisition and extraction. Snapshot review prompts against the same dataset and source versions. Mark older judgments stale only when their inputs or rubric changed.

Do field/region/era audits at batch boundaries or when a coverage cell changes, not after every individual record. Have scripts calculate coverage, duplicates and missing facets; ask a model to interpret only the resulting exceptions. Existing SQLite/FTS research tools already make local lookup cheap. Millisecond query tuning is secondary to eliminating hundreds of model round trips.

Keep raw downloads outside the agent prompt, with required licensed excerpts, metadata and hashes retained according to policy. Compact handoffs should contain accepted IDs, failed IDs, reasons and artifact paths. Avoid full-history forks and long prose progress reports to other workers. Completion events should wake the scheduler; a large conversational agent need not continually ask whether work has finished.

## Decide the model mix with a small controlled evaluation

Before another unbounded overnight campaign, use a fixed 100-candidate calibration set spanning easy institutional sources, archaeological dating, contested independence, source failures, underrepresented regions and duplicate/extension cases. Freeze the candidate and evidence snapshots. Compare Luna extraction + Terra review with Terra extraction + Sol review, and use independently adjudicated source readings as the reference. This tests the actual workload rather than selecting on advertised model strength.

For proposal generation, compare equal-budget Sol and Astra lists against the same inventory. Measure marginal useful novel candidates and coverage, not list length or how confident they sound. Keep a held-out set after tuning prompts. Review false rejections as well as false admissions; a cheap system that silently loses difficult regional evidence is not efficient.

Measure cost per useful reviewed record, cost per supported claim, first-pass acceptance, substantive corrections, duplicate work, deferred-source failures, search requests, bytes retrieved, cache read/write tokens, wall time and human adjudication time. Track breadth output separately from evidence-rich mechanism cases. Claimed records per hour and raw total tokens are inadequate alone.

The first 100 cases select prompts and routes; they cannot prove a sub-1% error rate. Even zero independent errors in 100 cases leaves an approximately 3% one-sided 95% upper bound. Roughly 300 independent zero-error checks are needed to get near 1%, and shared sources can make checks correlated. Keep semantic review on every admission until the evidence supports relaxing it. [OpenAI's evaluation guidance](https://developers.openai.com/api/docs/guides/evals) supports testing against representative inputs; these sample sizes are statistical calculations, not provider guarantees.

Set a finite per-run cost/time budget and explicit stop/defer conditions. Stop enlarging a coverage cell when a documented candidate/source search is exhausted for that pass, recording what remains uncertain. Do not use “all major human discoveries found” as an operational stopping rule: it cannot be proven by repeatedly asking the same models for more examples.

## Order of implementation

First preserve and inventory the unfinished cards, correct the usage accounting, enforce deduplication before retrieval, and give search failures a durable defer state. Replace Astra's scheduling loop with code plus bounded Sol decisions. Harden source snapshots and the semantic admission gate before increasing throughput. Then run the controlled model comparison, choose budgets from its results, and resume the existing queue. Bulk/asynchronous processing can reduce costs for independent extraction/review jobs where supported; it does not remove retrieval dependencies or automatically apply to desktop agent calls. [OpenAI's cost-optimization guidance](https://developers.openai.com/api/docs/guides/cost-optimization) recommends reducing requests and tokens as well as choosing smaller models.

The evidence supports a large avoidable coordination cost and identifiable retrieval/deduplication waste. It does not establish the exact savings, throughput or error rate of the proposed replacement. The next useful investment is a bounded, instrumented pilot, followed by systematic breadth and targeted depth—not another open-ended run with the same conversation structure.

## Reproduce and inspect

`tools/research_efficiency_audit.py` reads local logs without modifying them or copying conversation text into the analysis. Example arguments for this machine are recorded in `reproduce.txt`. `audit.json` records the reviewed source commit, per-file SHA-256, role/model totals, diagnostic counts, pipeline inventory and dataset checkpoints. `calls.csv` permits independent aggregation. `viewer/` retains the authored report content and chart inputs; `tools/research_efficiency_report.py` regenerates them and the static figure from these reviewed values. Runtime billing, missing requests and undocumented advisor calls remain outside the accounting.
