"""Write the CTX supplement. Evidence judgments are authored, not generated tests."""
from pathlib import Path
import json

R = Path(__file__).parent
S01 = 'https://www.cambridge.org/core/services/aop-cambridge-core/content/view/1B4DC63727682F1EEC958A62A4126757/S0020859012000521a.pdf/womens-work-and-the-politics-of-homespun-in-socialist-china-1949-1980.pdf'
S03 = 'https://www.cambridge.org/core/services/aop-cambridge-core/content/view/D3FF69916AB8B12A27073722AF080C6F/S1557466019015365a.pdf/women-and-chinas-socialist-construction-1949-78.pdf'

sources = [
    {
        'id': 'CTX-S01',
        'title': 'Women’s Work and the Politics of Homespun in Socialist China, 1949–1980',
        'authors': ['Jacob Eyferth'], 'year': 2012, 'url': S01,
        'source_type': 'scholarly-analysis', 'access': 'full-text',
        'locator': 'International Review of Social History 57(3), pp.365–391, DOI 10.1017/S0020859012000521. Entire publisher PDF text inspected through web; post-1949 pp.374–391 read closely. Direct local PDF/HTML downloads failed (403); no original PDF hash claimed.',
        'scope_limit': 'Retrospective interviews and archival interpretation, not random national sampling or an identified policy effect. About 200 interviews with >80 villagers in three Guanzhong villages, mostly people born 1920–1945. Original recordings and Chinese archival files not independently inspected. National estimates and post-1980 diffusion are not promoted to CTX findings.',
        'accessed': '2026-11-05',
        'evidence_lineage': 'EXACT SAME ARTICLE as IND-S15, not independent corroboration. IND uses the inherited pre-1949 background; CTX uses original 2005–2011 fieldwork in Gedatou (Zhouzhi) and Danbei/Zhangli (Xingping), Shaanxi archival material and associated scholarship. National cloth estimates inherit Xu Jianqing, SMC and earlier studies. Eyferth cites Hershatter/Gao for women’s mobilisation; CTX-S03 in turn cites Eyferth2012/2015 for cloth access. Original-record overlap beyond identified citations is unknown.'
    },
    {
        'id': 'CTX-S03',
        'title': 'Women and China’s Socialist Construction, 1949–78',
        'authors': ['Gail Hershatter'], 'year': 2019, 'url': S03,
        'source_type': 'scholarly-analysis', 'access': 'full-text',
        'locator': 'The Asia-Pacific Journal: Japan Focus 17(12), no.2, article 5289, 15 June 2019; published excerpt from Women and China’s Revolutions. Full text accessible through publisher web PDF extraction; inspected pp.1–3, 10–19, 24 and notes pp.26–28. Direct APJJF downloads failed. Use printed PDF page numbering, not the book’s.',
        'scope_limit': 'A broad scholarly synthesis incorporating the author’s earlier original research, not a new matched sample of Eyferth’s villages. Used for policy variation and social/public roles; original works behind every statement were not separately inspected. Full bibliographic details are referred to the book by the excerpt.',
        'accessed': '2026-11-05',
        'evidence_lineage': 'Notes41/43 identify Hershatter2011, Gao2006 and other scholarship for rural work and labour models. Note49 explicitly uses Eyferth2012/2015 for household cloth access; note40 shares Eyferth2015 and Hershatter2011 for early textile activity. Thus cloth-access agreement is inherited evidence, not an independent replication of CTX-S01. Broader social-history material is additional context with incompletely reconstructed original-record overlap.'
    },
]

def support(sid, loc, text):
    return {'source_id': sid, 'locator': loc, 'supports': text}

def descriptive(reason):
    return {'status': 'descriptive-only', 'reason': reason}

def mechanism(chain, rival, observation, found, ambiguity, timing='retrospective synthesis responding to P2-SP03'):
    return {
        'status': 'underdetermined', 'mechanism_chain': chain,
        'strongest_rival': rival, 'discriminating_observation': observation,
        'evidence_sought_found': found, 'remaining_ambiguity': ambiguity,
        'hypothesis_timing': timing,
    }

claims = [
    {
        'id': 'CTX-K01', 'case_ids': ['CTX-C01'],
        'statement': 'Eyferth’s post-1949 investigation records continued household textile work in three Guanzhong villages: Gedatou in Zhouzhi, and Danbei and Zhangli in Xingping. Its fieldwork comprised about 200 interviews with more than eighty villagers, mostly men and women born in 1920–1945, over fourteen weeks during five visits in 2005–2011.',
        'evidence_type': 'scholarly-analysis', 'confidence': 'medium', 'causal_status': 'descriptive',
        'sources': [support('CTX-S01', 'pp.379–381; pp.384–389 for recalled collective-era work', 'Names sites, interview scope and population, then reports work histories.')],
        'counterevidence': 'The author explicitly acknowledges that one village cannot represent China and presents extension to other cotton regions as a hypothesis. Later photographs distinguish a spinning demonstration and niche weaving.',
        'inference_limits': 'No probability sampling frame, sex-specific interview count, national prevalence or annual adoption series. This is retrospective local evidence; 2011–2012 photographs are not a measurement of collective-era diffusion.',
        'test': descriptive('Records the population and observed practice; assigns no causal share to persistence.'),
    },
    {
        'id': 'CTX-K02', 'case_ids': ['CTX-C01'],
        'statement': 'In Eyferth’s Zhouzhi account, cloth-ration entitlement did not ensure purchased factory cloth: informants attributed coupon resale and continued home production to scarce disposable cash, with village cadres and newly married couples described as exceptions to the prevailing practice.',
        'evidence_type': 'scholarly-analysis', 'confidence': 'medium', 'causal_status': 'mechanism-supported',
        'sources': [support('CTX-S01', 'p.377 for 1954 procurement/rationing; pp.386–387 for Zhouzhi use and cash', 'Distinguishes coupon access from buying cloth and reports resale, household resources and exceptions.')],
        'counterevidence': 'Rations could themselves fall below needs; homespun had reported durability and social uses. Better-dressed cadres and newlyweds are not matched households and had different roles and needs.',
        'inference_limits': 'Supports an actor-level access pathway, not a national preference claim, a measured price elasticity or a counterfactual effect of abolishing the policy. The numerical household budget is an author’s illustrative reconstruction, not a sampled mean; it is not reproduced as a CTX estimate.',
        'test': mechanism(
            'Procurement/income arrangements and essential purchases leave little cash -> households sell coupons and avoid cloth spending -> home production supplies clothing despite industrial availability.',
            'Durability, ritual use or custom could sustain homespun even with adequate purchasing power; low physical rations could also cause home production.',
            'Compare redemption and home labour across similar households or within the same household after cash changes, holding cloth entitlement, service quality and family needs as constant as possible.',
            'Read CTX-S01 pp.377 and 386–387: explicit cash explanation and coupon resale, with named social exceptions. No matched household panel or affordability intervention found in the article.',
            'Interviews favour constrained access over preference alone, but prices, quantities, cloth qualities and obligations vary together; relative contributions remain unidentified.'
        ),
    },
    {
        'id': 'CTX-K03', 'case_ids': ['CTX-C01'],
        'statement': 'The Guanzhong accounts describe women meeting household clothing duties through unpaid textile work alongside collective agricultural obligations, often at the expense of rest. This supports a pathway in which continued household production was sustained by shifting time costs onto its women operators.',
        'evidence_type': 'scholarly-analysis', 'confidence': 'medium', 'causal_status': 'mechanism-supported',
        'sources': [support('CTX-S01', 'pp.385–389, especially pp.388–389 and notes79–82', 'Connects collective work, family expectations, blame, night work and recalled exhaustion.')],
        'counterevidence': 'Women negotiated, traded and sometimes held leadership positions; both textile skill and public work could bring recognition. The source does not show every household bargain or compare all male and female tasks.',
        'inference_limits': 'No quantified aggregate labour transfer, national time budget, coercion rate or net welfare balance. This is not evidence of a state mandate to hand-weave: official policy opposed that activity while other obligations narrowed alternatives.',
        'test': mechanism(
            'Collective labour demands plus household clothing obligations -> women reconcile competing claims with additional domestic work -> clothing is supplied while operators bear unremunerated time and rest costs.',
            'Poverty or clothing quality might motivate extra work independently of gendered authority; rewarding skilled activity could explain some time spent at the loom.',
            'Separate household time diaries and bargaining accounts, including households with shared textile duties or purchasable substitutes, would test who could shift costs and refuse them.',
            'Read CTX-S01 pp.388–389: differentiated household duties, late textile work, reported exhaustion and blame, alongside accounts of negotiation and sale.',
            'Accounts directly locate burdens but do not isolate gendered authority from scarcity, family size, skill or preferences; prevalence and causal magnitude are not measured.'
        ),
    },
    {
        'id': 'CTX-K04', 'case_ids': ['CTX-C01'],
        'statement': 'Reported durability and the social uses of textiles complicate a comparison based on metres of cloth alone. These observations leave room for useful task advantages of homespun, but do not establish that ritual textiles had to be handmade or that operators freely preferred the work.',
        'evidence_type': 'scholarly-analysis', 'confidence': 'medium', 'causal_status': 'mechanism-supported',
        'sources': [support('CTX-S01', 'pp.383–384 for exchanges and grave clothes; p.386 and note76 for interview-based cloth needs; p.382 captions for later niche', 'Documents differentiated cloth services and an author estimate reflecting reported wear.')],
        'counterevidence': 'Factory cloth was used by some people and ration coupons were sold for cash. Social duties could impose obligations rather than represent autonomous preference. Material quality was not measured experimentally.',
        'inference_limits': 'No controlled wear test, all-purpose technical ranking or causal contribution of ritual demand. The local subsistence estimates cannot be treated as objective universal clothing requirements.',
        'test': mechanism(
            'Cloth attributes and local social uses -> differing value for specific services -> possible persistence of selected hand-production tasks.',
            'Restricted cash and household authority can produce the same observed persistence even when a factory substitute could perform the task adequately.',
            'Compare equivalent warmth, wear, repair and social acceptability at affordable prices, allowing the operator meaningful refusal; persistence after those constraints relax would strengthen the task-advantage account.',
            'Read CTX-S01 pp.382–386: reported product/service distinctions, but no matched product trial or claim that all gifts necessarily require handmade cloth.',
            'Useful service and constrained access are compatible; the source cannot allocate their weights.'
        ),
    },
    {
        'id': 'CTX-K05', 'case_ids': ['CTX-C01'],
        'statement': 'Retained and diverted cotton, local distributions and some black-market cloth production offered routes around formal procurement constraints in the Guanzhong account. Reports of commercial weaving coexist with reports that its risk and required absence from collective work made it inaccessible to many interviewees.',
        'evidence_type': 'scholarly-analysis', 'confidence': 'medium', 'causal_status': 'mechanism-supported',
        'sources': [support('CTX-S01', 'pp.387–388; p.377 for self-retained cotton', 'Describes cotton sources, concealed distributions, trading and different assessments of commercial risk.')],
        'counterevidence': 'Some interviewees, including a former local Women’s Federation chairwoman, sold cloth. Self-provision was not the only use of household output, and local leaders were not uniformly enforcers of central restrictions.',
        'inference_limits': 'No fraction of all households able to trade, audited profitability or proof of women’s control of proceeds. Commercial anecdotes cannot establish a generally accessible independent occupation.',
        'test': mechanism(
            'Cotton retained, diverted or exchanged outside formal channels -> inputs for home production and occasional sales -> clothing or cash despite official restrictions.',
            'Commercial reports may be selected exceptional accounts; formal rations or gifts might have supplied more clothing than narrators recall.',
            'Link dated team cotton accounts and household output/sales to independently recorded access and enforcement, comparing sellers and nonsellers.',
            'Read CTX-S01 pp.387–388: several distinct input routes and admissions of sales, but also danger/absence constraints and disagreement between farmers and former leaders about pilfering.',
            'The channels are documented narratively; their size, selection and effect on bargaining remain unknown.'
        ),
    },
    {
        'id': 'CTX-K06', 'case_ids': ['CTX-C01'],
        'statement': 'The evidence does not support a uniform loss-of-agency account: Eyferth records appreciation of changed marital status and some women’s public prominence, while Hershatter describes broadened rural social worlds and labour-model visibility alongside continued unequal burdens.',
        'evidence_type': 'scholarly-analysis', 'confidence': 'medium', 'causal_status': 'descriptive',
        'sources': [
            support('CTX-S01', 'pp.384, 386, 388', 'Reports attraction to marital reform, differentiated activism and interviewees’ gratitude about status.'),
            support('CTX-S03', 'pp.13–14; notes41/43 at p.27', 'Describes social encounters and public roles during mobilisation while retaining domestic and remuneration inequalities.'),
        ],
        'counterevidence': 'Public recognition was selective and could require exceptional effort; gratitude about marriage is not evidence of adequate material provision or free consent to every work demand.',
        'inference_limits': 'Different outcomes and populations cannot be combined into a net welfare verdict. Hershatter’s broader discussion is not a new matched study of the three Eyferth villages; shared scholarship is disclosed.',
        'test': descriptive('Records counterevidence to an undifferentiated characterisation of actors, without estimating the causal or welfare balance of political change.'),
    },
    {
        'id': 'CTX-K07', 'case_ids': ['CTX-C01'],
        'statement': 'Compared with IND-C07’s pre-1949 hybrid-yarn configuration, this post-1949 episode adds observed access and unpaid-labour pathways to persistence. Continued task performance alone cannot establish technical preference, voluntary participation or a desirable paid occupation.',
        'evidence_type': 'synthesis-inference', 'confidence': 'medium', 'causal_status': 'mechanism-supported',
        'sources': [support('CTX-S01', 'pp.373–374 compared with pp.386–389', 'Contrasts historical background on hybrid inputs with original local findings on access and competing labour demands.')],
        'counterevidence': 'Useful product properties, skills and commercial niches remain possible contributors. IND-C07 already limits claims about voluntary preference; the new evidence extends selection rather than refuting its hybrid observation.',
        'inference_limits': 'Same article as IND-S15, different temporal episodes and evidence bases. No independent replication, pooled prevalence or projection of post-1949 institutions backward. This is an inference about what persistence can establish, not a forecast of present-day repair employment.',
        'test': mechanism(
            'Different feasible choices and different control of labour -> similar visible persistence -> an outcome label alone leaves mechanism and livelihood quality unidentified.',
            'A task-fit explanation could remain sufficient for some earlier households or later niches; the later access evidence does not show it was absent.',
            'Observe comparable households with equivalent accessible substitutes and operator control, then compare continuing production, compensation and exits.',
            'Reopened CTX-S01 pp.373–374 and 386–389; read IND-C07/K20–K22/X03. The later account contains concrete cash, coupon and work-allocation evidence absent from the earlier case’s selected period.',
            'The countercase defeats an inference from persistence alone to desirable work; it does not estimate the share of persistence caused by each pathway or invalidate the earlier hybrid configuration.'
        ),
    },
    {
        'id': 'CTX-K08', 'case_ids': ['CTX-C01'],
        'statement': 'Hershatter’s account distinguishes early PRC support for some women’s textile cooperatives from the narrowing of household selling opportunities and the Great Leap’s attempted collective provision of domestic services. Policy towards women’s work was not one unchanging programme across 1949–1980.',
        'evidence_type': 'scholarly-analysis', 'confidence': 'medium', 'causal_status': 'descriptive',
        'sources': [support('CTX-S03', 'p.12; pp.16–18; notes40/41/50 at p.27', 'Dates distinct institutional arrangements and attempted reorganisation of domestic work.')],
        'counterevidence': 'An initiative’s stated aim does not establish reliable services or release from domestic duties. Later accounts still describe unpaid household work, and the Great Leap episode is not a successful alternative established by this supplement.',
        'inference_limits': 'A periodisation check from a broader synthesis, not an adoption-rate or implementation-effect estimate in Eyferth’s three villages. Note40 shares Eyferth2015; no claim of independent corroboration of household cloth access.',
        'test': descriptive('Distinguishes named policy episodes and limits a uniform-period interpretation; does not infer implementation success.'),
    },
]

cases = [{
    'id': 'CTX-C01',
    'title': 'Guanzhong household textiles under collective agriculture and restricted cloth access',
    'region': ['China', 'Shaanxi', 'Guanzhong', 'Gedatou (Zhouzhi county)', 'Danbei and Zhangli (Xingping county)'],
    'period': '1949–1980; strongest mechanism evidence from mid-1950s procurement/collectivisation through collective-era recollections',
    'domain': ['household textiles', 'state procurement', 'gender and unpaid labour'],
    'outcome': ['continued household production', 'restricted substitute access', 'unequal unpaid work', 'limited commercial niches'],
    'summary': 'Hand production continued amid valued cloth services, scarce cash and rationed substitutes, while women combined household clothing duties with collective work. Local alternatives and agency varied; persistence is not a measure of voluntary preference or occupational opportunity.',
    'stages': {
        'invention': 'No claim of invention; hand textile processes and factory substitutes already existed.',
        'feasibility': 'Household production supplied clothing; technical feasibility did not imply adequate inputs, time, consent or remuneration.',
        'deployment': 'Retrospective interviews and archival interpretation document continued work in three named villages.',
        'diffusion': 'No adoption curve or national denominator. Author’s extension to other cotton-growing areas is a hypothesis.',
        'scaling': 'National factory output and local household use are different measures; this case estimates neither a scaling rate nor a national household-output share.',
        'non-adoption': 'Factory cloth entitlement could fail to become actual purchase because cash and other needs constrained redemption; qualities and social uses also differed.',
        'displacement': 'Later photo captions report the end of hand spinning and continued niche weaving, but no household exit panel or causal timing is established here.',
    },
    'mechanisms': ['ration entitlement versus effective purchase', 'household cash constraints', 'gendered allocation of unpaid work', 'collective labour obligations', 'different cloth services', 'cotton retention and informal exchange'],
    'counterevidence': 'Some households used factory cloth; some women sold handwoven cloth or gained public standing. State policies varied and local leaders sometimes mediated informal cotton access. No single mechanism or uniform welfare outcome follows.',
    'claim_ids': [c['id'] for c in claims], 'source_ids': ['CTX-S01', 'CTX-S03'],
    'episode': {
        'technology_configuration': 'Household spinning, weaving and clothing work using retained or informally obtained cotton, alongside collective field labour and coupon-and-cash access to factory cloth. Do not assume the pre-1949 mixed-yarn configuration for every later household.',
        'task': 'Clothe family members and fulfil locally valued textile exchanges; state authorities also sought cotton procurement and agricultural labour, creating conflicting purposes.',
        'population': 'Primary local evidence: >80 villagers, mostly men and women born 1920–1945, in Gedatou (Zhouzhi), Danbei and Zhangli (Xingping), interviewed about 200 times over 14 weeks in five visits, 2005–2011. Broader policy context in CTX-S03 has a different, nonmatched population.',
        'interval': '1949–1980, separating early PRC years from procurement in 1954 and collectivisation in 1955–1956. Main work/consumption accounts concern the subsequent collective period; later photographs are a limited coda.',
        'contemporary_alternatives': [
            'Purchase rationed factory cloth when coupons, cash and supplies permit; entitlement alone is not access.',
            'Use retained cotton, glean or acquire informally, and produce cloth at home.',
            'Sell coupons or cloth and exchange output for cotton or other necessities; illegal or risky routes were not equally available.',
            'Local gifts and collective cotton distributions; variable and not a guaranteed substitute.',
            'Earlier textile cooperatives or attempted collective domestic services existed in broader histories; local reliability and coverage are not established here.',
            'Reduce clothing consumption or divert time from collective work/rest; these are burdensome adjustments, not necessarily acceptable choices.',
        ],
        'adoption_measure': 'Qualitative continued-use and purchase/resale accounts in a bounded retrospective sample. No consistent person/household-year denominator, national prevalence or common pre/post output share.',
        'observation_limits': 'Oral history recorded decades later, selected villages and surviving interviewees, no acquired original recordings or archived files. Actor motives are reported interpretations. Macro output totals in pp.378–379 require denominator reconciliation and are excluded.',
    },
    'actors': {
        'chooser': 'State planners set procurement and cloth allocation; collective/team leaders allocate work and resources; households decide purchases and exchanges unevenly; women operate and negotiate within these constraints. No unitary household or state preference assumed.',
        'payer': 'Households supply cash or coupons and cotton; women supply much unremunerated textile time. Collective work points and retained household resources differ from a wage for home production.',
        'operator_maintainer': 'Women performing hand spinning, weaving, sewing and related clothing work; detailed loom repair organisation is not observed and must not be inferred as a paid repair role.',
        'affected_nonchooser': 'Women bearing competing work demands, children and dependants needing clothing, and relatives whose access to cloth depends on household allocation.',
        'ability_to_refuse': 'Neither compulsory hand weaving nor unrestricted choice is established. Agricultural obligations, scarce cash, household expectations and sanctions/risk around informal trade narrowed options. Some women negotiated, sold cloth, concealed inputs or held local office; extent of individual refusal rights is unmeasured.',
    },
    'labour': {
        'tasks': 'Collective field duties and cotton cultivation overlapped with unpaid home textile and care work; occasional sales provided a distinct cash route for some.',
        'entry_barriers': 'Textile skills, access to cotton/tools, time after collective duties, market contacts, risk of prohibited trade and household position. No credential or entry-cost series available.',
        'bargaining_ownership': 'State/collectives controlled important inputs, work allocation and legal channels; households exercised additional authority. Women’s operational skill and trading activity do not establish control of all proceeds or capacity to leave.',
        'transition': 'Retrospective work histories span political change, but no tracked cohort transition from home textiles to a paid industrial or repair occupation. Later spinning cessation is not an identified transition rate.',
        'distribution': 'Accounts locate unpaid work/rest burdens among women and document some public roles and commercial exceptions. They do not yield a net group welfare effect, an average individual income or a national gender comparison.',
        'evidence_limit': 'No audited time-use panel, wages for unpaid household work, original interview files, independent national sampling or measured value capture. This case cannot establish an attractive future occupation from task persistence.',
    },
}]

comparisons = [{
    'id': 'CTX-X01',
    'question': 'When household textiles persist alongside factories, does useful task fit, restricted substitution or unequal allocation of labour explain the continuation?',
    'case_ids': ['IND-C07', 'CTX-C01'],
    'useful_similarities': 'Separable spinning/weaving/clothing tasks, household production alongside industrial textiles, and gendered work. Similar visible persistence can conceal different feasible choices and beneficiaries.',
    'important_differences': 'IND-C07 is c.1870–1949 and includes market integration through factory yarn; CTX-C01 is 1949–1980 with its own mid-1950s procurement/collectivisation institutions and local retrospective sample. Product, place, date and institutions are not held constant.',
    'evidence_comparability': 'IND uses inherited historical background and an attributed interwar national output estimate; CTX centres original interviews/archival interpretation from three Guanzhong villages. No pooled denominator, matched before/after effect or common output-share series is defensible.',
    'connections_nonindependence': 'Direct work-level dependence: CTX-S01 and IND-S15 are the EXACT SAME Eyferth2012 article, using different sections and underlying evidence. The histories are temporally connected, not independent replications. CTX-S03 note49 inherits Eyferth2012/2015 for cloth access, and both draw on Hershatter/Gao for wider rural work; original-record overlap beyond named citations is unknown.',
    'omitted_countercases': 'Matched households with sufficient cash and equivalent factory cloth; non-cotton or nonweaving regions; profitable commercial producers with documented control of proceeds; households where men shared textile work; the same households through late-1970s exit.',
    'conclusion_limit': 'The earlier hybrid claim survives. The later episode adds concrete constrained-access and unpaid-labour routes, so persistence alone cannot establish preference, efficiency, consent, welfare or an accessible paid repair/adaptation role. No backward projection or national causal weighting follows.',
}]

nodes = [
    ('CTX-T01', 'Mid-1950s cotton procurement and coupon-based cloth access', 'institution'),
    ('CTX-T02', 'Limited disposable household cash in Zhouzhi accounts', 'resource'),
    ('CTX-T03', 'Purchased factory cloth for household clothing', 'technology'),
    ('CTX-T04', 'Guanzhong household spinning, weaving and clothing work', 'practice'),
    ('CTX-T05', 'Collective agricultural work obligations', 'institution'),
    ('CTX-T06', 'Women operators’ available time and rest', 'resource'),
    ('CTX-T07', 'Household expectations that women provide clothing', 'institution'),
    ('CTX-T08', 'Retained and informally obtained cotton', 'resource'),
    ('CTX-T09', 'Household clothing provision', 'practice'),
]
nodes = [{'id': n, 'label': label, 'kind': kind, 'case_ids': ['CTX-C01']} for n, label, kind in nodes]

def edge(num, src, dst, relation, claim_ids, qualification, alternatives, dispute):
    return {
        'id': f'CTX-E{num:02}', 'from': src, 'to': dst, 'relation': relation,
        'case_ids': ['CTX-C01'], 'claim_ids': claim_ids, 'source_ids': ['CTX-S01'],
        'confidence': 'medium', 'qualification': qualification,
        'basis': 'observed-contribution',
        'scope': {'case_id': 'CTX-C01', 'stage': 'continued deployment under collective-era constraints', 'configuration': 'Named Guanzhong villages and Zhouzhi work/consumption accounts under mid-1950s procurement and later collective arrangements; not all China.'},
        'alternatives': alternatives, 'joint_inputs': [],
        'necessity_rationale': 'No necessity claim', 'dispute': dispute,
    }

edges = [
    edge(1, 'CTX-T01', 'CTX-T03', 'constrains', ['CTX-K02'],
         'Formal access required allocation and purchase; this edge records restricted channels, not a net effect compared with no rationing. Rationing also distributed entitlements.',
         ['Household hand production', 'Informal exchange or gifts', 'Different ration/income policies are counterfactual, not observed treatments'],
         'No identified overall policy effect: ration quantity, cash, prices and household needs interact.'),
    edge(2, 'CTX-T02', 'CTX-T03', 'constrains', ['CTX-K02'],
         'Interviewees linked coupon resale/nonpurchase to scarce disposable cash. A ration coupon was not itself a purchased garment.',
         ['Reduce other spending when possible', 'Sell coupons and make cloth', 'Obtain gifts or other household resources'],
         'Social role and cloth quality differ between reported buyers and nonsellers; no matched comparison.'),
    edge(3, 'CTX-T08', 'CTX-T04', 'enables', ['CTX-K05'],
         'Retained, concealed or exchanged cotton supplied inputs for reported home production; legal retention did not describe all actual access.',
         ['Purchased yarn where accessible', 'Recycled or low-grade fibre', 'Purchased cloth substitutes for home processing'],
         'Input quantities and channel shares are not independently audited; no single channel is claimed necessary.'),
    edge(4, 'CTX-T07', 'CTX-T06', 'constrains', ['CTX-K03'],
         'Reported household expectations added clothing duties to women’s existing claims on time. This is not a claim that those expectations were necessary or sufficient for home production.',
         ['Purchased clothing', 'Other household members provide labour', 'Shared or collective services where effective'],
         'Authority, affection, skill and scarcity overlap; no causal share or universal household rule.'),
    edge(5, 'CTX-T05', 'CTX-T06', 'constrains', ['CTX-K03'],
         'Collective field duties competed for time also needed for domestic work and rest.',
         ['Reduced collective hours or reassignment where permitted', 'Purchasing substitutes', 'Sharing domestic work'],
         'Retrospective accounts do not yield a complete comparable time-use panel or prove identical obligations for every woman.'),
    edge(6, 'CTX-T04', 'CTX-T06', 'constrains', ['CTX-K03'],
         'Accounts describe additional unpaid textile work reducing available rest after other duties; the burden is scoped to the reported configuration.',
         ['Buy adequate cloth', 'Share the task', 'Reduce clothing service or other work'],
         'Not an inherent effect of hand weaving in all settings; these alternatives were not equally feasible.'),
    edge(7, 'CTX-T04', 'CTX-T09', 'enables', ['CTX-K01', 'CTX-K03', 'CTX-K05'],
         'Home textile work provided clothing and social textile goods in the local accounts, while imposing distinct operator costs.',
         ['Factory cloth and purchased garments', 'Gifts and exchange', 'Collective provision when effective'],
         'A productive contribution does not demonstrate a voluntary or compensated livelihood, or a technical necessity.'),
]
graph = {'nodes': nodes, 'edges': edges}

for name, records in [('sources', sources), ('claims', claims), ('cases', cases), ('comparisons', comparisons), ('graph', graph)]:
    (R / f'{name}.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'cases': len(cases), 'sources': len(sources), 'claims': len(claims), 'comparisons': len(comparisons), 'nodes': len(nodes), 'edges': len(edges)}))
