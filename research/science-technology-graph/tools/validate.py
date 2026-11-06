#!/usr/bin/env python3
"""Validate graph records, source references and local evidence files.

Run ``python3 tools/validate.py --json`` from the graph repository. Review
concerns are reported separately from errors; ``--strict-concerns`` makes them
fail the command too. The standard-library validator always runs. An installed
jsonschema package supplies an additional independent check unless disabled.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
import sys

KINDS = {"nodes": "node", "events": "event", "relationships": "relationship", "sources": "source"}
LIFECYCLE = (
    "invention", "first_commercial_availability", "practical_deployment", "adoption",
    "discovery", "observation", "formulation", "publication", "experimental_confirmation",
    "acceptance", "decline", "withdrawal", "end_of_use", "abandonment", "revival",
)
SCIENTIFIC = {"discovery", "observation", "formulation", "publication", "presentation", "experimental_confirmation", "acceptance"}
DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def issue(path, message, code="invalid"):
    return {"path": path, "code": code, "message": message}


def _is_type(value, kind):
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda: isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": lambda: isinstance(value, bool),
        "null": lambda: value is None,
    }[kind]()


def schema_errors(value, schema, root=None, path="$", errors=None):
    """Evaluate the Draft 2020-12 subset used by the bundled schemas.

    Unknown keywords fail closed, so editing a schema cannot silently bypass the
    dependency-free validator. This is deliberately not a general schema engine.
    """
    if errors is None:
        errors = []
    root = schema if root is None else root
    if isinstance(schema, bool):
        if not schema:
            errors.append(issue(path, "value is forbidden by schema", "schema"))
        return errors
    supported = {"$schema", "$id", "$defs", "$ref", "title", "description", "type", "const", "enum", "required", "properties", "additionalProperties", "items", "minItems", "uniqueItems", "minLength", "pattern", "format", "minimum", "maximum", "anyOf", "allOf", "oneOf", "not", "if", "then", "else"}
    unknown = set(schema) - supported
    if unknown:
        errors.append(issue(path, "unsupported schema keywords: " + ", ".join(sorted(unknown)), "schema_configuration"))
        return errors
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            errors.append(issue(path, "only local schema references are supported", "schema_configuration"))
            return errors
        target = root
        for token in ref[2:].split("/"):
            target = target[token.replace("~1", "/").replace("~0", "~")]
        schema_errors(value, target, root, path, errors)
    if "type" in schema and not _is_type(value, schema["type"]):
        errors.append(issue(path, f"expected {schema['type']}, got {type(value).__name__}", "schema"))
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(issue(path, f"must equal {schema['const']!r}", "schema"))
    if "enum" in schema and value not in schema["enum"]:
        errors.append(issue(path, f"must be one of {schema['enum']!r}", "schema"))
    if "not" in schema and not schema_errors(value, schema["not"], root, path):
        errors.append(issue(path, "value/field combination is forbidden", "schema"))
    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            matches = sum(not schema_errors(value, branch, root, path) for branch in schema[keyword])
            if matches == 0 or (keyword == "oneOf" and matches != 1):
                errors.append(issue(path, f"must satisfy {'one' if keyword == 'oneOf' else 'at least one'} allowed shape", "schema"))
    for branch in schema.get("allOf", []):
        schema_errors(value, branch, root, path, errors)
    if "if" in schema:
        branch = "else" if schema_errors(value, schema["if"], root, path) else "then"
        if branch in schema:
            schema_errors(value, schema[branch], root, path, errors)
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(issue(path + "." + key, "required field is missing", "required"))
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                schema_errors(item, properties[key], root, path + "." + key, errors)
            elif schema.get("additionalProperties") is False:
                errors.append(issue(path + "." + key, "unexpected field", "schema"))
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(issue(path, f"requires at least {schema['minItems']} item(s)", "schema"))
        if schema.get("uniqueItems"):
            keys = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(keys) != len(set(keys)):
                errors.append(issue(path, "duplicate entries are not allowed", "duplicate_reference"))
        if "items" in schema:
            for i, item in enumerate(value):
                schema_errors(item, schema["items"], root, f"{path}[{i}]", errors)
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(issue(path, "must not be empty", "schema"))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(issue(path, f"does not match {schema['pattern']!r}", "schema"))
        if schema.get("format") == "date":
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                    raise ValueError
                date.fromisoformat(value)
            except ValueError:
                errors.append(issue(path, "expected a valid YYYY-MM-DD date", "date"))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(issue(path, f"must be >= {schema['minimum']}", "schema"))
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(issue(path, f"must be <= {schema['maximum']}", "schema"))
    return errors


def null_errors(value, path):
    errors = []
    if value is None:
        errors.append(issue(path, "null is ambiguous; use an explicit status or omit the optional field", "null"))
    elif isinstance(value, float) and not math.isfinite(value):
        errors.append(issue(path, "non-finite numbers are not JSON values", "non_json_number"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(null_errors(item, path + "." + key))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            errors.extend(null_errors(item, f"{path}[{i}]"))
    return errors


def _walk_evidence(value, path):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence" and isinstance(item, list):
                for i, entry in enumerate(item):
                    if isinstance(entry, dict) and "source_id" in entry:
                        yield entry, f"{path}.evidence[{i}]"
            else:
                yield from _walk_evidence(item, path + "." + key)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from _walk_evidence(item, f"{path}[{i}]")


def _time(bound, latest=False):
    return (bound["year"], bound.get("month", 12 if latest else 1), bound.get("day", 31 if latest else 1))


def _date_checks(record, path, errors, concerns):
    d = record["date"]
    if "earliest" not in d or "latest" not in d:
        return
    for name in ("earliest", "latest"):
        b = d[name]
        month, day = b.get("month"), b.get("day")
        if month is not None and day is not None:
            # The contract does not choose Julian vs Gregorian leap rules.
            maximum = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[month - 1]
            if day > maximum:
                errors.append(issue(path + ".date." + name, "day is impossible for this month", "date"))
        if d["precision"] == "day" and (month is None or day is None):
            errors.append(issue(path + ".date." + name, "day precision requires month and day", "date"))
        if d["precision"] == "month" and month is None:
            errors.append(issue(path + ".date." + name, "month precision requires month", "date"))
    if _time(d["earliest"]) > _time(d["latest"], True):
        errors.append(issue(path + ".date", "earliest bound follows latest bound", "date_order"))
    if d["status"] == "known" and d["earliest"] != d["latest"]:
        concerns.append(issue(path + ".date", "known has unequal bounds; consider bounded or explain the precision convention", "known_range"))


def validate_records(records, schema_path=None, optional_jsonschema=True):
    """Return errors, review concerns, coverage counts for in-memory records.

    Does not mutate inputs or infer lifecycle acceptance from historical review.
    """
    schema_path = Path(schema_path or DEFAULT_ROOT / "schema.json")
    schema = _read_json(schema_path.read_text())
    schemas = {kind: schema["$defs"][singular] for kind, singular in KINDS.items()}
    result = {"valid": False, "errors": [], "concerns": [], "counts": {}, "jsonschema_backend": "stdlib"}
    errors, concerns = result["errors"], result["concerns"]
    optional = None
    if optional_jsonschema:
        try:
            import jsonschema
            optional = jsonschema
            result["jsonschema_backend"] = "stdlib + jsonschema"
        except ImportError:
            pass
    indexes, valid_ids = {}, {}
    for kind in KINDS:
        indexes[kind], valid_ids[kind] = {}, set()
        for i, record in enumerate(records.get(kind, []), 1):
            path = f"{kind}.jsonl:{i}"
            local_errors = null_errors(record, path) + schema_errors(record, schemas[kind], root=schema, path=path)
            if optional is not None:
                record_schema = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/" + KINDS[kind]}
                for e in optional.Draft202012Validator(record_schema, format_checker=optional.FormatChecker()).iter_errors(record):
                    suffix = "".join(f"[{p}]" if isinstance(p, int) else "." + p for p in e.absolute_path)
                    if not local_errors:
                        local_errors.append(issue(path + suffix, e.message, "jsonschema"))
            errors.extend(local_errors)
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                continue
            rid = record["id"]
            if rid in indexes[kind]:
                errors.append(issue(path + ".id", f"duplicate ID {rid!r} in {kind}.jsonl", "duplicate_id"))
            else:
                indexes[kind][rid] = (record, path)
                if not local_errors:
                    valid_ids[kind].add(rid)
    nodes, events, sources = indexes["nodes"], indexes["events"], indexes["sources"]
    for kind in KINDS:
        for rid, (record, path) in indexes[kind].items():
            for evidence, ep in _walk_evidence(record, path):
                if not isinstance(evidence["source_id"], str) or evidence["source_id"] not in sources:
                    errors.append(issue(ep + ".source_id", f"unknown source {evidence['source_id']!r}", "dangling_source"))
            provenance = record.get("provenance")
            if isinstance(provenance, dict) and isinstance(provenance.get("source_ids"), list):
                for i, source_id in enumerate(provenance["source_ids"]):
                    if not isinstance(source_id, str) or source_id not in sources:
                        errors.append(issue(f"{path}.provenance.source_ids[{i}]", f"unknown source {source_id!r}", "dangling_source"))
    for eid in sorted(valid_ids["events"]):
        event, path = events[eid]
        if event["node_id"] not in nodes:
            errors.append(issue(path + ".node_id", f"unknown node {event['node_id']!r}", "dangling_node"))
        _date_checks(event, path, errors, concerns)
    for nid in sorted(valid_ids["nodes"]):
        node, path = nodes[nid]
        owned = {eid for eid, (e, _) in events.items() if e.get("node_id") == nid}
        listed = set(node["event_ids"])
        for eid in sorted(listed - owned):
            message = f"unknown event {eid!r}" if eid not in events else f"event {eid!r} belongs to {events[eid][0].get('node_id')!r}"
            errors.append(issue(path + ".event_ids", message, "event_membership"))
        for eid in sorted(owned - listed):
            errors.append(issue(path + ".event_ids", f"owned event {eid!r} is missing from node event_ids", "event_membership"))
        for stage, entry in node["lifecycle"].items():
            for eid in entry["event_ids"]:
                lp = path + ".lifecycle." + stage
                if eid not in owned:
                    errors.append(issue(lp + ".event_ids", f"event {eid!r} is not owned by this node", "event_membership"))
                elif events[eid][0].get("event_type") != stage:
                    errors.append(issue(lp + ".event_ids", f"event {eid!r} has type {events[eid][0].get('event_type')!r}, expected {stage!r}", "lifecycle_type"))
        anchor = node["graph_anchor"]
        if anchor["status"] == "selected":
            eid = anchor["event_id"]
            if eid not in owned:
                errors.append(issue(path + ".graph_anchor.event_id", f"anchor {eid!r} is not owned by this node", "anchor_membership"))
            elif eid in valid_ids["events"]:
                event = events[eid][0]
                allowed = SCIENTIFIC if anchor["policy"] == "scientific_event" else {anchor["policy"]}
                if event["event_type"] not in allowed:
                    errors.append(issue(path + ".graph_anchor.event_id", f"{event['event_type']!r} is not eligible for {anchor['policy']!r}; do not substitute invention/adoption for commercial availability", "anchor_type"))
            if anchor["policy"] == "practical_deployment":
                applicability = node["commercial_applicability"]
                if applicability["status"] not in ("nonmarket", "not_applicable") or not applicability["evidence"]:
                    errors.append(issue(path + ".graph_anchor", "practical-deployment anchor requires nonmarket/not_applicable status and explicit decision evidence", "anchor_applicability"))
            elif anchor["policy"] == "first_commercial_availability" and node["commercial_applicability"]["status"] != "applicable":
                errors.append(issue(path + ".graph_anchor", "selected commercial availability requires commercial applicability status applicable", "anchor_applicability"))
    for rid in sorted(valid_ids["relationships"]):
        edge, path = indexes["relationships"][rid]
        dated = []
        for side in ("from", "to"):
            endpoint = edge[side]
            nid, eid = endpoint["node_id"], endpoint.get("event_id")
            if nid not in nodes:
                errors.append(issue(path + "." + side + ".node_id", f"unknown node {nid!r}", "dangling_node"))
            if eid is not None:
                if eid not in events:
                    errors.append(issue(path + "." + side + ".event_id", f"unknown event {eid!r}", "dangling_event"))
                elif events[eid][0].get("node_id") != nid:
                    errors.append(issue(path + "." + side + ".event_id", f"event {eid!r} does not belong to {nid!r}", "event_membership"))
                elif eid in valid_ids["events"]:
                    dated.append(events[eid][0]["date"])
        if len(dated) == 2 and "earliest" in dated[0] and "latest" in dated[1] and _time(dated[0]["earliest"]) > _time(dated[1]["latest"], True):
            concerns.append(issue(path, "source event is later than receiving event; review temporal_note and relation direction (commercial display anchors were not compared)", "event_chronology"))
        if edge["relation"] in {"supersedes", "revival-of", "abandonment-of"}:
            inspected = any(sources.get(e["source_id"], ({}, ""))[0].get("inspected_passages") for e in edge["evidence"])
            if not inspected:
                errors.append(issue(path + ".evidence", "new relation requires a source with inspected passages", "uninspected_relation"))
    good_nodes = [nodes[nid][0] for nid in sorted(valid_ids["nodes"])]
    reviews = {}
    for kind in ("nodes", "events", "relationships"):
        rows = [r for r, _ in indexes[kind].values() if isinstance(r.get("review"), dict)]
        reviews[kind] = {axis: dict(sorted(Counter(
            r["review"][axis] if isinstance(r["review"].get(axis), str) else "invalid" for r in rows
        ).items())) for axis in ("historical_claim", "lifecycle_classification")}
    result["counts"] = {
        "records": {kind: len(records.get(kind, [])) for kind in KINDS},
        "node_kinds": dict(Counter(n["kind"] for n in good_nodes)),
        "technology_commercial_dates_unresearched": sum(n["kind"] == "technology" and n["lifecycle"]["first_commercial_availability"]["status"] == "not_yet_researched" for n in good_nodes),
        "anchors_unresolved": sum(n["graph_anchor"]["status"] in ("unknown", "not_yet_researched") for n in good_nodes),
        "anchor_status": dict(Counter(n["graph_anchor"]["status"] for n in good_nodes)),
        "lifecycle_status": {stage: dict(Counter(n["lifecycle"][stage]["status"] for n in good_nodes)) for stage in LIFECYCLE},
        "review": reviews,
    }
    result["valid"] = not errors
    return result


def _reject_constant(value):
    raise ValueError(f"non-JSON number {value}")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _read_json(text):
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def verify_local_files(records, root):
    """Check current review paths and source copies without consulting the web."""
    root = Path(root).resolve()
    errors, verified, reviewed, actual_hashes = [], set(), set(), {}

    def contained_file(relative, path):
        rel = Path(relative)
        try:
            target = (root / rel).resolve()
        except (OSError, RuntimeError, ValueError) as e:
            errors.append(issue(path, f"cannot resolve local file: {e}", "local_path"))
            return
        if rel.is_absolute() or not target.is_relative_to(root):
            errors.append(issue(path, "file reference must be repository-relative and stay within the graph repository", "local_path"))
            return
        return target

    for kind in KINDS:
        for i, record in enumerate(records.get(kind, []), 1):
            path = f"{kind}.jsonl:{i}"
            if not isinstance(record, dict):
                continue
            review = record.get("review")
            if isinstance(review, dict) and isinstance(review.get("records"), list):
                for j, relative in enumerate(review["records"]):
                    if not isinstance(relative, str):
                        continue
                    rp = f"{path}.review.records[{j}]"
                    target = contained_file(relative, rp)
                    if target is not None:
                        if target.is_file():
                            reviewed.add(target)
                        else:
                            errors.append(issue(rp, "current review record is missing or is not a file", "review_file"))
            if kind == "sources" and isinstance(record.get("local_copy"), dict):
                copy = record["local_copy"]
                if not isinstance(copy.get("path"), str) or not isinstance(copy.get("sha256"), str) or not re.fullmatch(r"[a-fA-F0-9]{64}", copy["sha256"]):
                    continue  # Shape diagnostics are emitted by the schema validator.
                cp = path + ".local_copy.path"
                target = contained_file(copy["path"], cp)
                if target is None:
                    continue
                if target not in actual_hashes:
                    try:
                        actual_hashes[target] = hashlib.sha256(target.read_bytes()).hexdigest()
                    except OSError as e:
                        actual_hashes[target] = None
                        errors.append(issue(cp, f"cannot read local source copy: {e}", "local_copy_hash"))
                actual = actual_hashes[target]
                if actual is not None:
                    if actual != copy["sha256"].lower():
                        errors.append(issue(cp, f"hash mismatch for {copy['path']}: actual {actual}", "local_copy_hash"))
                    else:
                        verified.add(target)
    return errors, len(verified), len(reviewed)


def validate_repository(root=DEFAULT_ROOT, optional_jsonschema=True):
    root = Path(root).resolve()
    records, parsing = {}, []
    for kind in KINDS:
        records[kind] = []
        path = root / "data" / (kind + ".jsonl")
        try:
            lines = path.read_text().splitlines()
        except (OSError, UnicodeError) as e:
            parsing.append(issue(str(path), f"cannot read canonical data: {e}", "read"))
            continue
        for number, line in enumerate(lines, 1):
            if not line.strip():
                parsing.append(issue(f"{kind}.jsonl:{number}", "blank lines are not JSONL records", "json"))
                records[kind].append({})  # Preserve subsequent source line numbers.
                continue
            try:
                records[kind].append(_read_json(line))
            except ValueError as e:
                parsing.append(issue(f"{kind}.jsonl:{number}", f"invalid JSON: {e}", "json"))
                records[kind].append({})
    result = validate_records(records, root / "schema.json", optional_jsonschema)
    result["errors"][:0] = parsing
    file_errors, verified, reviewed = verify_local_files(records, root)
    result["errors"].extend(file_errors)
    result["counts"]["source_copies_verified"] = verified
    result["counts"]["review_files_verified"] = reviewed
    result["valid"] = not result["errors"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="graph repository directory")
    parser.add_argument("--json", action="store_true", help="machine-readable result")
    parser.add_argument("--stdlib-only", action="store_true", help="disable optional installed-jsonschema cross-check")
    parser.add_argument("--strict-concerns", action="store_true", help="also return failure for review concerns")
    args = parser.parse_args(argv)
    try:
        result = validate_repository(args.root, not args.stdlib_only)
    except (OSError, ValueError, KeyError) as e:
        result = {"valid": False, "errors": [issue("validator", str(e), "configuration")], "concerns": [], "counts": {}}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"{'VALID' if result['valid'] else 'INVALID'}: {len(result['errors'])} error(s), {len(result['concerns'])} review concern(s)")
        print(json.dumps(result["counts"], indent=2, ensure_ascii=False))
        for severity, entries in (("ERROR", result["errors"]), ("REVIEW", result["concerns"])):
            for entry in entries:
                print(f"{severity} {entry['path']} [{entry['code']}]: {entry['message']}")
    return 1 if result["errors"] or (args.strict_concerns and result["concerns"]) else 0


if __name__ == "__main__":
    sys.exit(main())
