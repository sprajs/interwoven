"""Draw the persistent figure and, optionally, the in-chat exploration from results.json."""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
MEASURES = {
    "count": "Catalogue records",
    "population": "Records per billion person-years",
    "gdp": "Records per 100 trillion international dollars of GDP",
}


def value(row, scope, measure):
    n = row[scope]
    if measure == "count":
        return n
    if measure == "population":
        return n / row["billion_person_years"]
    return 100 * n / row["trillion_intl_dollars"]


def figure(result):
    out = ['<svg xmlns="http://www.w3.org/2000/svg" role="img" width="940" height="350" viewBox="0 0 940 350">',
           '<title>Natural-science records in three consecutive centuries</title>',
           '<desc>Counts and rates per population and GDP for each century from 1720 to 2019. Each row has its own scale.</desc>',
           '<rect width="940" height="350" fill="#fcfbf7"/>',
           '<g font-family="system-ui, sans-serif" fill="#183639">',
           '<text x="28" y="40" font-size="24" font-weight="600">Natural science in the catalogue</text>',
           '<text x="29" y="66" font-size="15">Three equal centuries · primary physical- and life-science records</text>']
    periods = result["century_profiles"]
    for i, row in enumerate(periods):
        x = 248 + i * 228
        out.append(f'<text x="{x}" y="112" font-size="18" font-weight="600">{row["start"]}–{row["end"]-1}</text>')
    for i, (measure, label, units, decimals) in enumerate([
        ("count", "Records", "in 100 years", 0),
        ("population", "Per billion", "person-years", 3),
        ("gdp", "Per 100 trillion", "2021 international $ of GDP", 2),
    ]):
        y = 147 + 62 * i
        out += [f'<text x="28" y="{y+4}" font-size="16" font-weight="600">{label}</text>',
                f'<text x="28" y="{y+23}" font-size="13">{units}</text>']
        values = [value(r, "science", measure) for r in periods]
        for j, v in enumerate(values):
            x = 248 + j * 228
            length = 139 * v / max(values) if max(values) else 0
            out += [f'<rect x="{x}" y="{y}" width="{length:.3f}" height="13" fill="#27786f"/>',
                    f'<text x="{x+length+6:.3f}" y="{y+12}" font-size="15">{v:.{decimals}f}</text>']
    footer = f'Each row has its own scale. Selective catalogue at {result["metadata"]["commit"][:8]} · GDP measures annual output.'
    out += [f'<text x="28" y="327" font-size="14">{escape(footer)}</text>', '</g></svg>']
    return "\n".join(out) + "\n"


def inline(result):
    configs = []
    for key, rows in (("century", result["century_profiles"]), ("twenty", result["twenty_years"])):
        for scope in ("science", "broad", "all"):
            for measure, unit in MEASURES.items():
                points = [{"Period": f'{r["start"]}–{r["end"]-1}', "Value": value(r, scope, measure),
                           "Records": r[scope]} for r in rows]
                spec = {"type": "bar", "x": "Period", "y": "Value", "yLabel": unit, "startAtZero": True,
                        "showValues": key == "century", "sortOrder": "original",
                        "valueFormat": {"style": "decimal", "maximumFractionDigits": 3}}
                if measure != "count":
                    spec["tooltipFields"] = [{"field": "Records", "label": "Record count"}]
                config = {"id": "science-history-bars", "title": unit, "height": 310,
                          "showHeader": False, "spec": spec, "rows": points}
                payload = json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")
                configs.append(f'<script type="application/json" data-viz-chart data-key="{key}-{scope}-{measure}">{payload}</script>')
    return (HERE / "chart-template.html").read_text().replace("<!-- DATA -->", "\n".join(configs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inline", type=Path)
    args = parser.parse_args()
    results = json.loads((HERE / "results.json").read_text())
    (HERE / "three-centuries.svg").write_text(figure(results))
    if args.inline:
        args.inline.write_text(inline(results))
