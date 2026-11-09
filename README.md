# Interwoven

An interactive chart of how science and technology build on one another, and the research behind it.

| Folder | What it holds |
| --- | --- |
| `research/science-technology-graph` | The research: entries, events, links and sources as JSONL, with the evidence, reviews and tools that maintain them |
| `web` | The chart. It reads the research and never writes to it |

```bash
git lfs install --local --skip-smudge
npm install
npm run dev
```

Install [Git LFS](https://git-lfs.com/) on each machine before running these commands. PDF, JPG and PNG research evidence uses LFS; the committed `.gitattributes` also covers future captures. Git stores their pointers and GitHub stores their contents under the same repository permissions. Text, graph data and review records stay in ordinary Git. LFS storage and downloads use the repository owner's GitHub allowance.

Evidence downloads are optional for application work. `--skip-smudge` leaves unfetched evidence as small pointer files. Fetch a needed document with `git lfs pull --include="research/science-technology-graph/evidence/acquired/NAME.pdf" --exclude=""`, or fetch the full collection with `git lfs pull --include="" --exclude=""` before running the full evidence-hash validator. For a new environment, use `GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none https://github.com/sprajs/big_idea.git` to also avoid eagerly downloading binaries retained in old Git history.

Then open http://localhost:5174. While the server runs, the chart rebuilds itself whenever the research changes.

Each folder has its own README, and `web/DESIGN.md` explains the chart's design. `AGENTS.md` has the working rules for this repository.
