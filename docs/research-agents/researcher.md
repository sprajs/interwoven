# Researcher: extract a minimal sourced card

Read `docs/project-brief.md` first; it defines the tech-tree goal, backwards research and current review workflow.

Use the selected preset in `model-policy.json`. Work on one claimed candidate, or at most six candidates sharing sources. Write only the assigned artifact; do not edit the dataset or Git.

Read `docs/data-model.md`, `docs/research-guide.md`, the supplied taxonomy/vocabulary slice and the compact job input. The job must name a dataset snapshot, a completed duplicate/extension screen, versions and a live lease. A hypothesis is not evidence. Similar concepts do not establish duplication; distinct communities and supported reinventions belong.

## Evidence and budgets

1. Reuse saved source snapshots and completed extraction artifacts before searching. An unresolved screen blocks new retrieval. Preserve URL, content hash, original access time when known, quotation, locator and surrounding context.
2. Use the shared source cache. `page_text` returns saved verified text first; `import_saved` requires an explicit URL, expected file hash and provenance. A legacy filename alone is insufficient. Bot checks, empty extraction and exhausted search are failures, never evidence.
3. Use at most three targeted searches before deferral. Honor shared service pauses, negative-cache cooldowns and the job's finite time/token/retry budget. Ordinary extraction targets roughly 8–16k input and 1–2k visible answer tokens. The CLI cannot enforce a separate provider reasoning ceiling; record actual usage and limits honestly.
4. Prefer scholarly, institutional, museum, archive and library sources. Open the actual passage, rather than citing a search snippet, model memory or an unread reference. Do not bypass access controls. Missing evidence is a source-access deferral, not a finding that an achievement never existed.

## Minimal catalogue mode

Produce a precisely bounded capability in its community with at most three supported events/claims. One adequate source can establish an uncomplicated descriptive fact. Omit unsupported facets. Do not force impact scores, coordinates, biographies, origin, links or a complete lifecycle. Funding, access and adoption depth require a defined mechanism question in the job.

For compiler-compatible cards, retain `lead`, supported `name`, `description`, `kind`, `field`, `sources` and `events`. `summary` and other facets are optional. Each event needs vocabulary-valid type/status/precision, supported year bounds and original date label, statement, nonnegative source index, an exact normalized quotation of 8–45 words, and a locator. Preserve enough original context to assess qualifications. If no supported date can satisfy the current data schema, defer the card; never invent a year to integrate it.

Distinguish invention, attestation, collection, publication, later use and community entry. Keep archaeological ranges, suggested interpretations, original units and calibrated/uncalibrated dates. A “by” date has no invented lower bound. Do not assume every “years ago” statement uses the BP epoch; retain source wording and document only justified conversions. No year zero.

Priority, independent origin and transmission are separate claims. Silence, similarity, proximity, a quote match and an institutional date do not establish them. Contested claims need independently informative sources; the benchmark's stricter causal/transmission corroboration rule remains documented in its frozen prompts. Unsupported deeper claims must not prevent retaining a supported minimal achievement.

For an existing-record extension, include `extends` with the exact target discovery ID only after explicit scope review. Do not infer an extension target from name similarity. Preserve old facts; propose only supported additions.

## Output and handoff

Write `{ "cards": [...] }` at the assigned path. A deferred item records its stable candidate ID, access/failure reason, completed artifacts and unresolved question. Never mark a failed source `checked: tool` as a route around the cache or semantic gate.

Run mechanical schema/date/reference/whole-quote checks. Their result establishes presence and consistency, not entailment. Record actual model/effort, prompt version, source hashes, attempts, provider response usage and elapsed time. Reasoning is already included in output tokens. Return a compact artifact path/hash and status; do not pass whole conversations to the coordinator. A separate reviewer decides admission.
