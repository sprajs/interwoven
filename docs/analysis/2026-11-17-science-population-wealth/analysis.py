"""Rebuild catalogue-rate analysis from a named Git snapshot, using only the standard library."""
import argparse
from bisect import bisect_left
from collections import Counter
import csv
from functools import cache
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from discovery_trend_audit import git, person_years, snapshot

SCALES = ("centuries", "billion_person_years", "trillion_intl_dollars")
WIDTHS = (20, 50, 100, 200)
START, END = 1000, 2020


def interpolate_annual(anchors):
    """Match observed annual output exactly; interpolate positive levels in log space."""
    annual = dict(anchors)
    for (a, x), (b, y) in zip(anchors, anchors[1:]):
        for year in range(a + 1, b):
            annual[year] = x * (y / x) ** ((year - a) / (b - a))
    return annual


def two_tails(log_weights, observed):
    """Conservative exact double-minimum-tail p; normalize in log space."""
    peak = max(log_weights)
    mass = [math.exp(x - peak) for x in log_weights]
    tail = min(math.fsum(mass[:observed + 1]), math.fsum(mass[observed:]))
    return min(1., 2 * tail / math.fsum(mass))


def log_binomial(n, p):
    return [math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
            + k * math.log(p) + (n - k) * math.log1p(-p) for k in range(n + 1)]


def level_test(counts, exposures):
    n = sum(counts)
    return two_tails(log_binomial(n, exposures[1] / sum(exposures)), counts[1])


def curvature_test(counts, exposures):
    """Condition on sum and linear time score: both nuisance parameters cancel."""
    n = sum(counts)
    score = counts[1] + 2 * counts[2]
    low, high = max(0, score - n), score // 2
    weights = []
    for last in range(low, high + 1):
        possible = (n - score + last, score - 2 * last, last)
        weights.append(sum(k * math.log(e) - math.lgamma(k + 1)
                           for k, e in zip(possible, exposures)))
    return two_tails(weights, counts[2] - low)


def fixed_interval(counts, exposures, alpha=0.05):
    """Invert exact binomial tails (Clopper-Pearson), then convert odds to a rate ratio."""
    k, n = counts[1], sum(counts)
    if n == 0:
        return [0., None]
    result = []
    for lower in (True, False):
        lo, hi = 0., 1.
        for _ in range(52):
            p = (lo + hi) / 2
            mass = [math.exp(x) for x in log_binomial(n, p)]
            if lower:
                go_right = math.fsum(mass[k:]) < alpha / 2
            else:
                go_right = math.fsum(mass[:k + 1]) > alpha / 2
            if go_right:
                lo = p
            else:
                hi = p
        prob = (lo + hi) / 2
        result.append(prob / (1 - prob) * exposures[0] / exposures[1])
    return [0. if k == 0 else result[0], None if k == n else result[1]]


def holm(tests):
    running = 0.
    for index, test in enumerate(sorted(tests, key=lambda t: t["p"])):
        running = max(running, (len(tests) - index) * test["p"])
        test["p_holm"] = min(1., running)


def dates(rows, key="year"):
    return sorted(r[key] for r in rows if r[key] is not None)


def count(years, a, b):
    return bisect_left(years, b) - bisect_left(years, a)


def analyse(revision, economics):
    meta, rows, pop = snapshot(revision)
    taxonomy = json.loads(git("show", meta["commit"] + ":data/taxonomy.json"))
    domains = {d["id"] for d in taxonomy["domains"] if d["group"] == "understanding"}
    science = [r for r in rows if r["domain"] in domains]
    all_dates, science_dates = dates(rows), dates(science)
    broad = [r for r in rows if r["domain"] in domains | {"mathematics", "measurement", "health"}]
    broad_dates = dates(broad)
    world = pop["series"]["world"]
    gdp = interpolate_annual(economics["gdp"])
    stock = {y: w for y, w, _ in economics["wealth"]}

    @cache
    def exposure(a, b):
        return {"centuries": (b - a) / 100,
                "billion_person_years": person_years(world, a, b) / 1e9,
                "trillion_intl_dollars": math.fsum(gdp[y] for y in range(a, b)) / 1e12 if a >= min(gdp) else None}

    def period(a, b):
        measures = exposure(a, b)
        n = count(science_dates, a, b)
        return {"start": a, "end": b, "science": n, "broad": count(broad_dates, a, b),
                "all": count(all_dates, a, b),
                **measures, "rates": {k: n / e if e else None for k, e in measures.items()}}

    def contrast(a, width, scale, kind):
        size = 2 if kind == "level" else 3
        spans = [(a + i * width, a + (i + 1) * width) for i in range(size)]
        counts = [count(science_dates, x, y) for x, y in spans]
        exposures = [exposure(x, y)[scale] for x, y in spans]
        rates = [n / e for n, e in zip(counts, exposures)]
        p = level_test(counts, exposures) if size == 2 else curvature_test(counts, exposures)
        direction = ("rise" if rates[1] >= rates[0] else "fall") if size == 2 else (
            "downward bend" if rates[1] ** 2 > rates[0] * rates[2] else "upward bend")
        return {"kind": kind, "scale": scale, "start": a, "width": width, "direction": direction,
                "counts": counts, "rates": rates, "p": p}

    tests = [contrast(a, w, scale, kind) for scale in SCALES for w in WIDTHS
             for kind, size in (("level", 2), ("curvature", 3))
             for a in range(START, END - size * w + 1, 10)]
    wealth_halves = [(1995, 2008), (2008, 2021)]
    stock_counts = [count(science_dates, a, b) for a, b in wealth_halves]
    stock_exposures = [math.fsum(stock[y] for y in range(a, b)) / 1e15 for a, b in wealth_halves]
    stock_rates = [n / e for n, e in zip(stock_counts, stock_exposures)]
    stock_test = {"kind": "wealth", "scale": "quadrillion_USD_years", "counts": stock_counts,
                  "exposures": stock_exposures, "rates": stock_rates, "p": level_test(stock_counts, stock_exposures),
                  "ratio": stock_rates[1] / stock_rates[0] if stock_rates[0] else None,
                  "fixed_ratio_95ci": fixed_interval(stock_counts, stock_exposures)}
    tests.append(stock_test)
    holm(tests)
    groups = {}
    for t in tests[:-1]:
        key = (t["scale"], t["kind"], t["direction"])
        if key not in groups or t["p"] < groups[key]["p"]:
            groups[key] = t

    best = list(groups.values())
    for t in best:
        if t["kind"] == "level":
            a, w = t["start"], t["width"]
            es = [exposure(a + i*w, a + (i+1)*w)[t["scale"]] for i in (0, 1)]
            t["simultaneous_ratio_95ci"] = fixed_interval(t["counts"], es, 0.05 / len(tests))
    scopes = {"primary": science_dates, "broad": broad_dates, "all": all_dates,
              "earliest_if_bounded": sorted(r["year"] if r["earliest"] is None else r["earliest"] for r in science),
              "known_dates": dates([r for r in science if r["date_status"] == "known"]),
              "bounded_dates": dates(science, "earliest")}
    sensitivity = []
    for key in SCALES:
        for direction in ("rise", "fall"):
            t = groups[key, "level", direction]
            a, w = t["start"], t["width"]
            spans = ((a, a+w), (a+w, a+2*w))
            effects = {}
            for name, years in scopes.items():
                ns = [count(years, x, y) for x, y in spans]
                e0, e1 = [exposure(x, y)[key] for x, y in spans]
                effects[name] = {"counts": ns, "ratio": ns[1] / e1 / (ns[0] / e0) if ns[0] else None}
            sensitivity.append({"scale": key, "direction": direction, "start": a, "width": w, "scopes": effects})

    decades = [period(y, y + 10) for y in range(1820, END, 10)]
    # Descriptive rank correlations; ties receive their average rank.
    def ranks(values):
        ordered = sorted(values)
        return [bisect_left(ordered, v) + (ordered.count(v) + 1) / 2 for v in values]
    drivers = {"population": [d["billion_person_years"] / 10 for d in decades],
               "gdp": [d["trillion_intl_dollars"] / 10 for d in decades],
               "gdp_per_person": [1000 * d["trillion_intl_dollars"] / d["billion_person_years"] for d in decades],
               "records": [d["science"] for d in decades]}
    def rho(x, y):
        return statistics.correlation(ranks(x), ranks(y))
    associations = {k: rho(v, drivers["records"]) for k, v in drivers.items() if k != "records"}
    associations["population_vs_gdp_per_person"] = rho(drivers["population"], drivers["gdp_per_person"])
    record_changes = [v-u for u, v in zip(drivers["records"], drivers["records"][1:])]
    change_associations = {k: rho([math.log(y/x) for x, y in zip(v, v[1:])], record_changes)
                           for k, v in drivers.items() if k != "records"}

    old = [period(a, b) for a, b in [(-10000, 1), (1, 1000), (1000, 1500), (1500, 1600),
                                     (1600, 1700), (1700, 1800), (1800, 1900), (1900, 1950), (1950, 2000), (2000, 2020)]]
    previous = [period(1960, 1980), period(1980, 2000)]
    earlier, later = previous
    previous_tests = {}
    for key in SCALES:
        ns = [r["science"] for r in previous]
        es = [r[key] for r in previous]
        previous_tests[key] = {"ratio": later["rates"][key] / earlier["rates"][key],
                               "fixed_ratio_95ci": fixed_interval(ns, es), "nominal_p": level_test(ns, es)}
    century_profiles = []
    for a in (1720, 1820, 1920):
        members = [r for r in science if a <= r["year"] < a + 100]
        century_profiles.append({**period(a, a + 100), "fields": dict(Counter(r["domain"] for r in members)),
                                 "physical_science_fields": dict(Counter(r["field"] for r in members
                                                                        if r["domain"] == "physical-sciences")),
                                 "electronics": sum(a <= r["year"] < a + 100 and r["domain"] == "electronics" for r in rows),
                                 "unique_anchor_years": len({int(r["year"]) for r in members})})
    first, middle, last = century_profiles
    per_person = "billion_person_years"
    baseline = {"observed": last["science"],
                "at_first_rate": last[per_person] * first["rates"][per_person],
                "at_middle_rate": last[per_person] * middle["rates"][per_person],
                "last_to_first_rate_ratio": last["rates"][per_person] / first["rates"][per_person],
                "ordinary_95ci": fixed_interval([first["science"], last["science"]],
                                                [first[per_person], last[per_person]])}
    return {"metadata": meta, "domains": sorted(domains), "science_count": len(science),
            "science_date_status": dict(Counter(r["date_status"] for r in science)),
            "science_unbounded": sum(r["earliest"] is None for r in science),
            "science_before_10000_bce": count(science_dates, -math.inf, -10000),
            "science_from_2020": count(science_dates, 2020, math.inf),
            "economics_sha256": hashlib.sha256((HERE / "economics.json").read_bytes()).hexdigest(),
            "eras": old, "century_profiles": century_profiles, "per_person_baseline_comparison": baseline,
            "twenty_years": [period(y, y+20) for y in range(1500, END, 20)],
            "decade_rank_correlations": associations,
            "decade_change_rank_correlations": change_associations,
            "wealth": stock_test, "wealth_growth": stock[2020] / stock[1995] - 1,
            "test_count": len(tests), "best_tests": best, "sensitivity": sensitivity,
            "detections": [t for t in tests[:-1] if t["p_holm"] <= 0.05],
            "1980_comparison": {"periods": previous, "tests": previous_tests},
            "field_counts_1980_1999": dict(Counter(r["domain"] for r in rows if 1980 <= r["year"] < 2000))}, tests


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--revision", required=True)
    p.add_argument("--scan-csv", type=Path, help="Optional complete search grid")
    args = p.parse_args()
    result, tests = analyse(args.revision, json.loads((HERE / "economics.json").read_text()))
    (HERE / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if args.scan_csv:
        with args.scan_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, ["kind", "scale", "start", "width", "direction", "counts", "rates", "p", "p_holm"], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(tests)


if __name__ == "__main__":
    main()
