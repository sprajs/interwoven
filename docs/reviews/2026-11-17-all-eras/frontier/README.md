# Record-level research frontier

[The queue](research-frontier.csv) has one row for every discovery at the dataset snapshot used in the round. It shows where to look for recorded prerequisites, descendants and open questions. Gaps measure catalogue coverage.

## Filter the queue

- Filter by `era`, `primary_region`, and `primary_domain`. `primary_field` gives the record's full taxonomy ID. Eras use the latest bound of the earliest-record event, as in the [coverage audit](../../../analysis/2026-11-17-tech-tree-gaps/report.md). Records without such an event are `undated`.
- `primary_region` uses a unique region for places marked `origin` when available. Otherwise it uses the sole recorded region, `multiple` when more than one region remains possible, or `unplaced` when no region is recorded at discovery level. The `regions` array retains all discovery-level region memberships used in coverage totals. Expand that array to count overlapping regions.
- Filter `established_connectivity` for `isolated`, `incoming_only`, `outgoing_only`, or `incoming_and_outgoing`. For records with no incoming edge, select `isolated` and `outgoing_only`. The four directional counts use established dependence and transmission only. Incoming means the link is stored on that row's discovery. Outgoing means another discovery's link points to it.
- Filter `candidate_links` or `insufficient_links` above zero to revisit recorded questions. Both ends of each stored link have a pointer, including links in the affinity and parallel layers with those statuses. To count unique questions across the full CSV, count their distinct pointers. The established pointers cover dependence and transmission.
- `missing_prerequisites_state` distinguishes `listed`, `empty`, and `absent`. The list preserves the recorded leads. `uncertainty_pointers` locates recorded unresolved questions, facets researched and marked `unknown`, record and event caveats, approximate or bounded event dates, event place notes, and provisional event types.

Array cells contain JSON. Read a pointer such as `data/discoveries/energy/example.json#/links/0` by opening the path before `#` and following the JSON Pointer after it. Array positions are zero based. Use the same dataset snapshot when opening pointers.

## Regenerate

From the repository root, validate the input checkout and run the exporter. `--data` accepts a checkout root or its `data/` directory and defaults to the exporter's own dataset. `--output` can be omitted to write to standard output.

```sh
python3 tools/validate.py
python3 tools/research_frontier.py --data . \
  --output docs/reviews/2026-11-17-all-eras/frontier/research-frontier.csv
```

Rows are sorted by era, primary region, primary domain, and discovery ID. The exporter assigns no research priority. `tools/tests/test_research_frontier.py` checks the queue against the coverage audit for the checked-out dataset.
