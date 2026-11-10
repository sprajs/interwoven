# Tech-tree research round 1 — bounded, independently reviewed additions

The round adds **two discovery records, four events (two on existing records), and one extension to an existing event**. It establishes **no new prerequisite, causal or transmission edges**. One Antikythera–Babylonian astronomy relation remains an explicitly labelled candidate question and is excluded from established graph connections. No circumstances were added.

The new Sangjeong and Savery records are useful antecedents found while researching backwards; their earlier dates do **not** establish them as prerequisites of Jikji or Newcomen. This small, deliberately bounded round is not a general efficiency experiment and cannot establish that backwards research outperforms other methods.

## What changed

| Lane | Independently accepted addition | Boundary and next question |
| --- | --- | --- |
| Proto-porcelain | A missing `dated_assertion` event for wider prevalence during the complete source period, Zhou 1027–221 BCE, on the existing Shang discovery. | The UCL thesis abstract supports broad prevalence, not a site, onset year or route. Original site reports should clarify distribution. |
| Jikji / Korean metal type | A separate reported *Sangjeong Gogeum Yemun* metal-type edition, estimated 1234–1241, with the museum's report of 28 copies. | No physical copy or original postface was inspected. The museum's approximate postface date around 1234 and the paper's estimated printing interval need reconciliation. No direct lineage to Jikji is asserted. |
| Newcomen | Savery's **1702 published description** of a condensation/steam-pressure water-raising engine; a Newcomen event for the museum's report of at least 100 engines in Europe **by 1729**. | Savery's text is an inventor's promotional account, read through an 1827 reprint transcription. It does not prove successful mine installation or influence on Newcomen. The Newcomen count's underlying register was not inspected. |
| Antikythera | Existing archaeological event extended with the 223-lunar-month eclipse-possibility dial and the qualification that about a third of its scale survives. | The possible Babylonian theoretical connection is a candidate question, not proven transmission. Earlier and later palaeographic interpretations of construction date require follow-up. No loss is inferred from missing descendants. |

The proto-porcelain control compares actual event type, subject, bounds and scope. The existing Shang appearance event is a **true duplicate and is rejected as an additional event**; the subsequent Zhou prevalence is absent from the base event array despite appearing in description text. The new review uses `tech-tree-event-scope-v1`. Earlier benchmark labels and the 480-call sweep were not changed or rerun.

## Source and review provenance

Base for every writing lane: `07f1f1e085edf3c471c67a620f9a34ebc64fdf61`, fetched from `origin/main`. The root coordinating chat explicitly spawned `/root/astra_orchestrator` with **`gpt-6-astra`, effort `medium`**. The root chat's model is not inferred. This orchestrator explicitly spawned four researchers and four separate reviewers, each **`gpt-6.1-terra`, effort `high`, `fork_turns: none`**, with no model substitution.

Each researcher had a separate `codex/tech-tree-round-1-<lane>` branch and worktree under `/Users/szymon/.codex/worktrees/tech-tree-round-1/`, created from the same base. Maximum concurrent research lanes: four. Reviewers wrote only assigned review artifacts and did not edit dataset or Git. No researcher approved their own patch.

| Lane | Exact independently reviewed worker commit | Review artifact |
| --- | --- | --- |
| Proto-porcelain | `eaa501952f791c024e121820c91b5c1e8723c980` | [porcelain.json](reviews/porcelain.json) |
| Jikji | `ea86c30cd7108a82b0ac0b2edb76f27f2dc6f196` | [jikji.json](reviews/jikji.json) |
| Newcomen | `50ab56d6eca3016c33a78f11f310a1ca8b77482c` (includes proposal `cca68f51d27b82b3e52036e6abf9b5ffb1bb2d6a`) | [newcomen.json](reviews/newcomen.json) |
| Antikythera | `12008b663cdfb8892d73b5127ebdc1d8de4fbfa1` | [antikythera.json](reviews/antikythera.json) |

These are **direct dataset patch reviews**, with claim-level decisions and immutable commit/file/evidence hashes; they did not run the separate `tools/cards` admission pipeline. No card-gate success is claimed. Unchanged historical claims and research facets were not silently upgraded to reviewed. Historical lane submissions retain their proposal-time “pending” language; the separate review artifacts provide subsequent acceptance. Savery deliberately retains conservative `draft` record status despite acceptance of these narrow claims.

Seven source records were added. They are not seven independent corroborations: the new Yin and NMS records preserve new passages from already catalogued works, and the two Sangjeong accounts ultimately concern historical literary testimony. Consequential causal/transmission claims were withheld because this round did not establish independently informative corroboration for them.

Original-source inspection is scoped in each artifact. The porcelain decision is based on the original UCL repository abstract, not a complete thesis/site-report audit. The Antikythera reviewer read the studies' original text and identified a nonblocking inherited date issue: Freeth's 150–100 BCE inference and the broader letter-form range discussed by Iversen and Jones should be reconsidered together. The old date remains unchanged and is not newly approved. The Newcomen reviewer inspected the retained excerpt and indexed museum opening after a direct fetch timed out; the reported count remains attributed to the museum.

## Integration checks and preservation

Only approved worker changes were cherry-picked onto `codex/tech-tree-round-1-orchestration`; the assembled data commit is `5ebb00da2dddb2aa66b44548291fb03fe7a4be96`. All 25 reviewed file/evidence hashes match the assembled files, including the locally cached PDF. Every changed data/evidence file is covered by an acceptance artifact. The PDF remains ignored locally; only its retrieval descriptor is committed.

- `python3 tools/validate.py`: passed — 888 discoveries, 1,473 events, 233 stored links, 1,593 source records.
- `npm test`: passed — 165 Python tests and 53 Vitest tests in three files.
- `python3 tools/build.py`: passed — compiled data `602b8900c339add6f5459d52`, with 202 visible links (candidate/insufficient links are not established connections).
- `npm run build`: passed — TypeScript and Vite. The build reports a nonblocking large-chunk warning.
- Review hash binding, protected-path overlap and preservation: passed; all 92 original unfinished files still match the supplied preservation manifest. `setup-verification.json`, shared registers and app UI were untouched.

The exact 30 changed paths are listed in [changed-paths.json](changed-paths.json). See [integration-verification.json](integration-verification.json) for exact check and preservation bindings. The orchestrator did not switch, clean or stage the original checkout, and did not push or merge `main`. Final remote synchronization, integration and publication belong to the coordinating chat; this report does not claim those later steps are complete. The coordinating chat reported an interactive results view rendered in Chrome, verified lane switching and question expansion, and visually checked a screenshot. The local view is outside the repository and will be embedded by that chat.

## Time, usage and inspectable results

[results.json](results.json) contains the actual node, event, event-extension and candidate-edge payloads, per-lane next questions and provenance for the coordinating chat's interactive view. Counts are derived by comparing the assembled discovery JSON with the named base, using discovery IDs, event IDs and link values. It includes the measured interval from the orchestration branch creation reflog (22:51:08 UTC) to results generation; this excludes earlier setup and later root integration/presentation. Individual workers did not instrument reliable start times.

There were four researcher executions and four distinct reviewer executions. Newcomen required one minimal metadata correction and exact-byte rebind. No per-agent token meter or billing data was exposed, so token counts, API-equivalent costs and billing remain **null**, not estimates. These are observed task executions, not an API-call billing count.

Next research should focus on the unresolved original postface/chronology, actual prerequisite relationships, Newcomen's installation/count evidence, and Antikythera's chronology and transmission evidence. Similarity, temporal ordering and catalogue gaps remain questions rather than historical conclusions.
