# Interwoven: a researched tech tree of human civilisation

This is the shared project brief for every agent and provider. Read it before planning, researching, reviewing or changing the app. It states the product we are building; AGENTS.md supplies repository rules, docs/data-model.md the record contract, and docs/research-guide.md the evidence rules. Updated 10 November 2026 following the user's direction.

## What we are building

Build an explorable, evidence-backed graph of human discoveries, inventions and practices: what each achievement made possible, what it depended on, and why it emerged in that place and period. “Tech tree” is the navigation metaphor; history is a branching, reconnecting network, not one inevitable ladder towards the present.

Cover every field, region and era, including independent reinventions, local adaptations, failed approaches, lost capabilities, abandoned branches and later revivals. Do not select only ancestors of modern technology. A gap in research is not proof of absence or loss, and similarity is not proof of continuity.

The reader should be able to start at a breakthrough, follow evidenced prerequisites backwards, inspect descendants forwards, and open the source and uncertainty for each node and connection. Keep the existing map, timeline, index and evidence detail as complementary ways into that graph. Explain unknowns and research coverage visibly.

## Research direction: start from anchors and work backwards

Use a small, varied set of major breakthroughs as research anchors. Select across eras, regions and fields, including a branch without established continuity to the present. Do not assume recent history is inherently more efficient or historically representative. Treat backwards research as a workflow to evaluate, not a proven universal improvement.

For each anchor, ask:

1. What exactly was achieved, by which community, and what dates and places are evidenced?
2. Which materials, tools, processes, instruments, knowledge and organisational practices demonstrably contributed? Distinguish a strict requirement from an enabling improvement, a borrowed technique, and a merely similar earlier achievement.
3. What supported circumstances explain “there and then”: resources, skill, labour, demand, funding, institutions, trade or transmission? Each causal assertion needs its own evidence. Do not make a complete story out of plausible background facts.
4. Which prerequisites already have records, which need bounded new records, and which remain research questions? Extend existing records before creating duplicates.
5. What happened afterwards: spread, adaptation, replacement, abandonment, documented loss or deliberate revival? No descendant in our catalogue means “not yet linked”, not “lost”.

Begin one evidence-backed step backwards for several anchors in parallel. Expand the most informative unresolved frontier next. Stop a branch at an explicit evidence gap, access failure, unresolved direction, or batch limit; retain the question for later. Use forward checks and underrepresented/abandoned branches to counter selection and survival bias.

## Terra High and independent review

The selected routine admission reviewer is **Terra High: `gpt-6.1-terra`, reasoning effort `high`**. Use bounded Terra-low extraction when useful, then a separate Terra-high execution reading the original evidence and current matched records. A proposing/researching agent cannot approve its own additions. Astra-medium is a targeted escalation for consequential unresolved disputes, not a mandatory second pass on every easy fact.

`docs/research-agents/model-policy.json` is the machine-readable routing source. The measured comparison supports Terra High as a provisional quality/cost balance; it does not certify historical accuracy. Other providers may research or implement, but must read this brief, use the same evidence/schema gates, and record their actual model/settings. If Terra High is unavailable, report the limitation; do not silently rename a substitute. The coordinator owns integration and can request a separately identified alternative review.

Reuse verified sources and completed extractions; parallelise independent, non-overlapping work. Bound each wave by named anchors, questions, requests and time. Report newly accepted nodes/events/links, deferrals, review changes, elapsed time and observed usage; distinguish API-equivalent estimates from billing. Compare useful accepted work per time/cost, not raw generated record counts.

## The conflict rule: summary text versus dated events

A fact appearing in a record's description does not mean its supported dated event is already represented. Before rejecting an extension, compare the proposed event's type, subject, date bounds and scope against the actual `events` array. A supported adoption/spread event may extend the existing record even when its description already mentions spread. Do not create a second discovery merely for adoption. If the same event is already present, reject the duplicate extension. Retain broad source dates; never replace them with an invented precise date.

The motivating case is proto-porcelain: the existing record mentions Zhou spread but contains only a Shang emergence event. Review the proposed bounded Zhou spread event under this rule, from the original source, without copying prior model verdicts. Keep the old benchmark labels unchanged; new reviews belong to a new round with a new prompt version.

## Evidence, representation and completion

One record represents one community achieving one thing. Use existing typed links (`requires`, `builds_on`, `uses_instrument`, `uses_process`, `uses_theory`, `adapts`, `transmitted_from`, and other allowed types) only as precisely as the evidence allows. `requires` is not a synonym for “came earlier”. A candidate/insufficient link remains a question and is not drawn as established history. Established consequential causal/transmission links need independent informative corroboration under the review gate; repeated versions of one source do not count twice.

Use existing circumstance and lifecycle facets before inventing a new schema. Never force dates, coordinates, priority, transmission, loss or revival. Every filled facet has research basis and relevant citations. A round is complete when approved changes validate, relevant tests pass, only its own files are committed and pushed, and the app exposes an inspectable result. Preserve other agents' unfinished work.

## Current bounded round

First publish this brief and make the app's purpose/workflow discoverable. Then re-review the proto-porcelain conflict plus matched event controls, and research one prerequisite step for a diverse set of anchors, including a discontinued ancient branch. Do not reopen the 480-call sweep or launch another broad model tournament. Record accepted additions and unresolved next questions so the next round can continue from the frontier.
