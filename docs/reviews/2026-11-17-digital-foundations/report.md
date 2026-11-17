# Dry lithography, the Kirin 950 and early CCD imaging

On 17 November 2026 three parallel Sol researchers followed questions from the [previous digital research wave](../2026-11-17-digital/report.md). A separate Terra High reviewer checked each proposal against its sources. The three batches added **7 discoveries, 16 dated events and 26 sources**. Five new links are established. Four document a contribution to a later technology and one identifies related process variants. Three more links remain candidates. Two existing discoveries and one earlier event were updated. [Interactive chronology and source passages](view.html) · [Counts by investigation](metrics.json)

## The dry scanner inside the immersion prototype

ASML adapted the lens and platform of its dry 193 nm AT:1150 to build the AT:1150i. The dual-stage platform had already shipped in the AT:750 by September 2001. It let the new scanner measure one wafer in air while exposing another through water. ASML’s 2003 presentation identifies the converted lens, the added liquid handling and the results of a dry-to-wet comparison. An IBM-led study subsequently measured the improvement in depth of focus. The surviving evidence identifies the platform and prototype. The particular scanner used in TSMC’s 2004 SRAM trial remains unknown. [ASML slides, exhibit 99.13, slides 28 and 38–39](https://www.sec.gov/Archives/edgar/data/937966/000095017203003534/lon1248.txt) · [IBM-led experiment](https://research.ibm.com/publications/immersion-lithography-new-opportunities-for-semiconductor-manufacturing) · [Review](reviews/dry.json)

## A manufactured Kirin 950 on TSMC 16FF+

HiSilicon specifies 16FF+ for the Kirin 950. TechInsights independently identified that process on a Hi3650 die extracted from a Huawei Mate 8. TSMC dates volume production of 16FF+ to mid-2015. The Mate 8 went on sale in China on 9 December 2015. A December 2015 package teardown and the later die analysis examined separate phones. TSMC’s base 16FF and enhanced 16FF+ belong to the same process family. Which individual fabrication steps carried over remains open. [HiSilicon specification](https://www.hisilicon.com/cn/products/kirin/kirin-flagship-chips/kirin-950) · [TechInsights die analysis](https://www.techinsights.com/products/sce-1608-801) · [TSMC annual report](https://investor.tsmc.com/static/annualReports/2015/english/e_2_2.html) · [Review](reviews/kirin.json)

## From moving charge to recording an image

Bell Labs’ April 1970 experiment measured charge transfer. Its August paper explicitly reported an eight-bit device working as an optical line imager. George Smith’s Nobel lecture reproduces the oscilloscope image. The 1971 96-element sensor scanned text and pictures one line at a time. By 22 September 1972, Bell Labs had shown an image from a 128 × 106 area sensor. These experiments produced analog images. Bell authors describe design continuity between the prototypes. Independent sources verify the designs and leave two specific claims open, the wiring inherited by the 96-element sensor and the path from its paper’s proposed frame store to the working area sensor. [August 1970 paper](https://doi.org/10.1063/1.1653327) · [Smith, figure 9](https://www.nobelprize.org/uploads/2018/06/smith_lecture.pdf#page=7) · [Area-sensor images, figure 4](https://people.eecs.berkeley.edu/~sequin/PAPERS/1973_CCD-Sensor_IEEE-T-ED.pdf#page=4) · [Review](reviews/ccd.json)

## Publication and verification

| Batch | First verified on main, UTC | Published commit |
|---|---|---|
| Dry lithography | 22:49:16 | [3be33d4](https://github.com/sprajs/interwoven/commit/3be33d4603df2522c74e070f0e3ee4f74be0cdfa) |
| Kirin 950 | 22:50:26 | [930b900](https://github.com/sprajs/interwoven/commit/930b90062e610c6f8cc61bd0fe09cfc9d145d7b6) |
| CCD imaging | 22:51:28 | [19cb293](https://github.com/sprajs/interwoven/commit/19cb29356f68ba7a244c9bf266a283ef7ffd34fc) |

The last batch reached the remote 8 minutes 47 seconds after the first researcher started. The six worker and reviewer executions recorded 33,657,342 input tokens, including 32,627,328 cached input tokens, and 62,730 output tokens. These figures exclude the coordinator. Billing data was unavailable. The reader verifies the hashes of all 38 reviewed files against the published data snapshot and checks each proposal’s ancestry. Counts include only changes from the three reviewed proposals. [Publication and execution records](publication.json)

Each batch passed dataset validation and compiled for the app before its push. The combined data passed 178 Python tests, 53 app tests and the production build. Regenerate the counts and evidence reader with `python3 docs/reviews/2026-11-17-digital-foundations/render.py`.
