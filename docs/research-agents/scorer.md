# Scoring task: impact and grain for existing records

Interwoven is a research dataset that aims to be a tech tree of all human civilisation. Its 304 existing
records need two judgements added so that they can be compared with thousands of future records from every
era: the three impact scores, and the grain. You do not browse the web and you do not edit the repository.

## Read first

- docs/importance.md  (read it twice; it is the whole task)
- Your input file (path in your prompt): each record has its name, field, date, a summary, a precise
  description of exactly what the record stands for, its current tier (set earlier by a human review),
  and the later records that build on it.

## What to produce

One JSON file (path in your prompt): `{ "scores": [ { "id", "grain", "reach", "depth", "generativity", "note" } ] }`
with one entry per input record, in the same order.

- `grain`: `capability`, `improvement` or `instance`, by the definitions in importance.md. Many of these
  records are deliberately narrow: one experiment, one instrument, one site, one text. Those are instances.
  A record that stands for a community gaining a new ability is a capability.
- `reach`, `depth`, `generativity`: integers 0 to 3, by the tables and rules in importance.md.
- `note`: one sentence, at most 30 words, justifying the three numbers in plain words.

## How to judge

- **Score the record, not the famous topic around it.** "Joule's revised magnetocalorimeter" is one
  apparatus, not the conservation of energy. "Old Bess water-returning engine" is one engine. Read the
  description: it says exactly what the record stands for. A narrow instance of a great thing scores low.
- **Reach is a share of humanity,** counting only what descended from this achievement. A laboratory method
  used by one profession is 1. Something most people on Earth came to live with is 3.
- **When torn, take the lower score.** Expect most records in this dataset to total between 2 and 5.
  Scores of 3 are rare.
- **Be consistent across eras and regions.** A Bronze Age reservoir and a 1970s minicomputer are judged by
  the same tables.
- The current tier is a human judgement you should respect as evidence: tier 0 means later work across
  several fields or generations visibly depended on it. If your scores imply a very different tier (see the
  tier rule in importance.md), look again, but do not bend your scores to match: say so in the note.

Check before finishing: valid JSON, one entry per record, same ids, integers 0 to 3, grain valid.
Reply with two lines: the output path, and the distribution of grains and of totals.
