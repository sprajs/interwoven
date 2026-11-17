"""Freeze the two small world series from the original OWID CSV and CWON workbook.

Usage: python3 economics.py /path/to/global-gdp.csv /path/to/CWON.xlsx
The report links the original downloads. No third-party packages required.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
from xml.etree import ElementTree
import zipfile

HERE = Path(__file__).resolve().parent
GDP_URL = "https://ourworldindata.org/grapher/global-gdp-over-the-long-run.csv?v=1&csvType=full&useColumnShortNames=false"
CWON_URL = "https://datacatalogfiles.worldbank.org/ddh-published-v2/0042066/9/DR0084043/CWON%202024%20Country%20Tool%20012225.xlsx"


def wealth_series(path):
    with zipfile.ZipFile(path) as book:
        strings = ["".join(s.itertext()) for s in ElementTree.fromstring(book.read("xl/sharedStrings.xml"))]
        workbook = ElementTree.fromstring(book.read("xl/workbook.xml"))
        sheet = next(s for s in workbook.findall(".//{*}sheet") if s.get("name") == "reg_bal")
        rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        rels = ElementTree.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels if r.get("Id") == rel_id)
        table = ElementTree.fromstring(book.read("xl/" + target))
    rows = []
    for row in table.findall(".//{*}row"):
        cells = {}
        for cell in row:
            value = cell.findtext("{*}v")
            if value is not None:
                cells[cell.get("r").rstrip("0123456789")] = strings[int(value)] if cell.get("t") == "s" else value
        rows.append(cells)
    assert [rows[1][k] for k in ("A", "B", "C", "E", "AM")] == ["regionname", "unit", "year", "pop", "ncwi"]
    series = {}
    for row in rows[2:]:
        assert row["B"] == "Real chained 2019 US$"
        year = int(row["C"])
        regions = series.setdefault(year, {})
        assert row["A"] not in regions
        regions[row["A"]] = (float(row["AM"]), float(row["E"]))
    assert sorted(series) == list(range(1995, 2021))
    assert len(series[1995]) == 7 and all(s.keys() == series[1995].keys() for s in series.values())
    return [[y, math.fsum(v[0] for v in rs.values()), math.fsum(v[1] for v in rs.values())]
            for y, rs in sorted(series.items())]


def main():
    gdp_path, wealth_path = map(Path, sys.argv[1:])
    with gdp_path.open() as f:
        gdp = [[int(r["Year"]), int(r["GDP"])] for r in csv.DictReader(f)
               if r["Entity"] == "World" and r["Code"] == "OWID_WRL"]
    assert gdp[0][0] == 1 and gdp[-1][0] >= 2020 and all(a[0] < b[0] for a, b in zip(gdp, gdp[1:]))
    payload = {"gdp_source": GDP_URL, "gdp_file_sha256": hashlib.sha256(gdp_path.read_bytes()).hexdigest(),
               "gdp_columns": ["year", "annual_world_gdp_2021_international_dollars"], "gdp": gdp,
               "wealth_source": CWON_URL, "wealth_file_sha256": hashlib.sha256(wealth_path.read_bytes()).hexdigest(),
               "wealth_columns": ["year", "seven_region_wealth_chained_2019_USD", "covered_population"],
               "wealth": wealth_series(wealth_path)}
    (HERE / "economics.json").write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    main()
