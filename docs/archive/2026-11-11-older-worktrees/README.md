# Preserved older worktrees

Archived on 11 November 2026 at the user's request to commit and push all pending work, including older worktrees. These are historical working materials, not newly accepted dataset entries or a replacement for the current app.

- `technology-adoption-audit/` preserves all 1,190 files from the detached audit worktree, including its frozen review snapshots and original source files.
- `science-technology-graph-independent-review/` preserves the ten files added by unpublished commit `1bdf2313e1e80d5ba80fa541a376d7de8cca1a8d`.
- `unpublished-worktree-commits.bundle` preserves the 13 local branch histories not reachable from the published main snapshot. It also includes the paused-batch repair workers. It includes superseded proposals as well as accepted work; inclusion does not approve those proposals.
- `technology-science-tree.bundle` preserves the separate prototype repository. Its working directory contained only Git metadata, with all nine tracked content files absent. The archive records that state without applying those deletions or restoring files in the original worktree.

`MANIFEST.json` records original paths, commit IDs, file sizes, SHA-256 hashes, bundle prerequisites and the prototype's working-directory status. The original worktrees remain in place and unchanged. Archived reports retain their historical absolute links and conclusions; those links may need their original path prefix replaced with the corresponding archive location on another machine.

The prototype bundle is self-contained:

```sh
git clone /path/to/technology-science-tree.bundle /path/to/restored-prototype
```

The unpublished-worktree bundle requires the ancestors already included in the main repository, through `31546f15aca1aec8bc5ce662cb823ba264d21732`. In a clone of this repository, inspect it without changing the working tree:

```sh
git bundle verify docs/archive/2026-11-11-older-worktrees/unpublished-worktree-commits.bundle
git bundle list-heads docs/archive/2026-11-11-older-worktrees/unpublished-worktree-commits.bundle
```

Fetch a selected branch into a separate archive ref if its original history is needed. Do not merge archived proposals into the current dataset without the current review and validation gates.

During final integration, 40 numbered duplicate files appeared under `data/` and `evidence/`. All matched the original batch-12 draft hashes. Their exact bytes and filenames are preserved in `late-numbered-duplicates/`, outside the active dataset; the cause was not established.
