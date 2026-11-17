# Regenerate the prehistory report

Validate the integrated discovery data first. The completed review covers the data at `f6005ca2a29db51d9b4ccb67a74e3784f4fa54f9`. The exporter checks each review's SHA-256 values against that commit and applies only those files to the baseline projection. Later changes in unrelated files stay outside the comparison.

```sh
python3 tools/validate.py
report_dir=docs/reviews/2026-11-17-prehistory
python3 tools/prehistory_wave.py \
  --base 71326e01a105da21decb1587195a81bd5b596b8c --after f6005ca2a29db51d9b4ccb67a74e3784f4fa54f9 \
  --roster "$report_dir/roster.json" --lanes "$report_dir/lanes" \
  --reviews "$report_dir/reviews" --output "$report_dir" --png
```

The exporter uses Python's standard library. `--png` uses `rsvg-convert` from librsvg. Omit it to regenerate the SVG and the other results without librsvg. Open `view.html` to filter the roster by graph outcome and inspect primary-source locators, independent verdicts, and follow-up questions. Graph outcomes reflect the strongest recorded dependence or transmission status at either end of each anchor. `prehistory-wave.html` is the conversation fragment. `results.json` preserves the researcher's assessment and the derived graph outcome, as well as exact event-scoped changes alongside changes by direction and link type. It also records separate node additions and deletions and the net event change.

Twelve GPT-6.2 Sol High researchers owned the 90 anchor decisions. A further Sol High researcher checked possible transmission across those assignments. Twelve separate Terra High reviewers checked the original sources and the final proposals, coordinated by Astra Medium. The integration check matched all 282 per-lane hashes, covering 278 distinct files because two source-and-evidence pairs were shared. The source records count each shared work once. The review window ran from approximately 21:38 to 22:08 UTC on 17 November 2026. Per-agent token usage and billing were unavailable. [Exact worker and reviewer commits](review-manifest.json)
