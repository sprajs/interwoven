# Unsupervised research cards, 10 November 2026

These are research cards from a second research wave that was stopped before any of it was checked. They are drafts. None of them is in the dataset.

| Folder | What it holds |
| --- | --- |
| `leads/` | The curated leads each batch was given: 19 batches, about six leads each |
| `cards/` | What a researcher with web search wrote for each lead: 111 cards |

Of the 111 cards, the researcher marked 18 as confirmed, 79 as revised (the sources disagreed with the lead's date, place or claim) and 14 as unverified. Batch 208 has leads and no cards.

## What has and has not been done

- A researcher found sources and copied quotations for each dated event, following `docs/research-agents/researcher.md`.
- No quotation has been re-checked against its page by machine.
- No supervisor has read any card. Dates, places, claims of independence and impact scores are the researcher's own.
- The leads behind these cards are still open in `data/leads.jsonl`.

## To finish them

Run `python3 tools/cards/check_quotes.py` on a cards file, give the leads and the cards to a supervisor with `docs/research-agents/supervisor.md`, and admit what the supervisor accepts with `python3 tools/cards/admit.py`. In the first wave the supervisors rejected 15 cards in 96 and changed every one they accepted, so treat these as leads with sources attached, not as findings.

Check each card against the dataset first. Another research effort was adding records at the same time, and some of these may now exist under another name.
