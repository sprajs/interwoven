# Researching in batches with agents

These are the briefs for the four roles used to grow the dataset quickly without lowering its standard. Each is written to be handed to an agent as it stands.

| Role | Brief | Reads | Writes |
| --- | --- | --- | --- |
| Curator | `curator.md` | One slice of the taxonomy and what it already holds | A list of capabilities and of each community that reached them, with impact scores |
| Researcher | `researcher.md` | A batch of about six leads | One research card per lead: dated events, each with an exact quotation from a saved page |
| Supervisor | `supervisor.md` | The leads and the cards | The corrected cards with a verdict on each |
| Scorer | `scorer.md` | Existing records | Impact scores and grain |

The curator and the scorer work from knowledge and need a strong model. The researcher needs web search and can be a small, fast model, because every quotation it gives is checked by machine and every card by the supervisor. The supervisor needs a strong model.

## The steps

1. A curator lists what a slice lacks. Check the list against the dataset for things that now exist under another name.
2. Split the leads into batches of about six and give each to a researcher. The researcher saves each page with `tools/cards/fetch_page.py` and copies quotations from the saved text.
3. `python3 tools/cards/check_quotes.py <cards.json>` re-reads every cited page and records whether each quotation is on it.
4. A supervisor checks each batch against the rules in `docs/research-guide.md` and `docs/importance.md`, and rejects what cannot be supported.
5. `python3 tools/cards/admit.py <verified.json> --apply` turns accepted cards into records, sources, places and people, and saves the passage around each checked quotation under `evidence/`. A record whose every quotation was found is marked `sourced`; otherwise it is a `draft`.
6. `python3 tools/validate.py` must pass before a commit.

Coordinates, impact scores and the society a record belongs to come from the agents' own knowledge and are marked `recalled`.
