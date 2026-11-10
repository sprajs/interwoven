# Researcher task: verify and write up a batch of discoveries

Interwoven is a research dataset that aims to be a tech tree of all human civilisation. A curator has
listed capabilities that the dataset lacks, each as one community reaching one capability (for example
"Rice farming in the Yangtze basin"). You get a batch of these leads. For each one you use web search to
find reliable sources, establish what is actually known, and write a research card. A supervisor checks
your cards afterwards, and a script re-fetches every page you cite to confirm your quotations, so accuracy
matters far more than speed or completeness.

You write ONE JSON file. You do not edit the repository.

## Read first

- docs/importance.md (how impact is scored)
- data/vocab.json (allowed values for `event`, `origin`, `kind`,
  `advance`, `prompted_by`, `known_from`, `fate`, `link`, `place_kind`, `world_region`, `society_kind`,
  `date_status`, `date_precision`)
- Your batch input file (path in your prompt).

## The rules that never bend

1. **Never invent.** Not a date, not a place, not a person, not a quotation. If you cannot find it in a
   source you opened, leave it out. A card with one well-sourced event is a good card.
2. **Every event cites a page you actually saved, with an exact quotation from the saved text.** After a
   search finds a promising page, save it with the project's fetcher and read the saved text, not a
   summary of it:

   ```
   python3 tools/cards/fetch_page.py "<url>" --find "<a word or two you expect>"
   ```

   It prints where the text was saved and 600 characters around each match (`--show 0` prints the start
   of the page; raise the number to read further). If it says the page could not be fetched, do not cite
   that page: find another. Copy each quotation, 10 to 40 words, character for character from that
   output. Do not paraphrase inside `quote`, do not join separate sentences, do not fix spelling. A
   checker searches the same saved text for your words, and a quotation it cannot find sinks the event.
   The fetcher cannot reach every site (Science, PNAS, PubMed, Wiley and JSTOR often fail from it). When
   it fails for a page that your own web fetch tool CAN open, first look for a copy the fetcher can
   reach (PubMed Central at `https://pmc.ncbi.nlm.nih.gov/articles/PMC.../`, Nature, Scientific Reports,
   PLOS, eLife, a university repository, a museum or university page reporting the same result) and
   quote from that. If there is none, you may still cite the page you opened with your web fetch tool:
   copy the quotation as exactly as the tool shows it and add `"checked": "tool"` to that event. Such an
   event is admitted as unchecked and flagged for a person to verify, so use this only when the source is
   a strong one and nothing fetchable says the same. Use the `url` you actually read in `sources`.

3. **Use reliable sources.** In order of preference: peer-reviewed papers you can open (PubMed Central,
   PNAS, Nature, Science, PLOS, journals with open access), university and museum pages, UNESCO, national
   libraries and archives, Encyclopaedia Britannica, Smithsonian, reputable science journalism that quotes
   the researchers. **Do not cite Wikipedia**, but you may read it to find the sources it cites and then
   open those. Do not cite blogs, forums, AI-generated pages or content farms.
4. **Dates keep their uncertainty.** Archaeological dates are ranges and limits. Record what the source
   says: "c. 7000 BCE", "by 3200 BCE", "between 9000 and 8400 years ago". Convert "years ago / BP" to BCE
   by subtracting from 1950 (9000 BP is about 7050 BCE) and say so in the statement. Never narrow a range
   the source gives.
5. **Check the curator.** The lead's date, place and claim of independence are hints from memory. If the
   sources say otherwise, follow the sources and set `status` to `"revised"` with a note. If the capability
   did not exist there, was not independent as claimed, or you can find no reliable source after a real
   effort, set `status` to `"rejected"` or `"unverified"` and explain. That is a useful result.
6. **Independence needs a reason.** `origin: "independent"` only when a source says the community reached
   it without knowledge of others, or when contact was impossible. Otherwise `"unknown"`, or `"derived"`
   with the evidence of transmission.

## Output

Write to the output path in your prompt:

```json
{ "cards": [ { ...one per lead, in the same order... } ] }
```

Each card:

| Key | Value |
|---|---|
| `lead` | The lead's `title`, copied exactly. |
| `status` | `confirmed`, `revised`, `unverified` or `rejected`. |
| `note` | For revised, unverified or rejected: one or two sentences on what you found. Otherwise omit. |
| `name` | The record's name: the capability and the community or place. Short. |
| `summary` | One plain sentence, at most 30 words: what it was and why it mattered. |
| `description` | Two or three sentences saying exactly what was achieved, by whom and where, as the sources support. |
| `kind`, `field`, `concept` | From the lead, corrected if needed. |
| `origin` | `first_known`, `independent`, `derived`, `revival` or `unknown`. |
| `origin_note` | One sentence giving the evidence for that. |
| `impact` | `{ "reach": 0-3, "depth": 0-3, "generativity": 0-3, "note": "one sentence" }` scored by importance.md for THIS community's achievement. Start from the lead's scores and change them only with a reason. |
| `advance` | One to three values from vocabulary `advance`. |
| `prompted_by` | Values from `prompted_by`, only if a source says what prompted it. |
| `why` | One or two sentences on why it happened there and then, only if a source supports it. |
| `known_from` | Values from `known_from`: the kinds of evidence. |
| `fate` | A value from `fate`, if clear. |
| `places` | One to three places: `{ "name", "kind" (site, settlement, area, country, region or water), "lat", "lon", "country" (ISO 3166 two-letter code or null), "region" (world_region value), "within" (name of the enclosing country or region) }`. Use the most precise place the sources support: an excavation site if there is one, otherwise the region. Coordinates to two decimals for a site or town. |
| `people` | `{ "name", "born", "died", "role" }` with role from `person_role`. Only people the sources name. Years may be null. |
| `society` | `{ "name", "kind" }` with kind `polity`, `culture` or `people`: the society it happened within, if known. |
| `events` | One to four dated events, earliest first. See below. |
| `earliest_record` | The index (from 0) of the event that gives the earliest defensible date for this capability in this community. |
| `sources` | The pages you opened and cite: `{ "title", "authors": [..], "year", "url", "publisher", "access" }` with access `full-text`, `partial-text` or `abstract`. |
| `links` | Optional. Connections you found evidence for: `{ "type" (a `link` value), "to": "name of the other discovery", "statement": "one sentence", "source": index, "quote": "exact words" }`. Only with a quotation that supports the connection itself. |
| `open_questions` | Things a later researcher should settle. |

Each event:

```json
{
  "type": "archaeological_evidence",
  "label": "c. 7000 BCE",
  "earliest_year": -7400,
  "latest_year": -6600,
  "status": "approximate",
  "precision": "range",
  "statement": "Rice phytoliths with domestication traits at Shangshan are dated to about 9,400 years ago.",
  "place": "Shangshan",
  "source": 0,
  "quote": "exact words copied from the page",
  "locator": "Abstract"
}
```

- `type` is a value from vocabulary `event`.
- Years are integers, negative for BCE. `earliest_year` is null when the source gives only "by" a date.
  `status` is `known` (the source gives the date), `approximate` (about that date) or `bounded` (a limit or
  a range). `precision` is one of day, month, year, decade, century, millennium, range.
- `place` is the `name` of one of the card's places.
- `source` is an index into the card's `sources`.

For a rejected or unverified card give `lead`, `status` and `note` only.

## How to work

Take the leads one at a time. For each: run two or three searches (the lead suggests phrases), open the two
or three most reliable results, read the relevant part, and write the card from what you read. Copy
quotations directly from the fetched text while it is in front of you. Then move on. Do not spend more
than a few minutes on a lead that will not resolve: mark it unverified and say what you tried.

Before finishing, re-read your file: valid JSON, one card per lead, every event has a source index that
exists and a quotation, every vocabulary value is spelled exactly as in vocab.json.

Reply with two lines: the output path, and how many cards are confirmed, revised, unverified and rejected.
