# Agent instructions

These instructions apply to the whole repository.

## Read the project brief first

Every agent, including agents from other providers, must read [docs/project-brief.md](docs/project-brief.md) before work. We are building an evidence-backed tech tree of human civilisation, tracing prerequisites and supported reasons for where and when achievements emerged, including lost and abandoned branches. Use the current routing in [docs/research-agents/model-policy.json](docs/research-agents/model-policy.json): routine admission review is Terra High (`gpt-6.1-terra`, effort `high`). Keep original evidence, independent review and explicit uncertainty; never substitute a model silently.


## Authorised parallel research worktrees

The user has authorised an Astra Medium orchestrator (`gpt-6-astra`, effort `medium`) with Terra High workers (`gpt-6.1-terra`, effort `high`). Give concurrent writing lanes separate Git worktrees on `codex/` branches, created from a named current committed snapshot. This is the explicit exception to main-only work below. Each worker reads this file and the project brief, owns named paths, records its actual model, and hands a reviewed commit to the orchestrator; workers do not push or merge. Use a separate reviewer execution, and do not let researchers approve their own changes. The coordinating chat owns final integration on `main`, required checks and direct push. Do not switch or clean another agent's worktree, and preserve uncommitted work in the main checkout.

## Keep main current and push directly

This project is used from multiple machines. Other machines and agents may push
to `main` at any time. Never assume the local checkout is current.

- At the start of every task, inspect `git status --short --branch`, fetch
  `origin`, and pull the latest `origin/main` before relying on the code or
  making changes. Work on `main`; when the checkout is clean, use
  `git switch main` followed by `git pull --ff-only origin main`.
- Preserve existing work before switching branches or pulling. Do not discard,
  overwrite, or silently include someone else's changes. If synchronization
  needs conflict resolution, resolve it while preserving the intended changes;
  ask only when the correct resolution needs the user's decision.
- Commit and push completed, validated changes directly to `main`. Do not create
  pull requests or feature branches unless the user explicitly asks for them.
  The user's standing preference authorizes routine commits and direct pushes;
  do not ask for confirmation each time. Read-only tasks need no commit.
- Immediately before pushing, fetch `origin` again. If `origin/main` advanced,
  rebase your unpublished commits onto it and rerun the checks affected by the
  combined changes. Stage only the files belonging to the task.
- Push with `git push origin main`. If another machine wins the race and the
  push is rejected, fetch, rebase, check, and retry. Never force-push or reset
  remote history to get a push through.
- Verify the push succeeded and report the commit and relevant validation.
  If network access or permissions prevent syncing or publishing, say so
  explicitly; do not claim the checkout is current or the work is pushed.

## The dataset

- `docs/data-model.md` defines the records and `docs/research-guide.md` says how
  to add to them. Read both before changing anything in `data/`.
- Everything people have discovered or invented belongs, in every field, and an
  achievement does not have to be a world first. Independent reinventions and
  regional achievements get records of their own, with their `origin` stated.
- Never invent a date, place, person or link. Leave the facet out. Every facet
  that has a value records where it came from in `research.basis`; mark anything
  entered from general knowledge as `recalled`.
- Run `python3 tools/validate.py` before committing data, and `npm test` before
  committing code. Both must pass.
- One discovery and one source per file, so several agents can work at once.
  Stage only your own files.

## Simulations: efficient Rust

- Implement all simulations and their numerical kernels in Rust, including
  Monte Carlo sampling, numerical integration, and experiment execution.
  Python may launch compiled Rust programs and read their outputs, but must
  not implement the simulations itself.
- Optimize for execution speed, throughput, and memory efficiency. Prefer
  efficient algorithms and data layouts, avoid unnecessary allocations and
  copies, and use parallelism or vectorization when measurements justify it.
- Run simulations and measure performance with optimized release builds:
  `cargo run --release`, `cargo build --release`, or an appropriate benchmark
  profile. Debug builds are for diagnosis, not production runs or performance
  claims. Do not favor ease of debugging over simulation efficiency.
- Preserve numerical correctness and reproducibility while optimizing. Use
  meaningful correctness checks and representative release benchmarks; record
  seeds, parameters, build settings, and hardware when they affect results.
  Document numerical or machine-specific optimization tradeoffs.

## Analysis and persistent visualizations: Python

- Use Python for data analysis, post-processing, and persistent visualizations.
  Keep reusable Python scripts or notebooks and their dependencies in the repo
  so saved results and figures can be regenerated on another machine.
- Have Rust write structured outputs that Python can consume. Keep simulation
  logic in Rust rather than duplicating it in Python or browser code.
- The tools in `tools/` are Python with no dependencies beyond the standard
  library. `tools/build.py` compiles `data/` for the app, which does no research
  logic of its own.
- Save useful plots, analysis results, and the metadata needed to trace them
  back to the input data, simulation configuration, and source commit. Label
  axes and units and distinguish measured results from illustrative examples.

## Make the work visible in the chat

- Use the app's native artifacts and dynamic features proactively as a default
  part of project chats. Do not wait for the user to request them separately.
- For substantive research, simulations, and analysis, include a useful rendered
  artifact and an interactive view when the current app supports them. Use
  controls, selectable comparisons, drill-downs, or explorable plots to help the
  user understand the actual results. Do not deliver only a wall of prose or
  file paths when the app can display the work directly.
- Use Python for persistent analyses and figures, and the available in-chat
  visualization tools for interactive presentation. Presentation glue may
  explore Rust-produced results; it must not become a second simulation engine.
- For code or documentation changes, show the native diff or review artifact
  when available. Choose features that make the current task easier to inspect;
  do not invent data or add an unrelated visualization just for decoration.
- Verify that artifacts render and their important interactions work. Include
  usable links or previews in the final response. If the current environment
  lacks the needed app features, explain that limitation and provide the best
  available saved artifact or static preview instead of claiming an interactive
  result exists.
