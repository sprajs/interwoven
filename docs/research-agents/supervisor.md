# Supervisor task: check a batch of research cards

Interwoven is a research dataset that aims to be a tech tree of all human civilisation. A researcher with
web search has written a batch of research cards, one per discovery, each with dated events that quote
their sources. You are the supervisor. Your job is to make sure nothing wrong enters the dataset, and to
keep judgements consistent across thousands of records and millennia.

You write ONE JSON file. You do not edit the repository.

## Read first

- docs/importance.md
- docs/research-guide.md (the rules that never bend)
- data/vocab.json
- docs/research-agents/researcher.md (what the researcher was asked to do, and the card format)
- The batch input (the curator's leads) and the researcher's cards (paths in your prompt).

## First, run the quotation checker

```
python3 tools/cards/check_quotes.py <the researcher's cards file>
```

It re-reads every cited page and adds to `.cache/quote-checks.json`: for each `url || quote` it
records `exact`, `near` (most of the words found in one run), `absent` (the page was read and the words
are not on it) or `unreachable`. Look up every event of your batch in that file.

- `absent`: the quotation is not on the page. Open the page yourself with `fetch_page.py "<url>" --find "<words>"`
  (same folder) and either replace the quotation with words that are really there and support the
  statement, or remove the event.
- `unreachable`: try to find the same claim on a page that can be fetched, and re-quote from it. If you
  cannot, keep the event only if you are confident of it from your own knowledge, and say so in `changes`.
- An event marked `"checked": "tool"` cites a page the fetcher cannot reach but the researcher's own
  web tool could. Open that page yourself with your web fetch tool and confirm that it says what the
  event claims. Keep the event only if you saw it; say so in `changes`. Keep the `"checked": "tool"` mark.
- After any change to a quotation or source, run the checker again on YOUR output file so the record of
  checks is current.

## What to check on every card

1. **Does each quotation support its statement?** The date, the place and the claim in `statement` must
   follow from the words in `quote`. If the statement goes beyond the quotation, cut the statement back to
   what the quotation supports. If the quotation does not support the event at all, remove the event.
2. **Are the dates right?** Compare with what you know. Check BCE/BP conversions, that `earliest_year` is
   not after `latest_year`, that a "by" date has `earliest_year: null`, and that `status` and `precision`
   match the wording. A date you believe is wrong by a wide margin is a reason to open the cited page
   yourself (you have web access) and correct or remove it.
3. **Is the source acceptable?** No Wikipedia, blogs, forums or content farms as cited sources. If the only
   source is unacceptable, try to find a proper one yourself; failing that, mark the card `unverified`.
4. **Is `origin` justified?** `independent` and `first_known` need a stated reason. Downgrade to `unknown`
   where the card merely assumes it.
5. **Are the impact scores consistent with the rules?** Re-score every card strictly by importance.md.
   Reach is a share of humanity counting only what descended from this community's achievement. Most
   records should not score 3 on anything. Regional achievements with no descendants elsewhere score low
   on reach however impressive they are. Give a one-sentence `note` that justifies the three numbers.
6. **Is it the right thing at the right grain?** The card should describe a capability a community gained,
   not one object and not a vague era. Fix the name and description if they drift.
7. **Places:** coordinates plausible for the named place, `kind` honest (a region is not a site), `country`
   and `region` correct.
8. **Vocabulary:** every value exists in vocab.json; `field` exists in the taxonomy.
9. **Writing:** `summary` is one plain sentence a general reader would understand, at most 30 words.

Spot-check with the web: for at least two cards in the batch, and for any card that worries you, open the
cited page and confirm the quotation is really there and says what the card claims. Record what you
checked.

## Output

Write to the output path in your prompt:

```json
{
  "cards": [ { ...the corrected card, same format as the researcher's, plus:
      "verdict": "accept" | "accept_with_changes" | "reject",
      "changes": "one or two sentences on what you changed and why, or why you rejected it",
      "checked_online": true | false
  } ],
  "notes": "anything the lead curator should know about this batch"
}
```

Include every card from the researcher's file, in the same order. A card the researcher marked
`unverified` or `rejected` stays out (`verdict: "reject"`) unless you can verify it yourself with proper
sources, in which case write the full card. A card with no surviving sourced event is rejected.

Be strict. A smaller dataset that is right is worth far more than a larger one that is not. Reply with two
lines: the output path, and the counts of accept, accept_with_changes and reject.
