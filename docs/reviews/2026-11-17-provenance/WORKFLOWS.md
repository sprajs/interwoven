# Reuse an original-source workflow

Run the commands from the repository root with Python 3.

```sh
python3 tools/provenance.py list
python3 tools/provenance.py show metrology
python3 tools/provenance.py start metrology --subject 'The instrument or standard to investigate' > worksheet.md
```

`list` prints the eight workflow IDs and their worked-example titles. `show` displays transferable steps, required inputs and criteria for rejecting or stopping the investigation. `start` gives the new subject a blank set of findings and source locators. Fill in both ends of the proposed relationship before drawing a conclusion. Record what each original document supports, what would distinguish a competing explanation, and whether corroborating documents come from a separate source lineage.

## Inspect the source evidence

Open [the evidence reader](view.html). Select one of the two artifact traces or eight worked examples, then select a step to open the source and its locator. The case overview shows the decision, the remaining test, and the independent review. A review can accept a finding that a relationship remains unresolved.

Regenerate from the reviewed integration revision containing the accepted ledgers and receipts.

```sh
python3 tools/provenance.py --snapshot b7bf3c66542faff7b3ed52ed5602b27d08839077 render \
  --output docs/reviews/2026-11-17-provenance
```

`view.html` opens without a server. `provenance-reader.html` is the conversation fragment. Both include the source locators and receipt details and make no network requests until a reader opens a source link.

`--snapshot` defaults to `HEAD`. Each command checks the selected ledger bytes against the accepted Terra High receipt. The worksheet commands can use a later checkout even when the catalogue has since changed. `render` checks the other reviewed bytes at each original proposal commit when its Git object is available. If it is unavailable, `render` checks the selected revision. To regenerate from a later revision with changes to a pilot record and without the original worker commits, supply `render --historical REVIEWED_REVISION` with the accepted integration snapshot. The reader shows the revision used to verify the historical bytes. Use the reviewed integration revision as `--snapshot` to regenerate a published reader independent of subsequent catalogue edits.
