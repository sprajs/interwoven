# Regenerate the prehistory report

Validate the integrated discovery data first. Use the commit containing the reviewed files as `AFTER`. The exporter checks each review's SHA-256 values against that commit and applies only those files to the baseline projection. Later changes in unrelated files stay outside the comparison.

```sh
python3 tools/validate.py
report_dir=docs/reviews/2026-11-17-prehistory
python3 tools/prehistory_wave.py \
  --base 71326e01a105da21decb1587195a81bd5b596b8c --after AFTER \
  --roster "$report_dir/roster.json" --lanes "$report_dir/lanes" \
  --reviews "$report_dir/reviews" --output "$report_dir" --png
```

The exporter uses Python's standard library. `--png` uses `rsvg-convert` from librsvg. Omit it to regenerate the SVG and the other results without librsvg. Open `view.html` to filter the roster and inspect primary-source locators, independent verdicts, and follow-up questions. `prehistory-wave.html` is the conversation fragment. `results.json` preserves exact event-scoped changes alongside changes by direction and link type. It also records separate node additions and deletions and the net event change.
