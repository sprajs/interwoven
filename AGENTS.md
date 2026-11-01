# Agent instructions

These instructions apply to the whole repository.

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
