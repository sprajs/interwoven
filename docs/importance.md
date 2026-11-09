# Judging importance

Every discovery is scored on three questions. The scores decide its tier, guide what to research next, and let a stone tool and a transistor be compared on the same terms.

The scores describe **consequences**, which can be compared across any span of time. They do not describe fame, cleverness or how much evidence survives.

## The three scores

Each is a whole number from 0 to 3, stored in `impact`.

### Reach: how much of humanity came to live with it

Count the people whose lives it touched at its widest, as a share of everyone alive then. Count only what descended from this achievement, in this community.

| Score | Meaning | Examples |
| --- | --- | --- |
| 0 | One community, workshop, court or research group | A single observatory's instrument; one valley's irrigation rules |
| 1 | One society or region, or one profession across several | Inka khipu accounting; the slide rule among engineers |
| 2 | Many societies across a continent, or most of one civilisation, for generations | Nixtamalised maize across Mesoamerica; the Roman arch |
| 3 | Most of humanity, in most regions | Pottery from East Asia; paper; the germ theory of disease |

### Depth: how much it changed what those people could do or know

| Score | Meaning | Examples |
| --- | --- | --- |
| 0 | A variant or small refinement. Life went on as before | A new glaze colour; a second copy of a known instrument |
| 1 | A clear improvement to something people already did: better, cheaper, safer or more exact | The basic lining for Bessemer converters; logarithm tables to more places |
| 2 | A new capability, or an improvement so large that the activity was reorganised around it | The telescope; the magnetic compass; vaccination |
| 3 | A change in the basis of a way of life or of understanding: how people feed themselves, stay alive, move, communicate, organise, or what they take the world to be | Farming; writing; printing; steam power; natural selection |

### Generativity: how much later discovery rested on it

| Score | Meaning | Examples |
| --- | --- | --- |
| 0 | Nothing later is known to rest on it | An abandoned design; an isolated reinvention that was not passed on |
| 1 | A few direct successors or improvements | One instrument and the improved versions of it |
| 2 | A whole line of work or a field grew from it | Chain-termination sequencing; the Newcomen engine |
| 3 | Many fields, over many generations. It became a platform that unrelated work stood on | Metal smelting; positional numerals; the calculus; the transistor |

## Rules for scoring

1. **Score this record, not the idea in general.** The same thing reached twice is two records with two sets of scores. Writing in Mesopotamia has descendants across half the world. Writing in Mesoamerica changed its own societies as deeply and reached far fewer people. Depth can match while reach and generativity differ.
2. **Count forward from the achievement.** Reach and generativity look at what followed from it, however long that took. A recent discovery is scored on what has followed so far.
3. **Use shares, not head-counts.** A million users meant most of humanity in 10,000 BCE and almost nobody in 2000. Reach is a share of the people alive at the time.
4. **Do not reward documentation.** A well-recorded minor instrument scores below an unrecorded revolution in how people ate.
5. **Do not reward the region or the era.** Ask whether the score would change if the same consequences had followed somewhere else or three thousand years earlier. If it would, the score is wrong.
6. **When torn between two scores, take the lower.** Raise it when evidence arrives.
7. **Say where the scores come from.** `research.basis.impact` is `recalled` until a source supports the judgement.

## Tier

The tier is worked out from the scores. Add the three for a total from 0 to 9.

| Tier | Rule | Meaning |
| --- | --- | --- |
| 0 | Generativity 3 and a total of 7 or more | Later work in several fields or over many generations visibly depended on it |
| 1 | Total of 5 or more | A major contribution |
| 2 | Total of 3 or 4 | A bounded contribution |
| 3 | Total of 2 or less | Fine detail, a single instance or a witness |

A tier that a person has reviewed stands as it is, with `research.basis.tier` set to `reviewed`. Otherwise `tools/validate.py` requires the tier to match the scores.

## Grain

`grain` says how large a thing one record stands for. It keeps like with like when counting.

| Grain | Meaning | Examples |
| --- | --- | --- |
| `capability` | A community gained the ability to do or understand something new | Rice farming in the Yangtze basin; bronze casting in Shang China; heliocentric astronomy |
| `improvement` | A notable step within a capability that already existed | The separate condenser; the basic Bessemer lining |
| `instance` | One object, site, trial or text that shows a capability at work | One aqueduct; one marine timekeeper; one experiment |

Capabilities are the skeleton of the tree. When adding to the dataset, fill in capabilities first. Improvements and instances hang from them with `part_of` or `builds_on` links.

## Choosing what to add

A good next record is one of these, in this order:

1. **A capability the dataset lacks entirely.** `python3 tools/coverage.py --grid` shows which fields, regions and eras are empty.
2. **Another origin of a capability already recorded.** If farming, metalworking, writing, pottery, boats or the calendar has one record, the other places that reached it separately belong too, each with its own date, place and consequences.
3. **A missing link in a chain.** Something a recorded discovery depended on that has no record. `research.missing_prerequisites` lists the known ones.
4. **An improvement or instance** that explains how a capability changed.

Prefer the thing with large consequences over the thing with a famous name. Prefer what people did every day over what a court displayed once. Give every region and era the same question: what did people here become able to do, and what followed?
