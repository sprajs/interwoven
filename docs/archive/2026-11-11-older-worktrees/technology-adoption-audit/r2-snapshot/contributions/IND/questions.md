# IND: unresolved questions and research priorities

This register accompanies eight purposively selected industrial-system cases. It records missing evidence and competing explanations, not facts established by the present investigation. The case, claim and source ledgers contain the bounded findings and exact access levels. None of the follow-up material below is silently counted as an inspected source.

## Consequential weak-access and inherited evidence

1. **Reservoir coordination, IND-C03 / IND-K08.** Malm's *Fleeing the Flowing Commons* (IND-S06) was available only as the author-repository abstract. Acquire the full article, identify the original schemes and correspondence, and inspect engineering, flow, capital and allocation assumptions. Compare unbuilt schemes with realised reservoirs. Coordination failure and an economically unattractive project currently fit the observed non-building equally well. Neither the unrealised proposal nor a national water-potential estimate establishes a usable low-cost alternative at a particular mill.
2. **Factor-price comparisons, IND-C04 / IND-K09–K10.** The Allen source is the introductory publisher excerpt (IND-S07); its underlying machine-payback calculations were not acquired. Humphries and Schneider's accepted manuscript (IND-S08) was inspected, but the original archive items were not. Inspect task- and yarn-count-specific wages, hours, output quality, machine prices and maintenance costs, including commercial cotton workers underrepresented in the surviving observations. Determine whether a high international wage, low female household earnings and a changing marginal labour cost are distinct measurements that competing authors improperly equate.
3. **Colonial tariff authority, IND-C05 / IND-K16.** Charles Grant's 1821 testimony is inherited through Inikori (IND-S13) and his cited source, not an independently inspected parliamentary record. Retrieve the original statement and relevant tariff legislation, then connect them to named cloth qualities, markets and years. Asymmetric power is not a numerical estimate of the trade outcome under symmetric sovereignty.
4. **China's handloom-output share, IND-C07 / IND-K21.** The approximately 70 percent estimate for 1934–1936 is reported by Eyferth (IND-S15) from earlier research. Trace the original denominator, geography, yarn/cloth conversion and treatment of household output before using it quantitatively. Check regional time series: a declining share need not mean declining absolute hand production. Eyferth's later socialist-era evidence must not be projected backward to establish pre-1949 household choices.
5. **Engine performance and macro accounting, IND-C02 / IND-K04–K06.** Read original *Lean's Engine Reporter* issues, engine accounts and sampling conventions. Separate best reported duty, typical operating performance, annual fuel cost, mine profit and aggregate productivity. Nuvolari and Crafts share some inherited engineering histories; their agreement is not independent measurement. Crafts's January 2002 version remains the identified source for the bounded growth-accounting claim.
6. **Electric-power configurations, IND-C08 / IND-K23–K25.** Devine (IND-S16) combines technical journals and reconstructed capacity data; the underlying journal and census records were not independently audited. Follow a sample of plants through investment, machine design and operating changes, explicitly separating motor horsepower from numbers of factories, machines or workers. Utility service and onsite generation are alternative supplies; a motor attached to a line shaft is not evidence of unit-drive redesign.

## Comparisons most likely to change a mechanism claim

| Comparison | Distinguishing evidence sought | What the current cases cannot decide |
|---|---|---|
| Water versus steam at actual decision sites | Dependable seasonal power, rights, delivered fuel, engineering costs, demand and labour access for matched mills or mines | Whether hydrology, finance, agglomeration or coordination was binding in a particular purchase |
| Reported versus unreported pumping engines | Comparable design/vintage and investment, actual transfer of practices, downtime and full-year performance | The separate effect of disclosure from simultaneous engineering and district expansion |
| Rings versus mules and high drafting | Orders linked to completed installations, yarn quality, breakage, cotton mixes, work hours, maintenance and profits | Whether employer expectations were realised, or why nonbuyers lacked finance or rejected equipment |
| Mechanisation and household textile work | Followed households or cohorts, task-specific income, unpaid hours, outside employment, contracts and cloth properties | Whether displaced spinners found new livelihoods, whether hybrid weaving was preferred or constrained, and who received the gains |
| Electric retrofits versus new plants | Comparable products/demand, workflow changes and total capital spending, including non-electric new equipment | The productivity effect of motors apart from expansion and general investment |
| Colonial versus other textile competition | Quality-matched prices and market shares under differing policies, with independently dated policy and agricultural shocks | Unique shares attributable to productivity, imperial coercion, climate or political fragmentation |

Machinery orders, national capacity, treatise illustrations and household production estimates are different observation units. These comparisons require new common measures; they should not pool the existing records into a diffusion regression. See IND-X01–IND-X04 in [comparisons.json](comparisons.json) for explicit similarities, non-independence and omitted countercases.

## People and outcomes underobserved

The inspected evidence favours investors, engineers, machinery suppliers and surviving successful installations. It supplies little person-level evidence of displaced workers' subsequent employment, lifetime earnings, health or bargaining position. Paid labour, household work, child dependence, institutional recruitment and enslavement must remain distinct. The machinery buyer's choice does not establish operators' ability to refuse, and aggregate productivity does not demonstrate compensation of those bearing losses.

Useful next acquisitions include worker correspondence, household accounts and time budgets, recruitment contracts, apprenticeship and occupational-entry records, pay books linked across years, injury/mortality evidence and local welfare records. Such records have their own selection and administrative biases. An absence of complaints cannot be treated as consent without an account of preservation and the ability to complain.

## Geographic and technical omissions

The cases give substantial attention to Britain, India, Japan, China and the United States, with an earlier central European mining comparison. They do not establish representative coverage of African, Ottoman, Russian, Latin American or continental European industrial trajectories. Particularly useful countercases would include continental steam/water choices, successful collective reservoirs, Indian handloom persistence, Japanese rural weaving, Russian textile and labour institutions, and industrial expansion outside cotton. These are follow-up directions, not acquired findings.

The strand is also weighted toward textile and power systems. Chemical processes, steel, machine-tool firms, construction, military procurement, industrial agriculture and maintenance networks are not sufficiently represented to support general claims about all industrial adoption. Other programme contributions may address some gaps; cross-strand similarity does not create independent corroboration.

## Claims deliberately withheld

- A single numerical share of industrialisation caused by coal, wages, patents, slavery or colonialism.
- A universal ranking of water, steam or electric arrangements independent of task, site and complements.
- A fixed mapping from high wages to a particular machine, or from low wages to non-adoption.
- A claim that every older technology persisted rationally, or that every delayed purchase reflected irrational resistance.
- A claim that technical feasibility establishes deployment, an order establishes profitable operation, or output growth establishes welfare improvement.
- A prediction that people displaced from one task will necessarily occupy the new skilled roles created elsewhere.

## Reproduction and local checks

The records are generated by `build_records.py`, then extended by `extend_records_v2.py`. Run them in that order, followed by `check_records.py`. The extension preserves source lineage, case-specific actor/labour fields, rival-mechanism tests and graph scope. It separates British textile-mill waterpower from central European mine waterpower and makes no bounded-necessity or extra joint-input claim.

The local validator checks required fields, identifiers, references, enumerations, source access accounting and graph scope. Its result is written to [validation.json](validation.json). Those checks establish record integrity only. Historical entailment still depends on inspecting the named evidence and retaining the limitations above.
