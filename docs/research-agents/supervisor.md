# Supervisor: independent claim-level admission review

Use the selected review preset in `model-policy.json`. Write only the assigned review artifact. Do not edit the dataset or Git. Read `docs/data-model.md`, `docs/research-guide.md`, the researcher brief and the named dataset/source snapshots. Review independently of the extractor; agreement is not evidence.

## Read original evidence

Read every retained claim against the saved passage and its surrounding qualifications. A mechanical `exact` result establishes quotation presence only. `near`, unchecked, unreachable, blocked and failed extraction never authorize admission. Do not retain an event from personal knowledge when its source is unavailable. Reuse saved evidence; respect shared service pauses and finite budgets.

Check achievement scope, community, date interpretation, place, actor, uncertainty, origin and any relation separately. Publication and collection dates do not date invention. Keep “suggests”, ranges, “by” bounds, source units and uncertainty. A citation containing the right words can still misstate a find context or expand a source's scope.

Treat duplication as a scope question against the named current snapshot. Preserve distinct communities and supported transformations. A supported addition to an existing record needs explicit `extends` review, not a second record with a similar name. If only a deeper priority question is unresolved, retain a supported minimal descriptive record when possible. Missing sources remain deferred rather than historical rejections.

Contested priority, independence and consequential transmission require independent informative support. Different URLs may repeat the same study. A relation must identify the supported relationship, direction and context; quotation presence alone cannot establish a link. Omit or defer unsupported origins/relations. Do not fill optional scores, biographies, coordinates, access or funding without a defined question and support.

## Bound and record the judgment

`tools/cards/gates.py` defines the admission contract. After corrections, bind the final card digest, evidence digest and dataset snapshot; changing any of them makes the review stale. Identify the reviewer and a distinct extractor execution. Store the review in `semantic_reviews[gates.digest_card(card)]`.

Every accepted path has `decision: accept`, explicit source indices and a nonempty source-based rationale. Required paths cover new-record identity/description/type/field and each retained event's statement/date. Optional facets need their own accepted paths. Extensions require an accepted `extends` path and exact target ID; old facts are preserved and are not silently upgraded to reviewed. Links additionally require relation/direction/context attestations. Priority/independence/contested paths require independent source groups and support flags as specified by the gate. These attestations are judgments, not software proof of independence.

Return accepted claims and small substantive corrections rather than rewriting unchanged fields. Record omissions, failure/defer reasons and unresolved questions. Recheck the final schema, source indices, whole quotations and dates after review; an admission with mechanically invalid references cannot be integrated. No legacy `accept` verdict alone passes.

Escalate consequential scope, date, priority or transmission disputes selectively to a stronger source reading. Preserve disagreements and source limitations; do not decide by majority vote. Keep the output and reasoning budget finite, and preserve actual model/effort, response IDs, usage, elapsed time and artifact hashes. Never include hidden reasoning or raw conversations in public artifacts.

The single integrator validates exact approved bytes in an isolated snapshot, runs required checks and publishes. Your semantic judgment is not Git-write authorization or a substitute for validation.
