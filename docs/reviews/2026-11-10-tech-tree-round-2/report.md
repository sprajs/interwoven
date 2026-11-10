# Research round 2: constituent relationships and supported context

The round admits **one established functional process relationship**, a minimal process record needed to represent it, **one reported funding facet**, and **one explicitly attributed refinement of an existing explanation**. A proposed Newcomen-to-Watt development relationship remains a candidate. The astronomy proposal was removed after review; that lane retains its original sources and precise research questions, with no discovery or event additions.

This is limited graph and explanatory progress. It does not establish a complete account of why these technologies emerged in these places and periods, and it does not demonstrate a general efficiency advantage for this research method.

## Accepted changes and evidence boundaries

| Lane | Retained result | What remains unknown |
| --- | --- | --- |
| Chinese high-fired ceramics | A `uses_process` relationship from wood-ash glazing at Deqing to the sampled proto-porcelain, supported by Yin's archaeometric reconstruction. One minimal process record and its archaeological event are necessary to represent the relationship. | Exact ash preparation, origins and distribution beyond the analysed production-site samples. This is not a transmission claim or a universal requirement for proto-porcelain. |
| Korean printing | The 1378 woodblock Jikji receives `funding: community`, representing lay donations reported in the 2001 UNESCO nomination. | Donor identities, amounts, a contemporary transaction record, the cause of the edition, and any direct use of the 1377 edition. No casting method or prerequisite edge was admitted. |
| Steam engines | The existing Watt `why` text is now explicitly attributed to later recollections and historical accounts. A sourced `candidate` asks about the model's role in development. | Independently informative corroboration of the historical development path. Existing motivation, setting and bottleneck categories remain recalled. |
| Hellenistic geared astronomy | Two original studies and their source metadata are retained; the proposed generic calendar node and edge are removed. | The Miletos inscription does not identify the particular community achievement used by the mechanism. A dial is part of a physical device, not part of the existing broad gearing-capability record. |

The accepted ceramics statement is deliberately narrow. Yin lists **12 collected Nanshan sherds**, but tabulates glaze analyses for **four**: NS-1, NS-4, NS-8 and NS-11. The edge describes the study's interpretation of analysed Deqing wares, not every Shang vessel. Relevant thesis passages are pp. 73–75, 132–135, 138–143 and Appendix 3, Table A 3.1, p. 271. The thesis and the related article share research and are not independent corroborations.

The printing addition makes an already cited report searchable as a funding facet. Review removed a proposed funder contribution from an archaeological-evidence event: a production role must not be assigned to the stage at which surviving evidence is recorded. The edition's limited-output explanation remains a question, not an established causal link.

The steam review distinguishes three sources' evidentiary roles. Glasgow's account invokes Watt's retrospective recollection; Smiles recounts the same historical lineage. Russell independently explains the thermal mechanism but does not independently corroborate that development sequence. The `why` text is accepted as an **attributed account**, not a confirmed causal explanation. Under the existing `FACET_FOLLOWS` rule, `why` inherits the still-`recalled` `prompted_by` basis. The round therefore adds one sourced funding facet and one reviewed narrative refinement, not two newly sourced categorical explanations.

The astronomy review found a record-grain problem as well as a transmission gap. A nineteen-year cycle attested at Miletos and the mechanism's 235-month dial do not by themselves support an edge between these particular community achievements. A second proposal to represent the coeval dial as a component was also withheld: the existing destination is the broad gearing capability, not a correctly scoped whole-device record. This round did not add an unrelated event simply to increase its yield. The existing Babylonian candidate remains unchanged, and no loss is inferred from absent descendants.

## Models, isolation and independent review

All four research worktrees began at fetched `origin/main` snapshot **`c902638823f0eea5d3e7b97a34d4a7880bf2acb8`**. The coordinating chat verified this chat's runtime as **`gpt-6-astra`, effort `medium`** before dispatch. Round 2 was coordinated directly here, without an additional Astra relay. Four fresh researcher executions and four distinct reviewer executions were explicitly spawned as **`gpt-6.1-terra`, effort `high`, `fork_turns: none`**. At most four research lanes ran concurrently.

Each writer owned a separate `codex/tech-tree-round-2-<lane>` branch under `/Users/szymon/.codex/worktrees/tech-tree-round-2/`. Additional ceramics record/source ownership was reserved before editing. Reviewers read fixed commits and original retained evidence, wrote only their assigned review artifact, and did not approve their own research.

| Lane | Final independently reviewed worker commit | Accepted snapshot integration commit |
| --- | --- | --- |
| Ceramics | `e1c875f59f30f18e9e3cfe68d441d88fa8a46d35` | `1f964f12a2d4432496b47b88cdc483ebad4e05e9` |
| Printing | `91569f78e1d1ec252bbaba5a77a8d1954b2f915f` | `554e98ceb1cbedf8f762501bf412885dad2ff931` |
| Steam | `557bebbb703a885244333e9108a9364417d8694c` | `1c56636cc1428e7c7ace1e526b5553e5e991f409` |
| Astronomy | `30e094631ab5f0323070248908736c232ae141f1` | `e0fbb126f822d02bce4e82a3992efa5a40e2ec3d` |

Only each **final accepted base-to-worker patch** was applied to the orchestration branch. Rejected intermediate data changes were not replayed into it. Worker history and review revision history preserve those earlier proposals. The [review manifests](reviews/) bind original-source locators, retained claims, scope decisions and exact file hashes. These are direct dataset-patch semantic reviews; the separate `tools/cards` pipeline was not run and no card-gate success is claimed. Proposal-time manifests remain immutable; subsequent review decisions live separately.

## Validation, source retention and preservation

- Dataset validation passed: 889 discoveries, 1,474 events, 235 stored links and 1,596 source records.
- `npm test` passed: 169 Python tests, including four renderer-boundary tests, and 53 Vitest tests.
- Data compilation passed: `e2e94cc27350acdcf58ca5ce`, with 203 visible established links.
- Production TypeScript/Vite build passed; the existing large-chunk warning remains nonblocking.
- Exact review-bound files and original-source bytes were checked after assembly; see [integration-verification.json](integration-verification.json).
- All 92 original unfinished files still match the supplied preservation manifest. No changed path overlaps them. Round-1 outputs, setup files, shared registers and app UI remain unchanged.

The original checkout was never switched, cleaned or staged. Source reading there was read-only. The new raw Glasgow HTML is committed unchanged, including its upstream whitespace. The three original PDFs used for the new ceramic/astronomy source work are retained in the orchestration worktree at the paths listed in `integration-verification.json`, with committed checksum/retrieval descriptors. The existing UNESCO PDF was also copied read-only into the orchestration cache and verified. These ignored binaries do not travel with a cherry-pick: the final integrator should copy those exact local files or retrieve and verify them through their descriptors.

Three source records are new (Glasgow and two Jones studies); the existing Yin source record is extended. Reused passages were not duplicated into new bibliographic records. Different publications by the same author or based on the same historical recollection are not counted automatically as independent evidence.

## Inspectable results and reproduction

[results.json](results.json) separates `accepted_established_edges`, `unresolved_edges`, and `supported_circumstances`, and includes original locators, qualifications, node/event payloads, source metadata and the next research frontier. Counts compare the accepted assembled dataset with the named base. The existing candidate astronomy relationship is not counted as new.

The persistent [interactive view](view.html) is generated with the standard-library renderer:

```sh
python3 tools/render_research_round.py docs/reviews/2026-11-10-tech-tree-round-2/results.json docs/reviews/2026-11-10-tech-tree-round-2/view.html
```

Add `--fragment` and a separate output path for an in-chat rendering. Lane switching, expandable source passages and candidate exclusion were checked in Chrome; the ceramics diagram was visually checked at normal width and 320 pixels. Each accepted edge's scope and caveats remain visible beside its diagram, outside collapsed evidence details; the final Deqing qualifiers were inspected after regeneration. Only accepted established relations are drawn. The renderer rejects candidate edges misclassified into the established array and escapes source text/links. The native review panel can compare this branch with the base commit.

Elapsed time is recorded from worktree creation at **23:29:46 UTC on 10 November 2026**, excluding earlier round preparation. Four researcher and four reviewer executions were used, with corrections and rereads in those separate executions. Exact token usage, API-equivalent cost and billing were not exposed and remain unknown. No broad model benchmark was run.

The next useful work is precise: independent archaeometric testing and process distribution at Deqing; original edition and funding records for Jikji; contemporary evidence for Watt's development sequence; and an editorial/source-backed definition of the Antikythera device and its components before adding physical-component relations. No source gap was filled by an illustrative historical story.

This branch is a reviewed handoff. It has **not been pushed or merged into `main`**. Final synchronization, integration and publication belong to the coordinating chat. [changed-paths.json](changed-paths.json) lists the exact paths belonging to this round.
