# Paused batch-12 finalization

All 92 paused original files and 26 handoff files are preserved byte-for-byte in the committed archive. Independently reviewed repairs admit 13 new records and extend 8 existing records. This closes the paused batch; it does not start a growth campaign. Final integration and push belong to the coordinating chat. Main and the older-worktree archive were not edited here.

## Dispositions and resulting dataset

| Original-file disposition | Files |
| --- | ---: |
| Admitted with original bytes | 47 |
| Admitted after bounded repairs | 26 |
| Archived only | 19 |
| Total originals preserved | 92 |

Every original is archived, including the originals of repaired files. The [disposition manifest](../../research-drafts/paused-batch12-2026-11-11/disposition-manifest.json) maps each path to its original hash, archive, final hash, reason, claim ledger and independent review. Archive-scoped `.gitattributes` disables text conversion to preserve original bytes across platforms.

The combined dataset has 902 discoveries, 1,496 events, 237 stored links and 1,622 sources. Changes from the named base are 13 discoveries, 22 events, 2 candidate links and 26 sources. No established links were added. There are 23 approved register additions: 10 concepts, 7 people, 4 places and 2 organizations. Existing register rows are unchanged. Leads remain unchanged.

## Review outcomes

- **Making and food:** seven new records retained after scope corrections. The 1817 Kumase evidence supports foot-loom observation; a separate adinkra cotton-strip description was not transferred into that dated event. Te Takinga catalogue dates remain 1845–1855. Engaruka's irrigated area remains greater than 1,000 hectares, not an exact 1,000. Moche's excavated-area statement and Te Takinga location were bounded to the sources.
- **Transport and institutions:** four new records and the Venice extension retained. The 1939 Grand Portage canoe caption documents completion, not practical use. Lamu remains a museum-model instance; unsupported broad vessel claims and two associated sources were deferred. Venice's 75% is explicitly derived from three quarters. The 1587 Bosnian register was not established as evidence for this Sarajevo record, so the Sarajevo extension was archived and its active base restored.
- **Information:** Good and Golay records and the Cooley–Tukey extension retained. Good's 1958 evidence is a publisher summary; the unavailable 1960 addendum is archived only. Good–Cooley and Shannon–Golay links remain candidates. Michels distinguishes the FFT's IRIS implementation from its separate discussion of Cooley's FORTRAN program. Recalled fired-clay and Bessemer impact/grain extensions were archived and their active bases restored.
- **Access:** six existing records extended, with duplicate source IDs consolidated into existing sources. QLoRA's training capability is not represented as an observed run. ChatGPT Plus is scoped to the historical 2023 launch. Llama 2 uses the immutable original 2023 licence. CTSS documentary dates are not first-use claims, and MOSIS's preexisting draft status remains.

The 19 archive-only original paths include three discovery extensions and eight source/note pairs. Some source content was available only through a rendered page or summary; some original bytes remain unavailable. The lane ledgers and independent reviews retain these limitations. Admission does not remove those caveats or establish broad priority, continuity or transmission claims.

## Provenance and evidence retention

Named base: `46b68706bd48a423e9c2374780ba1b1acf2ebc68`.

Original archive commit: `73e38ede69b0bfe34abea7556cc1401019a58c35`.

Assembled reviewed data commit: `31546f15aca1aec8bc5ce662cb823ba264d21732`.

| Lane | Final independently reviewed worker commit |
| --- | --- |
| Making and food | `cdb358d599b234176dfe143f54f2359aa7e3fe74` |
| Transport and institutions | `4cd3479a65e64d2e29cdabfd388ffef11bce0a78` |
| Information | `8728f9fb9bbe61626c4581c4cbadcd6dd0602eac` |
| Access | `a4f85012d3ceab5f8872c66fa58c0ac6f371f5fe` |

The coordinating chat verified Astra Medium orchestration. Four Terra High repair executions and four separate Terra High reviewer executions are recorded in [results.json](results.json), with the original reviewer reports in `reviews/` and researcher ledgers in `lanes/`. Token usage and billing were not exposed and are not estimated.

The [raw-evidence retention manifest](raw-evidence-retention.json) lists 29 verified local files totaling 70,247,472 bytes, with exact absolute source/cache paths, hashes and provenance. These ignored bytes do not travel with Git: the integrating chat must copy them to the corresponding relative cache paths and verify hashes. External originals are also retained. The committed original Llama 2 licence has SHA-256 `8c17c2ebb0ea011be9981cc3922db8ca8fa61e828c5d3f44cb6ae342bf80460b`; its upstream trailing whitespace is intentionally preserved.

## Validation and integration handoff

[Integration verification](integration-verification.json) records successful checks of all 92 committed original blobs, all 26 committed handoffs, all 92 active dispositions, all 29 local evidence files, all reviewed nonregister hashes and all 23 canonical register-row hashes. All 92 original files in main still match the initial snapshot.

- `python3 tools/validate.py` passed.
- `npm test` passed: 169 Python tests and 53 Vitest tests.
- `python3 tools/build.py` passed, producing dataset hash `c48d316b89e6978b4276d15f` and 203 visible established links.
- `npm run build` passed; the existing bundle-size warning is nonblocking.

The final metadata commit changes documentation only. [changed-paths.json](changed-paths.json) enumerates the complete branch scope relative to the named base. The branch is `codex/finalize-batch12-integration` in `/Users/szymon/.codex/worktrees/commit-all-20261111/integration`.

The coordinating chat can reconcile main's 92 originals against the committed archive before integration, copy the 29 ignored evidence files using the retention manifest, and perform the required latest-main synchronization and push. No push is claimed by this handoff. The separate older-worktree archival task remains owned by that chat.
