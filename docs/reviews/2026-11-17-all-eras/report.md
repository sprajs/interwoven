# Research across the six eras

Fourteen investigations began from `612d88b`. They added **four discoveries and 18 dated events**, revised **22 existing events**, and added **50 source records**. The 24 discovery records touched by the round span all six dated eras. The combined data snapshot is `1537d299f2d0a6b4d121e8d5fb9f17467e067a08`. [Explore the investigations and their evidence](view.html) · [Record-level research queue](frontier/README.md)

## Two relationships entered the established graph

- **Lightweight volcanic aggregate → the Pantheon dome.** The 1929–1934 restoration provided first-hand observations of alternating tuff and light volcanic scoria in the upper dome. Comparison with other vaults in Rome documents the wider practice. The path by which the Pantheon builders learned it remains open. [Building review](reviews/building.json) · [Terenzio’s restoration account](https://www.treccani.it/enciclopedia/pantheon_%28Enciclopedia-Italiana%29/)
- **Jacquard card control → Babbage’s Analytical Engine design.** Successive punched cards selected actions in the loom. Babbage adapted that principle into separate operation and variable cards for his proposed engine. The original drawing, the attributed account and archival studies support the adaptation. The date when Babbage first encountered the method remains unresolved. [Textiles review](reviews/textiles.json) · [Design record](../../../data/discoveries/electronics/babbage-analytical-engine-punched-card-design.json)

## Findings by era

Eras in the count column follow the latest bound of each discovery’s earliest-record event. Some investigations cover later events on an earlier record or cross an era boundary. The counts partition the 24 changed records.

| Earliest record | Records changed | Historical result and remaining question |
| --- | ---: | --- |
| Before 3000 BCE | 5 | At Gesher, the fire and fish studies share flint observations from the same excavated horizons. The heating evidence supports the authors’ cooking interpretation, while use of those particular fires remains a candidate. At Ñanchoc, the later Tierra Blanca cultivation event is now distinct from the earlier crop evidence. Researchers could not tie a specific crop or date to the lower field supplied by the proposed Canal 3 connection. The Xihuatoxtla maize record also has a more precise account of the dating evidence. [Gesher](lanes/gesher.md) · [Ñanchoc](lanes/nanchoc.md) · [Maize](lanes/maize.md) |
| 3000 BCE–500 CE | 4 | Roman vault and Pantheon evidence supports one established process link. At Barbegal, the excavation supports a first-half-of-the-second-century construction anchor. At Antikythera, the five-turn, 235-month dial and its surviving pointer parts can be described separately from the reconstructed mechanism. The final drive gear and route of theoretical transmission remain unknown. [Roman building](lanes/building.md) · [Barbegal](lanes/placement.md) · [Antikythera](lanes/antiquity.md) |
| 501–1500 | 4 | The 812 Tang exchange decision and the Song court’s 1024 approval of the Yizhou note office give the monetary records dated institutional events. Direct transmission remains open. A 1047 visitor describes a Jerusalem hospital dispensing medicines and waqf-funded stipends for physicians. At San Bartolo, sealed deposits support a local Maya maize-treatment record, with the location of the cooking itself unresolved. [Chinese credit](lanes/credit.md) · [Jerusalem hospital](lanes/endowment.md) · [San Bartolo](lanes/maize.md) |
| 1501–1800 | 2 | At Engaruka, one excavated wall served as a canal side and a narrower canal was later cut into its fill. Deliberate sediment capture probably ceased in the 18th or early 19th century. Irrigation is practiced there today. Continuity across the intervening period remains open. The Nahua record identifies the particular preparation described by the 1577 witness; the specific supply route from earlier maize cultivation remains unestablished. [Engaruka](lanes/engaruka.md) · [Nahua maize](lanes/maize.md) |
| 1801–1950 | 4 | Babbage’s design joins weaving and computation. In medicine, a dated Necker Hospital case documents cylinder use in December 1817, and a London editor reported obtaining and commissioning local copies of Paris instruments by January 1820. Marshallese instruction with wave models is documented by 1862. The Sutatenza radio school gains a sourced Colombian origin and a 1954 transmitter inauguration. [Textiles](lanes/textiles.md) · [Medicine](lanes/medicine.md) · [Navigation](lanes/oceania.md) · [Radio](lanes/placement.md) |
| 1951 onward | 5 | Accounts differ on the production year of the Yoruba film *Aje Ni Iya Mi*. A surviving catalogue entry identifies a Yoruba VHS edition and its listed London distributor. Good recalled telling Tukey about an FFT in 1956. That testimony and the published acknowledgement leave the influence on the 1965 algorithm open. In the Marshall Islands, a named 2006 teaching encounter and return voyage are documented; dependence on the particular model during that voyage remains a candidate. [Yoruba film](lanes/yoruba.md) · [Fourier analysis](lanes/fft.md) · [Navigation](lanes/oceania.md) |

## What remains to research

| Measure | Before | After |
| --- | ---: | ---: |
| Discovery records | 902 | 906 |
| Dated events | 1,496 | 1,514 |
| Source records | 1,622 | 1,672 |
| Established links of all types | 203 | 205 |
| Established dependence or transmission links | 184 | 186 |
| Discoveries touching an established dependence or transmission link | 241 | 245 |
| Discoveries with neither an incoming nor outgoing link of these kinds | 661 | 661 |
| Candidate links | 7 | 10 |
| Insufficient-evidence links | 27 | 27 |

Four additional records now participate in established lineages. Two previously isolated records became connected, while two new discoveries entered without an established connection. All 90 pre-3000 BCE records still lack an established dependence or transmission link. The three new candidate links concern Gesher, Ñanchoc and Marshallese teaching. Other revisions strengthened dated events and provenance without creating a lineage.

The unplaced total remains 119: Radio Sutatenza acquired a sourced location, and Babbage’s new design record leaves its location open. Dating Barbegal reduced the undated group from four to three. The underlying catalogue still has 507 leads. The [full frontier CSV](frontier/research-frontier.csv) is a separate record-by-record view of all 906 discoveries, including their recorded prerequisites, unresolved links, and pointers to evidence gaps.

Next source targets are material that could change a verdict. At Ñanchoc, seek field stratigraphy tied directly to the documented canals. At Gesher, seek an independent test of the cooking inference using the fish and hearth spatial data. For the Yoruba film, a production document or first-person equipment identification could resolve conflicting accounts. For Good and Tukey, dated correspondence or working notes could establish when Good’s work entered the algorithm’s development. Each reviewed lane records its own further questions.

## Review and reproducibility

The wave used 14 GPT-6.2 Sol researchers at high reasoning effort and one more Sol worker for the frontier exporter. An Astra Medium coordinator assigned separate Terra High reviewers for each historical lane. Ten lanes went through a further review after a correction or renewed source inspection. The coordinating chat assembled the final accepted branches and confirmed that all 142 review-bound files matched their SHA-256 hashes. The merge retains the original proposals and review history. The research and review window ran approximately 23 minutes, from 20:20 through 20:43 UTC on 17 November 2026, before integration checks. Per-agent tokens and billing were unavailable. [Review decisions and exact commits](review-manifest.json) · [Structured reader data](results.json)

The validator, 171 Python tests, 53 frontend tests and production build passed. Browser checks selected all 14 investigations, opened source evidence, traversed both new relationships in the app and verified that only established edges were drawn in the research reader. Thirteen new binary-evidence descriptors follow the repository’s existing retrieval convention. Some studies were accessible only as scans, exposed passages or published summaries; each review records what its reader inspected.

To reproduce the figures and event selection, run the following from the repository root. To regenerate the CSV, point the exporter at a checkout containing the indicated data snapshot.

```sh
round=docs/reviews/2026-11-17-all-eras
snapshot=1537d299f2d0a6b4d121e8d5fb9f17467e067a08
python3 "$round/summarize.py" "$snapshot" "$round/results.json"
python3 tools/render_research_round.py "$round/results.json" "$round/view.html"
python3 tools/tech_tree_gaps.py "$snapshot" "$round/frontier"
python3 tools/research_frontier.py --data . --output "$round/frontier/research-frontier.csv"
```

[Coverage by domain, region and era](frontier/coverage.json) · [Domain figure](frontier/domain-gaps.svg) · [Baseline audit](../../analysis/2026-11-17-tech-tree-gaps/report.md)
