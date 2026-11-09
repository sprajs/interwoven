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
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

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

#: The facets of a discovery whose origin is tracked in ``research.basis``.
FACETS = (
    "summary",
    "domain",
    "tier",
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
                if not target.is_file():
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
            anchor = events.get((record.get("earliest_record") or {}).get("event"))
            entry = events.get((record.get("community_entry") or {}).get("event"))
            if anchor and entry and point_key(anchor["date"]["latest"]) > point_key(entry["date"]["latest"]):
                errors.append(f"{where}: the earliest record is dated after the community entry")
            basis = (record.get("research") or {}).get("basis", {})
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
