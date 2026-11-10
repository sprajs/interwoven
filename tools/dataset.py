"""Read, check and write the dataset in ``data/``.

Everything else in ``tools/`` goes through this module, and so can analysis code:

    from dataset import Dataset
    data = Dataset.load()
    for d in data.discoveries.values(): ...

Only the standard library is used.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date as calendar_date, datetime
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

#: The registers kept as one JSON object per line, sorted by id.
REGISTERS = ("places", "people", "organizations", "societies", "concepts", "leads")
REGISTER_DEFS = {
    "places": "place",
    "people": "person",
    "organizations": "organization",
    "societies": "society",
    "concepts": "concept",
    "leads": "lead",
}

#: Saved copies too large to commit. See tools/evidence.py.
BINARY_EVIDENCE = (".pdf", ".jpg", ".png")

#: The facets of a discovery whose origin is tracked in ``research.basis``.
FACETS = (
    "summary",
    "domain",
    "tier",
    "impact",
    "grain",
    "advance",
    "scale",
    "origin",
    "concept",
    "prompted_by",
    "limit_removed",
    "setting",
    "funding",
    "places",
    "people",
    "organizations",
    "societies",
    "known_from",
    "reception",
    "fate",
    "market",
    "measures",
    "events",
    "links",
)

#: Facets that share another facet's basis, because they are settled together.
FACET_FOLLOWS = {"fields": "domain", "why": "prompted_by", "end_reason": "fate"}


IMPACT = ("reach", "depth", "generativity")


def tier_from(impact: dict) -> int:
    """The tier that a set of impact scores gives. docs/importance.md states the rule."""
    total = sum(impact[key] for key in IMPACT)
    if impact["generativity"] == 3 and total >= 6:
        return 0
    return 1 if total >= 4 else 2 if total >= 2 else 3


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    """Write a record the one way the repository stores it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda row: row["id"])
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def discovery_path(record: dict) -> Path:
    return DATA / "discoveries" / record["domain"].split(".")[0] / f"{record['id']}.json"


def source_path(source_id: str) -> Path:
    return DATA / "sources" / source_id[0] / f"{source_id}.json"


def point_key(point: dict) -> tuple[int, int, int]:
    return (point["year"], point.get("month", 0), point.get("day", 0))


def year_value(point: dict) -> float:
    """A point in time as a number of years, for placing it on an axis."""
    year = point["year"]
    # 1 BCE is the year before 1 CE, so BCE years move up by one to close the gap.
    base = year + 1 if year < 0 else year
    return base + (point.get("month", 1) - 1) / 12 + (point.get("day", 1) - 1) / 365.25


@dataclass
class Dataset:
    schema: dict
    vocab: dict
    taxonomy: dict
    discoveries: dict[str, dict] = field(default_factory=dict)
    sources: dict[str, dict] = field(default_factory=dict)
    registers: dict[str, dict[str, dict]] = field(default_factory=dict)
    population: dict | None = None
    adoption_panels: dict[str, dict] = field(default_factory=dict)
    eurostat_ai_panels: dict[str, dict] = field(default_factory=dict)
    census_refrigeration_panels: dict[str, dict] = field(default_factory=dict)
    #: Where each discovery and source file was read from, for error messages and layout checks.
    paths: dict[str, Path] = field(default_factory=dict)

    @classmethod
    def load(cls, data: Path = DATA) -> "Dataset":
        self = cls(
            schema=read_json(data / "schema.json"),
            vocab=read_json(data / "vocab.json"),
            taxonomy=read_json(data / "taxonomy.json"),
        )
        for path in sorted((data / "discoveries").glob("*/*.json")):
            record = read_json(path)
            self.discoveries[record.get("id", path.stem)] = record
            self.paths["discoveries/" + record.get("id", path.stem)] = path
        for path in sorted((data / "sources").glob("*/*.json")):
            record = read_json(path)
            self.sources[record.get("id", path.stem)] = record
            self.paths["sources/" + record.get("id", path.stem)] = path
        for name in REGISTERS:
            self.registers[name] = {row["id"]: row for row in read_jsonl(data / f"{name}.jsonl")}
        population = data / "reference" / "population.json"
        if population.exists():
            self.population = read_json(population)
        for path in sorted((data / "reference" / "adoption").glob("*.json")):
            self.adoption_panels[path.stem] = read_json(path)
        for path in sorted((data / "reference" / "eurostat-ai").glob("*.json")):
            self.eurostat_ai_panels[path.stem] = read_json(path)
        for path in sorted((data / "reference" / "census").glob("*.json")):
            self.census_refrigeration_panels[path.stem] = read_json(path)
        return self

    # -- lookups ---------------------------------------------------------------------------

    @property
    def fields(self) -> dict[str, dict]:
        return {f["id"]: {**f, "domain": d["id"]} for d in self.taxonomy["domains"] for f in d["fields"]}

    @property
    def domains(self) -> dict[str, dict]:
        return {d["id"]: d for d in self.taxonomy["domains"]}

    def register(self, name: str) -> dict[str, dict]:
        if name == "discoveries":
            return self.discoveries
        if name == "sources":
            return self.sources
        if name == "fields":
            return self.fields
        return self.registers[name]

    def links(self) -> Iterator[tuple[dict, dict]]:
        """Every link with the discovery that holds it."""
        for record in self.discoveries.values():
            for link in record.get("links", []):
                yield record, link

    def event(self, discovery_id: str, event_id: str) -> dict | None:
        record = self.discoveries.get(discovery_id)
        if not record:
            return None
        return next((e for e in record["events"] if e["id"] == event_id), None)

    def earliest_record(self, record: dict) -> dict | None:
        event_id = record["earliest_record"].get("event")
        return self.event(record["id"], event_id) if event_id else None

    # -- checks ----------------------------------------------------------------------------

    def validate(self, check_files: bool = True) -> list[str]:
        """Every problem found, as readable lines. An empty list means the data is sound."""
        errors: list[str] = []
        defs = self.schema["$defs"]

        def check(value: Any, schema: dict, where: str) -> None:
            if "$ref" in schema:
                return check(value, defs[schema["$ref"].rsplit("/", 1)[1]], where)
            if "anyOf" in schema:
                trials = []
                for option in schema["anyOf"]:
                    before = len(errors)
                    check(value, option, where)
                    trials.append(errors[before:])
                    del errors[before:]
                if all(trials):
                    errors.extend(min(trials, key=len))
                return
            kinds = schema.get("type")
            if kinds:
                kinds = [kinds] if isinstance(kinds, str) else kinds
                if not any(_is(value, kind) for kind in kinds):
                    errors.append(f"{where}: expected {' or '.join(kinds)}, found {type(value).__name__}")
                    return
            if "enum" in schema and value not in schema["enum"]:
                errors.append(f"{where}: {value!r} is not one of {schema['enum']}")
            if isinstance(value, str):
                if "minLength" in schema and len(value) < schema["minLength"]:
                    errors.append(f"{where}: must not be empty")
                if "pattern" in schema and not re.search(schema["pattern"], value):
                    errors.append(f"{where}: {value!r} does not match {schema['pattern']}")
                if "vocab" in schema and value not in self.vocab[schema["vocab"]]["values"]:
                    errors.append(f"{where}: {value!r} is not in vocabulary '{schema['vocab']}'")
                if "ref" in schema and value not in self.register(schema["ref"]):
                    errors.append(f"{where}: {value!r} is not in {schema['ref']}")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if "minimum" in schema and value < schema["minimum"]:
                    errors.append(f"{where}: {value} is below {schema['minimum']}")
                if "maximum" in schema and value > schema["maximum"]:
                    errors.append(f"{where}: {value} is above {schema['maximum']}")
            if isinstance(value, list):
                for index, item in enumerate(value):
                    check(item, schema.get("items", {}), f"{where}[{index}]")
            if isinstance(value, dict):
                properties = schema.get("properties", {})
                for key in schema.get("required", []):
                    if key not in value:
                        errors.append(f"{where}: missing '{key}'")
                extra = schema.get("additionalProperties", True)
                for key, item in value.items():
                    if key in properties:
                        check(item, properties[key], f"{where}.{key}")
                    elif extra is False:
                        errors.append(f"{where}: unknown key '{key}'")
                    elif isinstance(extra, dict):
                        check(item, extra, f"{where}.{key}")

        for key, panel in self.adoption_panels.items():
            where = f"reference/adoption/{key}"
            check(panel, defs["chatTelephonePanel"], where)
            if not isinstance(panel, dict):
                continue
            if panel.get("id") != key:
                errors.append(f"{where}: id must match filename")
            seen = set()
            observations = panel.get("observations")
            if not isinstance(observations, list):
                continue
            for index, row in enumerate(observations):
                at = f"{where}.observations[{index}]"
                if not isinstance(row, dict):
                    continue
                country, year = row.get("country"), row.get("year_token")
                if not isinstance(country, str) or not isinstance(year, str):
                    continue
                pair = (country, year)
                if pair in seen:
                    errors.append(f"{at}: duplicate country and year")
                seen.add(pair)
                token = row.get("raw_value")
                if isinstance(token, str):
                    try:
                        expected = telephone_value(token)
                        status = "missing" if expected is None else "reported"
                        if row.get("status") != status or row.get("value") != expected:
                            errors.append(f"{at}: value and status must match the raw token")
                    except ValueError:
                        errors.append(f"{at}: invalid raw telephone value")

        for key, panel in self.census_refrigeration_panels.items():
            at = f"reference/census/{key}"
            check(panel, defs["us1950RefrigerationPanel"], at)
            if not isinstance(panel, dict):
                continue
            if panel.get("id") != key:
                errors.append(f"{at}: id must match filename")
            source = self.sources.get(panel.get("source")) if isinstance(panel.get("source"), str) else None
            if isinstance(source, dict) and panel.get("source_url") != source.get("url"):
                errors.append(f"{at}: source URL must match the source record")
            try:
                calendar_date.fromisoformat(panel.get("source_accessed"))
            except (ValueError, TypeError):
                errors.append(f"{at}: invalid access date")
            rows = panel.get("observations")
            if not isinstance(rows, list):
                continue
            seen: set[str] = set()
            for i, row in enumerate(rows):
                where = f"{at}.observations[{i}]"
                if not isinstance(row, dict):
                    continue
                residence = row.get("residence")
                if isinstance(residence, str):
                    if residence in seen:
                        errors.append(f"{where}: duplicate residence")
                    seen.add(residence)
                fields = ("numerator", "denominator", "percent")
                tokens = [row.get(f + "_token") for f in fields]
                values = [row.get(f) for f in fields]
                if row.get("status") == "missing":
                    if any(x is not None for x in tokens + values):
                        errors.append(f"{where}: missing values and tokens must all be null")
                    continue
                if row.get("status") != "reported":
                    continue
                if not all(isinstance(t, str) for t in tokens):
                    errors.append(f"{where}: reported values require source tokens")
                    continue
                n, d, p = tokens
                if len(n) > 30 or len(d) > 30 or not re.fullmatch(r"(?:0|[1-9]\d{0,2}(?:,\d{3})+|[1-9]\d*)", n) or not re.fullmatch(r"(?:0|[1-9]\d{0,2}(?:,\d{3})+|[1-9]\d*)", d) or not re.fullmatch(r"(?:0|[1-9]\d{0,2})\.\d", p):
                    errors.append(f"{where}: invalid count or percentage token")
                    continue
                numerator, denominator, percentage = int(n.replace(",", "")), int(d.replace(",", "")), Decimal(p)
                if (type(values[0]) is not int or type(values[1]) is not int or
                    not isinstance(values[2], (int, float)) or isinstance(values[2], bool) or
                    not Decimal(str(values[2])).is_finite() or values[0] != numerator or values[1] != denominator or
                    Decimal(str(values[2])) != percentage):
                    errors.append(f"{where}: values must match source tokens")
                if denominator <= 0 or numerator > denominator or percentage > 100:
                    errors.append(f"{where}: invalid numerator, denominator or percentage bounds")
                elif abs(percentage - Decimal(numerator) * 100 / Decimal(denominator)) > Decimal("0.05"):
                    errors.append(f"{where}: published percentage is inconsistent with counts at one decimal")
            if seen != {"total", "urban", "rural_nonfarm", "rural_farm"}:
                errors.append(f"{at}: require exactly the four residence categories")

        # These two narrowly defined survey extracts have different units and populations.
        from import_eurostat_ai import DIMENSIONS, extract as extract_eurostat
        for key, panel in self.eurostat_ai_panels.items():
            at = f"reference/eurostat-ai/{key}"
            if not isinstance(panel, dict):
                errors.append(f"{at}: expected object")
                continue
            dataset = panel.get("dataset")
            definition = {"isoc_eb_ai": "eurostatEnterpriseAiPanel", "isoc_ai_iaiu": "eurostatIndividualAiPanel"}.get(dataset) if isinstance(dataset, str) else None
            if not definition:
                errors.append(f"{at}: unknown Eurostat dataset")
                continue
            check(panel, defs[definition], at)
            if panel.get("id") != key:
                errors.append(f"{at}: id must match filename")
            release = panel.get("release")
            if not isinstance(release, dict):
                continue
            try:
                retrieved = release.get("retrieved")
                if not isinstance(retrieved, str) or calendar_date.fromisoformat(retrieved).isoformat() != retrieved:
                    raise ValueError
            except ValueError:
                errors.append(f"{at}: invalid retrieval date")
            try:
                updated = datetime.fromisoformat(release.get("updated", ""))
                if updated.tzinfo is None or updated.utcoffset() is None:
                    raise ValueError
            except (ValueError, TypeError):
                errors.append(f"{at}: invalid update timestamp")
            source_id = release.get("source")
            source = self.sources.get(source_id, {}) if isinstance(source_id, str) else {}
            source_file = source.get("file", {}) if isinstance(source, dict) else {}
            if source_file.get("path") != release.get("raw_path") or source_file.get("sha256") != release.get("sha256") or source.get("url") != release.get("query_url"):
                errors.append(f"{at}: release query, path and hash must match source")
            rows = panel.get("observations")
            selection = panel.get("selection")
            if not isinstance(rows, list) or not isinstance(selection, dict):
                continue
            query_url = release.get("query_url")
            if isinstance(query_url, str):
                try:
                    url = urlsplit(query_url)
                    params = parse_qs(url.query, keep_blank_values=True, strict_parsing=True)
                    expected_path = "/eurostat/api/dissemination/statistics/1.0/data/" + dataset
                    if (url.scheme != "https" or url.netloc != "ec.europa.eu" or url.path != expected_path
                            or url.fragment or set(params) != set(DIMENSIONS[dataset]) | {"lang"}
                            or params.get("lang") != ["en"]
                            or any(not isinstance(selection.get(k), list) or sorted(params.get(k, [])) != sorted(selection[k]) for k in DIMENSIONS[dataset])):
                        raise ValueError
                except (ValueError, TypeError):
                    errors.append(f"{at}: query dimensions do not match selected dataset")
            seen = set()
            indices = set()
            for n, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                dims = row.get("dimensions")
                if not isinstance(dims, dict) or any(not isinstance(dims.get(k), str) for k in DIMENSIONS[dataset]):
                    continue
                ident = tuple(dims[k] for k in DIMENSIONS[dataset])
                if ident in seen:
                    errors.append(f"{at}.observations[{n}]: duplicate dimension key")
                seen.add(ident)
                index = row.get("index")
                if isinstance(index, int) and not isinstance(index, bool):
                    if index in indices:
                        errors.append(f"{at}.observations[{n}]: duplicate source index")
                    indices.add(index)
                for name, value in dims.items():
                    if not isinstance(selection.get(name), list) or value not in selection[name]:
                        errors.append(f"{at}.observations[{n}]: dimension outside selection")
                value = row.get("value")
                if row.get("status") != ("missing" if value is None else "reported"):
                    errors.append(f"{at}.observations[{n}]: value and missing status disagree")
                if isinstance(value, float) and not math.isfinite(value):
                    errors.append(f"{at}.observations[{n}]: nonfinite percentage")
                if row.get("flag") == "":
                    errors.append(f"{at}.observations[{n}]: empty flag is not a status code")
            if any(not isinstance(selection.get(k), list) or not selection[k] or len(set(x for x in selection[k] if isinstance(x, str))) != len(selection[k]) for k in DIMENSIONS[dataset]):
                errors.append(f"{at}: selection must contain unique nonempty dimension codes")
            if check_files and isinstance(release.get("raw_path"), str) and isinstance(release.get("sha256"), str):
                try:
                    raw_path = ROOT / release["raw_path"]
                    expected = extract_eurostat(raw_path, dataset, release["sha256"])
                    raw = read_json(raw_path)
                    expected_selection = {name: [code for code, _ in sorted(raw["dimension"][name]["category"]["index"].items(), key=lambda item: item[1])] for name in DIMENSIONS[dataset]}
                    if expected_selection != selection or expected != rows:
                        errors.append(f"{at}: observations or selection differ from source response")
                    if raw.get("updated") != release.get("updated") or raw.get("extension", {}).get("datastructure", {}).get("version") != release.get("structure_version"):
                        errors.append(f"{at}: release metadata differs from source response")
                except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                    errors.append(f"{at}: cannot verify source response: {exc}")

        for name, definition in REGISTER_DEFS.items():
            for key, row in self.registers[name].items():
                check(row, defs[definition], f"{name}/{key}")
        for key, parent in ((k, p.get("within")) for k, p in self.registers["places"].items()):
            seen = {key}
            while parent:
                if parent in seen:
                    errors.append(f"places/{key}: 'within' loops back on itself")
                    break
                seen.add(parent)
                parent = self.registers["places"].get(parent, {}).get("within")

        for key, source in self.sources.items():
            where = f"sources/{key}"
            check(source, defs["source"], where)
            path = self.paths[where]
            if path != source_path(key):
                errors.append(f"{where}: belongs at {source_path(key).relative_to(ROOT)}")
            saved = source.get("file")
            if saved and check_files:
                target = ROOT / saved["path"]
                descriptor = Path(str(target) + ".cache.json")
                if target.suffix.lower() in BINARY_EVIDENCE:
                    # Large files are not committed. Their descriptor says how to fetch them, so a
                    # machine without the file is still sound as long as the two records agree.
                    if not descriptor.is_file():
                        errors.append(f"{where}: {saved['path']} has no .cache.json descriptor")
                    elif read_json(descriptor).get("sha256") != saved["sha256"]:
                        errors.append(f"{where}: {saved['path']} and its descriptor give different checksums")
                    if target.is_file() and sha256(target) != saved["sha256"]:
                        errors.append(f"{where}: saved copy {saved['path']} does not match its sha256")
                elif not target.is_file():
                    errors.append(f"{where}: saved copy {saved['path']} is missing")
                elif sha256(target) != saved["sha256"]:
                    errors.append(f"{where}: saved copy {saved['path']} does not match its sha256")

        for key, record in self.discoveries.items():
            where = f"discoveries/{key}"
            check(record, defs["discovery"], where)
            if "domain" in record and self.paths[where] != discovery_path(record):
                errors.append(f"{where}: belongs at {discovery_path(record).relative_to(ROOT)}")
            events = {}
            for event in record.get("events", []):
                if event.get("id") in events:
                    errors.append(f"{where}: event id '{event['id']}' is used twice")
                events[event.get("id")] = event
                date = event.get("date", {})
                if date.get("earliest") and date.get("latest") and point_key(date["earliest"]) > point_key(date["latest"]):
                    errors.append(f"{where}.events.{event.get('id')}: earliest is after latest")
                for point in (date.get("earliest"), date.get("latest")):
                    if point and point.get("year") == 0:
                        errors.append(f"{where}.events.{event.get('id')}: there is no year 0")
            for slot in ("earliest_record", "community_entry"):
                target = (record.get(slot) or {}).get("event")
                if target and target not in events:
                    errors.append(f"{where}.{slot}: no event '{target}'")
            for witness in record.get("witnesses", []):
                if witness.get("event") not in events:
                    errors.append(f"{where}.witnesses: no event '{witness.get('event')}'")
            def evidence_required(item: dict, at: str) -> None:
                evidence = item.get("evidence")
                if not isinstance(evidence, list) or not evidence:
                    errors.append(f"{at}: needs nonempty evidence")
                elif any(not isinstance(e, dict) or not e.get("source") or not e.get("locator") or not e.get("supports") for e in evidence):
                    errors.append(f"{at}: each evidence entry needs source, locator and supports")

            for event_id, event in events.items():
                for index, contribution in enumerate(event.get("contributions", [])):
                    at = f"{where}.events.{event_id}.contributions[{index}]"
                    if sum(k in contribution for k in ("person", "organization", "group")) != 1:
                        errors.append(f"{at}: needs exactly one person, organization or group")
                    evidence_required(contribution, at)

            extended_keys = {"event", "date", "subject", "person", "organization", "lower", "upper", "numerator", "denominator", "denominator_definition", "currency", "money_context", "method"}
            for index, measure in enumerate(record.get("measures", [])):
                at = f"{where}.measures[{index}]"
                if not extended_keys.intersection(measure):
                    continue  # Existing measures retain their original contract.
                evidence_required(measure, at)
                if not measure.get("event") and not measure.get("date"):
                    errors.append(f"{at}: an extended measure needs an event or date")
                if measure.get("event") and measure["event"] not in events:
                    errors.append(f"{at}: no event '{measure['event']}'")
                if not measure.get("status"):
                    errors.append(f"{at}: an extended measure needs status")
                if measure.get("status") == "derived" and not measure.get("method"):
                    errors.append(f"{at}: a derived extended measure needs method")
                if "person" in measure and "organization" in measure:
                    errors.append(f"{at}: use at most one person or organization")
                date = measure.get("date", {})
                if isinstance(date, dict):
                    if date.get("earliest") and date.get("latest") and point_key(date["earliest"]) > point_key(date["latest"]):
                        errors.append(f"{at}.date: earliest is after latest")
                    for point in (date.get("earliest"), date.get("latest")):
                        if isinstance(point, dict) and point.get("year") == 0:
                            errors.append(f"{at}.date: there is no year 0")
                numeric = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
                lower, upper, value = (measure.get(k) for k in ("lower", "upper", "value"))
                if numeric(lower) and numeric(upper) and lower > upper:
                    errors.append(f"{at}: lower is above upper")
                if numeric(value) and ((numeric(lower) and value < lower) or (numeric(upper) and value > upper)):
                    errors.append(f"{at}: value is outside its bounds")
                if ("numerator" in measure) != ("denominator" in measure):
                    errors.append(f"{at}: numerator and denominator must be paired")
                if "numerator" in measure or "denominator" in measure:
                    if not measure.get("denominator_definition"):
                        errors.append(f"{at}: adoption denominator needs a definition")
                    n, d = measure.get("numerator"), measure.get("denominator")
                    if numeric(d) and d <= 0:
                        errors.append(f"{at}: denominator must be positive")
                    if numeric(n) and numeric(d) and n > d:
                        errors.append(f"{at}: numerator exceeds denominator")
            anchor = events.get((record.get("earliest_record") or {}).get("event"))
            entry = events.get((record.get("community_entry") or {}).get("event"))
            if anchor and entry and point_key(anchor["date"]["latest"]) > point_key(entry["date"]["latest"]):
                errors.append(f"{where}: the earliest record is dated after the community entry")
            basis = (record.get("research") or {}).get("basis", {})
            impact = record.get("impact")
            if impact and basis.get("tier") != "reviewed" and all(isinstance(impact.get(k), int) for k in IMPACT) and record.get("tier") != tier_from(impact):
                errors.append(f"{where}: tier {record.get('tier')} does not follow from its impact scores, which give {tier_from(impact)}")
            for facet in basis:
                if facet not in FACETS:
                    errors.append(f"{where}.research.basis: '{facet}' is not a facet")
            for facet in FACETS:
                filled = record.get(facet) not in (None, [], {})
                if filled and facet not in basis:
                    errors.append(f"{where}: '{facet}' has a value and no basis")
                if not filled and basis.get(facet) in ("sourced", "recalled", "reviewed"):
                    errors.append(f"{where}: '{facet}' has a basis and no value")
            for follower, leader in FACET_FOLLOWS.items():
                if record.get(follower) not in (None, [], {}) and leader not in basis:
                    errors.append(f"{where}: '{follower}' has a value and '{leader}' has no basis")
            seen_links = set()
            for index, link in enumerate(record.get("links", [])):
                at = f"{where}.links[{index}]"
                other = link.get("from")
                if other == key:
                    errors.append(f"{at}: a discovery cannot link to itself")
                if (link.get("type"), other, link.get("from_event"), link.get("to_event")) in seen_links:
                    errors.append(f"{at}: duplicates another link")
                seen_links.add((link.get("type"), other, link.get("from_event"), link.get("to_event")))
                if link.get("to_event") and link["to_event"] not in events:
                    errors.append(f"{at}: no event '{link['to_event']}' here")
                if link.get("from_event") and other in self.discoveries and not self.event(other, link["from_event"]):
                    errors.append(f"{at}: no event '{link['from_event']}' on {other}")
                if link.get("status") == "established" and not link.get("evidence"):
                    errors.append(f"{at}: an established link needs evidence")
        return errors


def _is(value: Any, kind: str) -> bool:
    if kind == "null":
        return value is None
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, {"string": str, "array": list, "object": dict}[kind])


def telephone_value(token: str) -> int | None:
    """Parse a CHAT telephone cell without treating blanks as zero."""
    if token == "":
        return None
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise ValueError("invalid telephone token") from exc
    if not value.is_finite() or value < 0 or value != value.to_integral_value():
        raise ValueError("telephone count must be a non-negative integer")
    return int(value)
