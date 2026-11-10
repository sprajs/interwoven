# Curator task: the backbone of capabilities for one part of the tech tree

Interwoven is a research dataset that aims to become a tech tree of all human civilisation: every
discovery and invention, in every field, anywhere, from the first stone tools to today, with how each
connects to the others. It has 304 records so far, built from a narrow earlier project, so its coverage is
patchy: strong on steam engines, semiconductors and DNA sequencing, almost empty on farming, medicine,
building, textiles, ships, music, money, and on everything outside Europe and North America.

You are the curator for one slice of the subject taxonomy. Your job is to decide WHAT SHOULD BE IN THE TREE
for your slice: the capabilities humanity acquired, and every place that acquired each one. Researchers
with web access will then verify and write up each item you list, so your list sets the shape of the
dataset for years. Taste matters more than volume. You do not browse the web. You do not edit the repository.

## Read first

- docs/data-model.md (what a record is; origin and concept)
- docs/importance.md (the three impact scores, tier, grain, and what makes a good next record)
- data/vocab.json (the `origin`, `kind` and `world_region` lists)
- Your input file (path in your prompt): the domains and fields you own, the records that already exist in
  them, and the concepts already defined.

## What to produce

One JSON file (path in your prompt):

```json
{
  "concepts": [ { "id": "rice-farming", "name": "Rice farming", "field": "food.crops", "summary": "One sentence defining the capability." } ],
  "origins": [
    {
      "concept": "rice-farming",
      "title": "Rice farming in the Yangtze basin",
      "kind": "practice",
      "field": "food.crops",
      "where": "Lower and middle Yangtze, China",
      "region": "asia",
      "date": "c. 7000 BCE",
      "year": -7000,
      "origin": "first_known",
      "impact": { "reach": 3, "depth": 3, "generativity": 2 },
      "why": "One sentence on what followed from it.",
      "verify": "What a researcher must pin down: the earliest secure dated evidence and its site, and whether domestication here was independent of other centres.",
      "search": ["rice domestication Yangtze earliest evidence Shangshan", "Oryza sativa domestication archaeology date"]
    }
  ]
}
```

- A **concept** is a general capability: something a community could newly do or understand. Give it the
  single best `field` from your slice. Reuse an existing concept id when one fits.
- An **origin** is one community reaching that capability: one future record. The same concept usually has
  several origins. List each place that reached it INDEPENDENTLY (`origin: "independent"`, or
  `"first_known"` for the earliest known anywhere), and also the few transmissions that mattered
  enough to follow on their own because the receiving society changed the thing or built far on it
  (`origin: "derived"`). Use `"unknown"` when scholars genuinely dispute independence.
- `title` names the future record: the capability plus the community or place. Not a person's name unless
  the achievement is inseparable from one person.
- `kind`: technology, science, mathematics or practice (see vocab).
- `year` is your best single year for sorting (negative for BCE); `date` is how a careful reader would write
  it. These are hints for the researcher, who will replace them with sourced dates. If the dating is
  contested say so in `verify`.
- `impact`: score this origin's own consequences by the rules in importance.md. Be strict and consistent:
  most entries should not be 3-3-3. Score the Mesoamerican invention separately from the Eurasian one.
- `search`: two or three web search phrases that would find a reliable source.

## What to choose

1. **Capabilities first** (`grain: capability` is assumed for everything you list). Not instances, not
   famous individual objects, not minor improvements. Ask of each field in your slice: what are the 5 to 15
   things people became able to do here that mattered most, across the whole of history?
2. **Every era.** Deep prehistory, the first cities, classical and medieval societies everywhere, the early
   modern world, the industrial era, the twentieth century and the present. A field's list that starts in
   1700 is wrong. A field's list that stops in 1900 is also wrong.
3. **Every region.** For each capability ask who else reached it: East Asia, South Asia, Southwest Asia,
   Africa, Europe, Mesoamerica, the Andes, North America, Oceania and the Pacific. Independent origins in
   the Americas, Africa and Oceania are the dataset's biggest gap. Do not pad: only list an origin you are
   confident happened.
4. **Consequence over fame.** Prefer what changed how many people lived over what is well known.
5. **No duplicates.** Do not list anything already in `existing_records` (check names and meaning, not
   just ids). You may list a further origin of a concept that has a record.
6. **Everyday life counts.** Bread, beer, soap, the loom, the plough, the saddle, the sewer, the school,
   the drum, the ball game.

Aim for 40 to 60 origins across your slice, spread across its fields in proportion to how much happened in
each, covering roughly 20 to 30 concepts. Quality and balance matter more than hitting a number.

## Checks before you finish

Run a short Python check: valid JSON; every origin's `concept` is in your `concepts` or in the input's
`existing_concepts`; every `field` exists in the taxonomy and belongs to your slice; `origin`, `kind` and
`region` are valid vocabulary values; impact scores are integers 0 to 3; no two origins share a title.
Then print a small table of how many origins you have per field, per region and per era (before 3000 BCE,
3000 BCE to 500 CE, 500 to 1500, 1500 to 1800, 1800 to 1950, after 1950) and rebalance if any is badly
neglected without good reason.

Reply with two or three lines: the output path, the counts by region and era, and anything you were unsure
whether to include.
