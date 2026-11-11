# Independent review of the science and technology graph

Reviewed snapshot: commit `30df3e7` (221 entries, 387 events, 131 relationships, 310 sources). Nothing in `data/`, `reviews/`, `schema.json` or `tools/` was changed. Row-level findings are in `connection-verdicts.jsonl` and `entry-verdicts.jsonl`; proposals are in `gaps.jsonl`. `summarise_verdicts.py` checks coverage and regenerates every count below that it computes. To browse the verdicts, open the private page [Interwoven graph review](https://claude.ai/artifact/4bVA9ksnaaFttCRKncAxgB), or `verdict-browser.html` locally.

## Overall judgement

**The individual claims are very good. The picture they add up to is not yet reliable.**

I agree with most of what is there at the level of a single claim. Of 131 connections, I agree with 96, would change 32, would remove 2, and could not verify 1. Reading the cited sources at their locators found no connection that its source fails to support; 127 are fully supported, 3 partly, and 1 could not be read. No connection runs the wrong way, though one (objectives to eyepieces) has an arbitrary direction. The graph is often more careful than the textbook version: it routes Maxwell to Hertz through Helmholtz, as Hertz himself says, and Carnot to Clausius through Clapeyron and Thomson, as Clausius says. Outright errors of fact are few. The 32 changes are mostly about relation type, and the disagreements are mostly about emphasis.

The problems are in what the graph chooses to show:

- **Dates.** Many entries are placed by when a witness appeared, not when the thing entered use, so the chart often misrepresents order.
- **Selection.** Evidence-rich witnesses have replaced the breakthroughs they stand for. Tier 0 contains a toothbrush bristle, while the Gutenberg press, paper, the telephone and all modern physics are absent.
- **Ranking.** Tiers were mostly assigned batch by batch, not on one scale.
- **Links.** The strictness that keeps bad links out also keeps out well-known true ones, leaving the chart's main histories in pieces.

A reader who trusts the chart's shape would come away with several wrong conclusions, even though nearly every sentence in the data is true.

Earlier decisions were respected. I have not treated chart order as a claim of causation, asked for a date to be invented, or objected to one-sided limits or to disconnected entries as such.

## The ten most important corrections

Each item is labelled as historical error, modelling choice or opinion.

1. **Re-anchor entries whose date contradicts the graph's own events** (modelling choice, some historical error). 37 entries sit at least 20 years after their earliest event, and 14 connections draw backwards.
   - Kilby is shown in 1964, after Noyce and Fairchild's flip-flops, though TI announced the solid circuit in March 1959 and the graph's own candidate file says so.
   - Bi Sheng's clay type (1041-48) is shown at 1400, after Korean metal type (1377), because the anchor is a surviving printed copy.
   - Maxwell and Hertz's reflection experiment are at 1894. Faraday's magneto-optic rotation is at 1864, not 1845.
   - The 1775 Soho trials are at 1854, the Linz trials at 1966, and the 1769 condenser specification at 1799.
   - Al-Khwarizmi's arithmetic is at about 1300, after Leonardo's Bugia instruction.

   The README says surviving manuscripts should not be automatic, yet about ten entries use them. Suggested rule: an anchor may not fall after any event in the graph that already shows the same community using or knowing the thing, and a dated publication normally beats a later citation.

2. **Fix the double helix's ancestry** (modelling choice with real consequence). Its only inbound edge is a paper on base ratios in insect viruses. Franklin and Gosling's constraints are at tier 3 and connect to nothing beyond their own diffraction entry, although Watson and Crick's paper acknowledges being stimulated by unpublished Wilkins and Franklin results. Add both links and Chargaff, and raise the Franklin and Gosling entries. On a contested subject this shape will be read as a position.

3. **Remove the pH to Oxford penicillin link and add Fleming to Oxford** (modelling choice). The first is shared laboratory context, as its own note concedes, and it joins two tier 0 entries. The second is missing, although the paper already cited says the strains came from Fleming.

4. **Re-rank tier 0 against one written test** (opinion, but consistently applied). Remove or replace Nylon filament for toothbrush bristles, Pittsburgh Reduction aluminum supply, Hart's CRISPR fitness screen, Hōkūleʻa built and Maya blue. Lower Barbegal, Dholavira, Muldoons, Mau's navigation, Jikji, the Diamond Sutra, Sørensen's exponent, Shang casting, Faraday's magneto-optic rotation and Bloomfield. Raise Ørsted, Kilby and Noyce, Hertz, Marconi, the telegraph, Pearl Street, the Web, stored-program computing, Brahmagupta's zero, the separate condenser and antisepsis. Today, electricity's founding experiment, the integrated circuit, the telegraph and the Web are all below tier 0.

5. **Split witnesses from what they witness** (modelling choice). Recombinant DNA appears as 1979 (Cohen and Boyer, 1973). PCR is 1989 (Saiki, 1985). CRISPR is 2015 (2012-13). The pH scale is 1914 (Sørensen, 1909). Newcomen is 1796 (1712). The stethoscope is an English practice of 1822 (Laennec, 1816-19). Euclid is one procedure dated to 325 CE. Bakelite is a 1935 radio cabinet. Keep the witness as a dated use, and add the thing itself.

6. **Add the major missing breakthroughs, or state plainly what the chart covers** (selection). See the gap list. There is no physics after Hertz, no earth science, no evolution or genetics before DNA, no germ theory, and nothing on agriculture or writing. Three of the classic Chinese inventions (paper, gunpowder, compass) are absent. Readers will assume a chart of how science and technology developed is at least broadly complete.

7. **Replace `observed-combination` and split `documented-development`, and separate confidence from strength** (modelling choice). See "Relation types" below. 109 connections are high confidence and none low, because confidence measures whether the source says it. Nothing records how much it mattered, so Wyatt to the double helix looks the same as Hoerni to the planar transistor.

8. **Reconnect broken histories using the existing bounded type** (modelling choice). The semiconductor history is in four unconnected pieces, printing is in four and arithmetic is in six or more, and the telegraph and electric power entries are isolated from electromagnetism. Most of the repair is routine: Frosch and Derick's oxide to Hoerni, Briggs to Gunter, Volta to Ampère (whose entry says "two voltaic piles"). The candidate review asks whether a specific design source can be proved. That is often the wrong question, and `bounded-technical-requirement` can carry many of these honestly.

9. **Give mathematics and practices their own kind** (modelling choice). Comparable mathematical texts are filed both ways: Ibn al-Bannā is science while his student al-Hawārī is technology, and two Old Babylonian tablets differ. See "Kind" below.

10. **Move labels out of regular expressions** (modelling choice with some plain bugs). 43 entries have a labelling problem. Beckman's pH meter is under Optics because of "glass-electrode", Google Glass is under Optics and Materials, Fleming's penicillin is under Genetics, and the Mathematics filter omits Napier, Briggs, al-Khwarizmi and Brahmagupta. See "Labels" below.

## Connections

**Evidence.** Five evidence readers checked each cited passage against the local copy; every row records how. I spot-checked several myself (Watson and Crick, the genome paper's technology passage, Sanger 1977, Kornberg, Abraham 1941) and they matched. The clean result needs reading correctly: statements were written from these passages, so support is expected, and it shows the statements are honest. It says nothing about whether the link matters or whether a better one is missing. Those questions are where the review's disagreements lie.

Partly supported:
- `mech-watt-expansion-to-carnot`: "incorporated into his analysis" overstates an appended note, and it is Carnot's only inbound edge.
- `entry-electronics-oersted-needle-railway`: no source links the instrument to Ørsted, and Cooke credits Ampère.
- `math-edge02-khwarizmi-to-alchorismi`: the reordering Folkerts shows is against a different text.

**Removed.** `chem-ph-scale-to-oxford-penicillin` and `entry-regional-link-tirta-waterworks-irrigation`; the second only says two things share one inscription.

**Timing.** Linked events run in a possible order everywhere except `mech-trial-cylinder-to-engine`, where the source event carries a disputed letter year but the edge states April 1775 at high confidence. 14 connections draw backwards on the chart because of anchors, not because the edges are wrong.

**Long, thin links.** `bio-taq-pcr-to-ebola-nanopore` is true and tells the reader nothing: most molecular protocols since 1990 could carry it. `mat-edge-aluminum-wright-castings` rests only on Alcoa's own timeline. `mech-shadwell-to-expansion-spec` is, by its own note, continuity of a principle.

**Relation types.** Six of the eight are sound. Two are not.

| Type | Count | Judgement |
|---|---:|---|
| `instrument-enables-observation` | 12 | Good. Every use holds. |
| `process-enables-production` | 4 | Good. |
| `theory-informs-design` | 4 | Good. |
| `bounded-technical-requirement` | 3 | Good and underused. The right tool for many of the missing long-range links. |
| `documented-adaptation` | 19 | Good, though it covers physical reuse, substitution and design borrowing. |
| `documented-transmission` | 16 | Usable. The boundary with development is unclear: Joule to Clausius is transmission, while Thomson to Clausius, the same kind of citation, is development. |
| `documented-development` | 51 | Too broad. It holds continuation within one programme, a citation of someone else's result, a critical response and a comparison. |
| `observed-combination` | 22 | Should go. I agree with only one of the 22 as typed. It covers part-of, material used, platform used, co-location, citation and companion. |

Proposed replacements: `continuation`, `cited-input`, `critical-response`, `component-of`, `material-used-in`, `used-as-platform`, `method-used-in`, `companion-of` (undirected), `same-principle` (no causal direction) and `same-family` (for stone saws and mills, with no diffusion claim). Co-documented things should not be drawn as links at all. Rows carry a `proposed_relation` where I would change it. This is a modelling choice for the owner; the current types are not false, only uninformative.

**Strength fields.** `necessity` is repeated boilerplate in 39 connections (three stock sentences), so it records that nothing was assessed. The stock text is honest, but it should say "not assessed". Add an `influence` field (minor, contributing, major, essential), kept separate from evidence confidence.

## Entries: kind, identity and date

**Kind.** Two-way is not good enough. The two kinds would otherwise be fine for most entries: I would change only 2 outright and move 28 to a new kind.

- Add **mathematics**. Filing it as science or technology has produced arbitrary results.
- Add **practice**, for institutions, transmission and customary systems: subak, chaski, Mau's teaching, the Malindi pilot, Bugia.
- Add a separate **role** field (observation, theory, instrument, method, process, artifact, infrastructure, text witness, transmission), rather than more kinds. It answers what the owner asked about methods and instruments without forcing each into one box.

**Identity.** 52 entries have an identity question.
- **Same thing split:** three entries from one Shen Gua paragraph; CB3 as two entries; two Tirta Empul entries from one inscription; the Joule apparatus entries; three hafir components; the toothbrush and its bristle.
- **Bundle:** the planar transistor entry includes the 2N1613, which has its own entry.
- **Witness instead of the thing:** see correction 5.

Over-splitting matters because it inflates the entry and edge counts of well-documented episodes.

**Facts.** Labels and configurations match the historical record almost everywhere. Things to correct:
- Lister's region says Glasgow on a Preston case.
- The Great Hafir is anchored to Meroitic use around 350 CE, while the project's own chronology page gives radiocarbon dates of the 6th to 4th century BCE.
- Barbegal's "by 300" postdates the abandonment its own rationale cites, and the entry doesn't reflect its 2024 source's new argument about hardtack.
- Muldoons' tier reason says it is anchored in material chronology while it displays 1350 CE beside a 4650 BCE event. Later literature describes initial construction at least 6,600 years ago.
- Humulin's date needs FDA approval (1982) and first sale (1983, per the graph's NAS source) kept apart.
- EDSAC ran programs from May 1949, before the anchor.
- The Shang casting entry is anchored after the Shang.

## Breakthroughs and ranking

**Are tiers 0 and 1 really the most consequential?** About half are. I keep 20 of the 35 tier 0 entries and propose raising 12 others. Across all tiers, 106 of 221 entries would move, 96 of them by one level. Tier is opinion, so read these with care. The firm corrections are the tier 0 items in correction 4 and the following, where the current ranking is hard to defend:

- Too high: the teakettle, AD36 radio cabinet, pilgrim bottle and Anyang jar (tier 1).
- Too low: Franklin and Gosling's constraints (tier 3), Harrison's H4, the Nine Chapters and Portsmouth block mills (tier 2).

The other moves mostly rescale specialist items down to the existing tier 3, which has only 9 entries.

**Is the reasoning consistent?** No. 68 entries share a tier reason with at least two others, and those reasons describe a category, not a consequence. All 15 electronics additions are tier 1 ("a specific community-facing use..."), all 13 regional additions are tier 2, and four materials entries are tier 0 with "a major material or enabling industrial process". Tier was assigned per research batch, which is why a teakettle equals the telegraph.

**Does ranking follow documentation?** Not directly: median sources per entry is 2 at every tier, and median connections 1. The effect is at cluster level. Well-documented episodes get many entries, and those then fill the tiers:

- The steam and heat cluster has 25 connected entries, whereas electric power has 3.
- Hōkūleʻa has six, and ancient Pacific voyaging has none.
- Tier 0 also holds entries with little behind them: 13 rest on one source, 8 have no connections and 17 have nothing inbound.

**Regions and eras.** There are two opposite biases, and fixing one should not worsen the other.

- Coverage is heavily British and American. A rough parse of the `regions` field gives Britain 66 and the USA 40 of 221.
- To counter this, regional witnesses have been promoted for corrective reasons. Jikji's tier reason is about preventing a European bias, and there is no European branch in the graph. Muldoons and Dholavira are similar. This confuses inclusion with rank, and it leaves the larger non-European achievements absent: paper, the compass, gunpowder, Indian place value as a system, Ibn al-Haytham, maize, the settlement of Oceania.
- My tier proposals apply the same test everywhere. I demote comparable European and American entries too, such as Bloomfield, the aluminum supply and the nylon bristle, and I raise the Nine Chapters, Rhind, Brahmagupta and Abū Kāmil, since mathematics outside Europe is consistently under-ranked.

## Gaps

These are proposals only, with fuller reasons and sources in `gaps.jsonl`. Sources are from my knowledge unless stated. Check them before use.

### Missing breakthroughs, most important first

| # | Breakthrough | Why | Likely source |
|---:|---|---|---|
| 1 | Gutenberg's press | Printing stops at Korea, and the tier reasons refer to a European branch that doesn't exist. | Eisenstein 1979 |
| 2 | Papermaking | Precondition for much of the printing and arithmetic. | Tsien 1985 |
| 3 | Domestication, including maize | Nothing on food; no agriculture label. | Zeder 2011 |
| 4 | Writing | Base of the mathematics and record entries. | Schmandt-Besserat 1992 |
| 5 | Germ theory and vaccination | Lister and penicillin are unexplained. | Brock 1988 |
| 6 | Evolution and heredity | The molecular cluster has no question behind it. | Mayr 1982 |
| 7 | Newton's Principia and calculus | Mathematical physics is absent. | Westfall 1980 |
| 8 | Copernicus and Kepler | Galileo's observations bear on nothing. | Gingerich 2004 |
| 9 | Relativity and quantum theory | No physics after Hertz. | Pais 1982 |
| 10 | Fission and reactors | A major science-to-technology path. | Rhodes 1986 |
| 11 | Haber-Bosch | Named in the backlog; feeds much of the world. | Smil 2001 |
| 12 | Newcomen's engine | Watt has no predecessor. | Rolt and Allen 1977 |
| 13 | Steam railways | The steam cluster ends before rail. | Simmons 1978 |
| 14 | Magnetic compass | In the same Shen Gua book the graph already uses. | Needham 4.1 |
| 15 | Gunpowder | With paper and compass, three classic inventions absent. | Needham 5.7 |
| 16 | Euclid's Elements | Behind one tier 2 procedure. | Heath 1908 |
| 17 | Al-Khwarizmi's Algebra | Abū Kāmil is present; the founding text isn't. | Rashed 2009 |
| 18 | Indian decimal place value | Witnesses only. | Plofker 2009 |
| 19 | Ibn al-Haytham's Optics | Optics begins with Dutch spectacle makers. | Sabra 1989 |
| 20 | Chemical revolution, periodic table | Chemistry has no theory. | Scerri 2007 |
| 21 | Vacuum tube | Link between radio and computers. | Aitken 1985 |
| 22 | Stored-program computing origins | EDSAC is alone. | Haigh et al. 2016 |
| 23 | Junction transistor | Links point-contact to planar. | Riordan and Hoddeson 1997 |
| 24 | ARPANET and TCP/IP | The Web has no network. | Abbate 1999 |
| 25 | Powered flight | Only an aluminium casting. | Crouch 1989 |
| 26 | Telephone | Only an exchange. | Fischer 1992 |
| 27 | Dynamo and electric lamp | Links Faraday to Pearl Street. | Hughes 1983 |
| 28 | Iron smelting | Only meteoritic beads and later steel. | Erb-Satullo 2019 |
| 29 | Laser and optical fibre | In the backlog. | Bromberg 1991 |
| 30 | Settlement of Remote Oceania | The achievement behind the Hōkūleʻa entries. | Wilmshurst 2011 |

Near misses: mechanical clock, wheel, internal combustion engine, spaceflight, plate tectonics, glassblowing, machine learning, the Hall-Héroult process (see the Alcoa entry), Bakelite and Carothers's nylon.

### Missing connections between existing entries, most important first

"Read" means I or an evidence reader found the supporting passage locally.

| # | From | To | Reason | Check |
|---:|---|---|---|---|
| 1 | Humidity-varied DNA diffraction | Double helix | Acknowledged by Watson and Crick; the key evidence. | Read |
| 2 | B-DNA constraints | Double helix | Franklin and Gosling dead-end without it. | Read |
| 3 | Fleming's selective culture | Oxford penicillin | Abraham 1941 says the strains came from Fleming. | Read |
| 4 | Silicon oxide mask | Hoerni planar conception | The central technical link. | Knowledge |
| 5 | Photolithographic windows | Planar transistor | The entry's own anchor is Fairchild use by 1958. | Record |
| 6 | Volta | Ampère | His configuration says voltaic piles. | Record |
| 7 | Volta | Ørsted's trough battery | The voltaic tradition; needs a source on troughs. | Knowledge |
| 8 | Ampère | Blackwall telegraph | Cooke credits Ampère's idea. | Read |
| 9 | Briggs | Gunter | Common logarithms; Gresham colleagues. | Knowledge |
| 10 | Abū Kāmil | Liber abaci | Joins Arabic algebra to Latin Europe. | Knowledge |
| 11 | Elsecar (Newcomen) | Watt's condenser model | Watt's repair of a Newcomen model; needs a Newcomen entry. | Knowledge |
| 12 | Mau's 1976 voyage | Mau teaches Thompson | Same project. | Knowledge |
| 13 | Morse | 1858 Atlantic cable | Field records Morse's role. | Read |
| 14 | Morse | Marconi aerial | Marconi names a Morse key. | Read |
| 15 | Ørsted | Morse | Same bounded link as Blackwall. | Knowledge |
| 16 | Faraday ring | Lauffen-Frankfurt | Transformers; bounded. | Knowledge |
| 17 | Faraday disc | Pearl Street | Generation; a dynamo should sit between. | Knowledge |
| 18 | Faraday moving magnet | Joule magnetocalorimeter | Bounded; joins electricity to heat. | Read |
| 19 | Joule magnetocalorimeter | Joule series two | Same paper; one entry isolated. | Read |
| 20 | Regnault | Clausius | Clausius names him repeatedly. | Read |
| 21 | Joule friction | Clausius | An edge note says Clausius names it; check timing. | Record |
| 22 | Expansive specification | Soho double-expansive | The same document. | Knowledge |
| 23 | Condenser specification | Old Bess | A separate-condenser engine. | Knowledge |
| 24 | Maudslay's lathe | Portsmouth block mills | Maudslay built the machines. | Read |
| 25 | DNA polymerase | Plus/minus sequencing | Sanger and Coulson name E. coli polymerase I. | Read |
| 26 | Recombinant cloning | Mapped-clone sequencing | BACs are recombinant clones. | Knowledge |
| 27 | Taq PCR | Mapped-clone sequencing | The consortium lists sequencing polymerases and cycle sequencing; check references. | Read |
| 28 | Aluminum supply | Teakettle | Same firm, same page. | Read |
| 29 | Nine Chapters | Fangcheng | Chapter 8 is part of the text. | Read |
| 30 | Watt's condenser | Carnot | Carnot's subject is the steam engine; one note on expansion is thin. | Knowledge |

Also worth a second look: Diamond Sutra to Bi Sheng (Shen Gua opens from woodblock printing), Jikji's metal to woodblock editions (same text and monk), and a `same-family` link across the three Roman stone saws and the water mills. I agree with the earlier review's refusal of the speculative long-range candidates, such as Oughtred to Soho, Newton to Abbe and the Intel 4004 to the genome.

### Large clusters disconnected when they should not be

The graph has 98 fragments and 59 isolated entries. Disconnection is valid in principle, and I do not object to Ra I, Keawanui or the Andean and Pacific entries having no ancestry. These are different, because the connections are known:

- **Semiconductors:** Fairchild planar (7), transistor, MOS and 4004 (6), oxide and photolithography (2), Kilby (1).
- **Telegraph:** Blackwall is tied to electromagnetism, the Atlantic pair is separate, and Morse, India and Japan are isolated.
- **Electric power:** Lauffen and Niagara (2), Pearl Street (1), neither tied to Faraday.
- **Computing:** EDSAC and LEO (2), Colossus, FORTRAN and the Web each isolated, and the 4004 separate.
- **Molecular biology:** the main 11, Franklin's pair, cloning and insulin, PCR and nanopore, hybridoma, CRISPR, Maxam-Gilbert.
- **Positional arithmetic:** al-Khwarizmi (3), Bugia and Leonardo (2), Ibn al-Bannā and al-Hawārī (2), al-Uqlidisi (2), Brahmagupta, Gwalior.
- **Printing:** Bi Sheng (3), Diamond Sutra, both Jikji.
- **Roman water power:** Barbegal (2), Rome (3), three saws.

## Labels

The rules test only the id, label and icon, so words in names drive the labels: 158 entries use regular expressions and 63 use overrides. They are not reliable, and row-level problems are in the `label_issue` field.

Plain bugs:
- Beckman's "glass-electrode" gives Optics and Materials.
- "spyglass" gives Materials.
- "Google Glass" gets past the guard, which only checks the id.
- "polymerase" gives Instruments.
- `^bio-` gives Genetics to Fleming's penicillin and to hybridomas.
- "engine" makes the Wright casting Energy only.
- "kilby", "noyce" and "multiplexer" give Computing to an oscillator and an analog multiplexer.

Gaps:
- Mathematics omits Napier, Briggs, al-Khwarizmi, Brahmagupta, Ibn al-Bannā, Liber abaci and others.
- Steam omits Elsecar and Shadwell, because the rule is an id whitelist.
- Medicine has 4 entries and omits Fleming and the Ebola study.
- Faraday's rotation has no Optics.

The set itself needs changing:
- Rename **Optics & glass**, which puts pilgrim bottles beside telescopes. Split it into Optics and Glass.
- Rename **Genetics** to Molecular biology, since most of it is sequencing method.
- Rename **Wayfinding** to Navigation and seafaring, which would fit Harrison and Ra I.
- Add **Integrated circuits**, **Agriculture**, **Mechanisms** and **Medicine and microbiology** as real rules.
- Merge or define **Energy** and **Spread of knowledge**, which are too broad to filter by.

I recommend storing reviewed labels on the entries (`node.labels` is already supported by the importer) and dropping the rules, or adding a test that fails on a new unreviewed label.

## Other things that could mislead a reader

- **Precise-looking placement.** 154 of 221 placements are one-sided "known by" limits drawn at that limit, so most marks are at the latest possible date, skewing the whole chart later. Early eras suffer most. The detail panel explains this, but the chart's shape doesn't. Consider drawing the unknown side visibly.
- **Awareness in one community read as arrival in history.** A Polish bibliography (Gerlafingen), a US court (Linz trials), Muirhead's 1854 edition (Soho) and a copyist (Hawari) are real communities, but a reader sees a date. The rule "best defensible entry within a named community" permits nearly anything once the community is small enough, and in several cases the community is chosen by what the sources happen to show. It needs a rule of precedence.
- **Validation language.** "Accepted" and "zero concerns" mean hashes and structure, and the README says so. A reader of `CHECKPOINT.md` could still take them as more than they are. Lifecycle evidence is also thin: 2 of 171 technologies have a documented first commercial date.
- **Thread stories.** A Stories view that lifts out a thread will present these gaps as narrative: the double helix would be told with a viral paper as its only input.
- **Absence reads as independence.** Isolated entries look like independent inventions, though the graph says otherwise. Show "not yet researched" and "investigated, insufficient" differently from "no known link".
- **Modern reconstruction reads as origin.** Hōkūleʻa, Korent and Ra I are valuable, but with no ancient voyaging entry they place Pacific navigation in the 1970s.

## Decisions for a historian or the owner

**Owner:**
- What the chart claims to cover, and whether to state it on the page.
- A written test for tier 0, and whether specialist entries should be kept at all or moved to fine detail.
- The precedence rule for anchors. Should a chart meant for general readers show first public record, first use, or both?
- Whether to adopt new relation types, an influence field, new kinds and a role field. These have the widest effects.
- How far to merge over-split entries, since the Bi Sheng, CB3 and similar decompositions were deliberate.

**Historian:**
- Muldoons: when was the channel first used, and how should the entry read? This needs McNiven et al. 2012, which I could not read.
- Franklin's contribution: the wording and timing of the two links. Check the MRC report route against Cobb and Comfort 2023.
- The Volta-to-trough link: the voltaic tradition is agreed, but the specific source needs finding.
- Whether Hoerni's and Fairchild's knowledge of Atalla's and Bell's oxide work can be documented, as Riordan and Bassett suggest.
- Shadwell's expansive working, which now rests on Smiles.
- Barbegal's function and dates, in light of the 2024 paper.
- Wright Flyer aluminium: an independent source for the supplier.
- Whether Jikji's woodblock edition descends from the metal one.

## What I could not verify, and the limits of this review

**Not read:**
- McNiven et al. 2012 (no local copy; paywalled), which is why one connection is `cannot_verify`.
- The Science Museum page for the Blackwall instrument, and the Smithsonian and UNESCO chaski pages (errors on fetching).
- The original Smith 1986 PDF (only an index note and abstract).
- The table in Carnot's note, which is absent from the local copy.

**How rows were checked:**
- Connections: 125 had all cited sources read at the locator, 4 partly, 1 also with another source, 1 could not be read. Readers were subagents. I spot-checked a sample and did not re-read all of them. Some scanned sources were read by OCR.
- Entries: I read every entry's record. I did not separately check each entry's anchor evidence. 59 are from the record and my knowledge only, 157 also have linked connection sources read, and 5 have a cited or other source read directly. Every row says which.
- Online checks were search-result summaries, used only as a cross-check: secondary accounts of the Wright engine, a summary of the follow-up paper on Muldoons, coverage of Cobb and Comfort 2023, TI's March 1959 announcement, the Oxford penicillin story and the 2024 Barbegal paper. I did not read those papers in full. Facts from my own knowledge, such as EDSAC's May 1949 first program and the 1241 Pisan decree, are marked as such where they carry weight, and should be checked before they enter the graph.
- Gap sources are likely starting points from memory. Treat the citations as leads.
- `reviews/` was treated as the author's claims. I read the candidate links in full, but not every ledger line by line.

**Judgement.** Tier and kind rows are one reviewer's opinion, consistently applied, and I expect a historian to disagree with some. Rows carry `issue_class` (historical_error, modelling_choice, evidence_limit or opinion) so they can be weighed accordingly. By that field, entries carry 15 historical-error flags, mostly about dates, against 100 modelling and 81 opinion flags.

The region parse is crude. Medians per tier are from stored provenance, not a full count of the evidence.

## Regenerating

```sh
python3 research/science-technology-graph/handovers/independent-review/summarise_verdicts.py
```

The script validates coverage and values and writes `summary.json`, `summary.md`, `verdict-summary.png` and `verdict-browser.html` (`matplotlib` is needed only for the figure). The numbers depend on the reviewed commit's `data/`; later commits may report missing ids, which is intended.
