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
ENTRY_EVENT_TYPES = {
    "first_commercial_availability": {"first_commercial_availability"},
    "commercial_availability": {"commercial_offer", "commercial_availability"},
    "practical_use": {"practical_use", "practical_deployment"},
    "adoption": {"adoption"},
    "public_availability": {"public_availability"},
    "recognition": {"recognition", "acceptance"},
    "public_awareness": {"publication", "presentation", "public_disclosure"},
}
REVIEW_AXES = ("historical_claim", "lifecycle_classification")
REVIEW_FIELDS = {"id", "type", "historical_claim", "lifecycle_classification", "proposition_sha256"}
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
    for name in ("earliest", "latest"):
        if name not in d:
            continue
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
    if "earliest" in d and "latest" in d:
        if _time(d["earliest"]) > _time(d["latest"], True):
            errors.append(issue(path + ".date", "earliest bound follows latest bound", "date_order"))
        if d["status"] == "known" and d["earliest"] != d["latest"]:
            concerns.append(issue(path + ".date", "known has unequal bounds; consider bounded or explain the precision convention", "known_range"))


def _definitely_after(source_date, receiving_date):
    """Only supplied decisive bounds establish reversed event chronology."""
    # Approximation has no quantified tolerance, so its nominal year cannot
    # establish definite ordering against another event's limit.
    return (source_date.get("status") != "approximate"
            and receiving_date.get("status") != "approximate"
            and "earliest" in source_date and "latest" in receiving_date
            and _time(source_date["earliest"]) > _time(receiving_date["latest"], True))


def validate_records(records, schema_path=None, optional_jsonschema=True):
    """Return errors, review concerns, coverage counts for in-memory records.

    Does not mutate inputs or infer lifecycle acceptance from historical review.
    Repository file and review-ledger checks are performed by validate_repository.
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
        record_anchor = node["graph_anchor"]
        if record_anchor["status"] == "selected":
            eid = record_anchor["event_id"]
            if eid not in owned:
                errors.append(issue(path + ".graph_anchor.event_id", "earliest record must belong to the node", "anchor_membership"))
            elif eid in valid_ids["events"]:
                chosen = events[eid][0]
                if chosen["date"]["status"] not in {"known", "approximate", "bounded"}:
                    errors.append(issue(path + ".graph_anchor", "earliest record needs supplied date bounds", "anchor_date"))
                for witness in node.get("witnesses", []):
                    if witness["event_id"] == eid:
                        errors.append(issue(path + ".graph_anchor", "surviving-copy witness is not automatically an earliest-record anchor", "witness_anchor"))
        for witness in node.get("witnesses", []):
            if witness["event_id"] not in owned:
                errors.append(issue(path + ".witnesses", "witness event must belong to node", "event_membership"))
        anchor = node["community_entry"]
        if anchor["status"] == "selected":
            eid = anchor["event_id"]
            if eid not in owned:
                errors.append(issue(path + ".graph_anchor.event_id", f"anchor {eid!r} is not owned by this node", "anchor_membership"))
            elif eid in valid_ids["events"]:
                event = events[eid][0]
                allowed = ENTRY_EVENT_TYPES[anchor["entry_basis"]]
                if event["event_type"] not in allowed:
                    errors.append(issue(path + ".graph_anchor.event_id", f"{event['event_type']!r} does not establish {anchor['entry_basis']!r} in a community; invention/discovery/demonstration are not entry anchors", "anchor_type"))
                stage = event["event_type"]
                if stage in node["lifecycle"]:
                    entry = node["lifecycle"][stage]
                    if entry["status"] != "documented" or eid not in entry["event_ids"]:
                        errors.append(issue(path + ".graph_anchor.event_id", f"selected anchor must occur in the documented {stage!r} lifecycle entry", "anchor_lifecycle"))
                if event["date"]["status"] not in {"known", "approximate", "bounded"}:
                    errors.append(issue(path + ".graph_anchor.event_id", "selected anchor requires a known, approximate or bounded usable event date", "anchor_date"))
                required_bound = {"known_by": "latest", "known_from": "earliest"}.get(anchor["date_interpretation"])
                if required_bound and required_bound not in event["date"]:
                    errors.append(issue(path + ".graph_anchor.date_interpretation", f"{anchor['date_interpretation']} needs the selected event's supplied {required_bound} limit", "anchor_date"))
            basis, strength = anchor["entry_basis"], anchor["evidence_strength"]
            if (basis == "public_awareness") != (strength == "awareness_proxy"):
                errors.append(issue(path + ".graph_anchor", "public awareness requires an explicitly justified awareness_proxy; the proxy must never be called adoption/use/recognition", "anchor_strength"))
            if strength == "scoped_inference" and basis not in {"practical_use", "public_availability"}:
                errors.append(issue(path + ".graph_anchor", "scoped_inference is limited to contextual practical use or public availability", "anchor_strength"))
            if basis in {"first_commercial_availability", "commercial_availability"} and node["commercial_applicability"]["status"] != "applicable":
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
        if edge["relation"] not in {"same-principle", "same-family", "companion-of"} and len(dated) == 2 and _definitely_after(dated[0], dated[1]):
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
        "community_entry_basis": dict(Counter(n["community_entry"]["entry_basis"] for n in good_nodes if n["community_entry"]["status"] == "selected")),
        "entry_evidence_strength": dict(Counter(n["community_entry"]["evidence_strength"] for n in good_nodes if n["community_entry"]["status"] == "selected")),
        "entry_date_interpretation": dict(Counter(n["community_entry"]["date_interpretation"] for n in good_nodes if n["community_entry"]["status"] == "selected")),
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


def proposition_sha256(record):
    """Hash the complete current proposition, excluding only top-level review."""
    proposition = {key: value for key, value in record.items() if key != "review"}
    encoded = json.dumps(proposition, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _review_ledger(target, root, errors):
    """Index normalized decisions; heterogeneous auxiliary reviews stay auxiliary."""
    strict = target == root / "reviews/current-evidence.json"
    path = str(target.relative_to(root))
    try:
        document = _read_json(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        if strict:
            errors.append(issue(path, f"cannot read current review ledger: {e}", "review_ledger"))
        return {} if strict else None
    rows = document.get("records") if isinstance(document, dict) else None
    normalized = strict or (isinstance(rows, list) and any(
        isinstance(row, dict) and REVIEW_FIELDS <= row.keys() for row in rows))
    if not normalized:
        return None
    if not isinstance(rows, list):
        errors.append(issue(path, "normalized current review ledger requires a records array", "review_ledger"))
        return {}
    entries, duplicate = {}, set()
    for i, row in enumerate(rows):
        rp = f"{path}.records[{i}]"
        if not isinstance(row, dict) or not REVIEW_FIELDS <= row.keys():
            if strict:
                errors.append(issue(rp, "normalized review entry requires id, type, both review axes and proposition_sha256", "review_ledger"))
            continue
        if (not isinstance(row["id"], str) or not row["id"]
                or row["type"] not in ("node", "event", "relationship")
                or row["historical_claim"] not in ("accepted", "candidate", "withheld")
                or row["lifecycle_classification"] not in ("accepted", "needs_review", "withheld")
                or not isinstance(row["proposition_sha256"], str)
                or not re.fullmatch(r"[a-fA-F0-9]{64}", row["proposition_sha256"])):
            errors.append(issue(rp, "invalid normalized review entry fields", "review_ledger"))
            continue
        key = (row["type"], row["id"])
        if key in entries:
            errors.append(issue(rp, f"duplicate normalized review decision for {key!r}", "review_ledger"))
            duplicate.add(key)
        else:
            entries[key] = row
    return {key: row for key, row in entries.items() if key not in duplicate}


def verify_local_files(records, root, defer_binary_copies=False):
    """Check review decisions, proposition hashes and local source copies."""
    root = Path(root).resolve()
    errors, verified, reviewed, actual_hashes, ledgers = [], set(), set(), {}, {}
    deferred = set()
    current_reviews = 0

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
                matched = False
                try:
                    expected = proposition_sha256(record)
                except (TypeError, ValueError) as e:
                    expected = None
                    errors.append(issue(path, f"cannot hash current proposition: {e}", "review_proposition"))
                for j, relative in enumerate(review["records"]):
                    if not isinstance(relative, str):
                        continue
                    rp = f"{path}.review.records[{j}]"
                    target = contained_file(relative, rp)
                    if target is not None:
                        if target.is_file():
                            reviewed.add(target)
                            if target not in ledgers:
                                ledgers[target] = _review_ledger(target, root, errors)
                            ledger = ledgers[target]
                            if ledger is None:
                                continue
                            if not isinstance(record.get("id"), str):
                                continue
                            decision = ledger.get((KINDS[kind], record.get("id")))
                            if decision is None:
                                errors.append(issue(rp, f"normalized ledger has no decision for {KINDS[kind]} {record.get('id')!r}", "review_membership"))
                                continue
                            consistent = True
                            for axis in REVIEW_AXES:
                                if decision[axis] != review.get(axis):
                                    errors.append(issue(rp, f"{axis} differs from normalized ledger decision", "review_status"))
                                    consistent = False
                            if expected is None or decision["proposition_sha256"].lower() != expected:
                                errors.append(issue(rp, "normalized review proposition hash does not match the current record", "review_proposition"))
                                consistent = False
                            matched = matched or consistent
                        else:
                            errors.append(issue(rp, "current review record is missing or is not a file", "review_file"))
                if kind != "sources" and isinstance(record.get("id"), str):
                    if matched:
                        current_reviews += 1
                    else:
                        errors.append(issue(path + ".review.records", "at least one matching normalized current review decision is required", "review_coverage"))
            if kind == "sources" and isinstance(record.get("local_copy"), dict):
                copy = record["local_copy"]
                if not isinstance(copy.get("path"), str) or not isinstance(copy.get("sha256"), str) or not re.fullmatch(r"[a-fA-F0-9]{64}", copy["sha256"]):
                    continue  # Shape diagnostics are emitted by the schema validator.
                cp = path + ".local_copy.path"
                target = contained_file(copy["path"], cp)
                if target is None:
                    continue
                if defer_binary_copies and target.suffix.lower() in {".pdf", ".png", ".jpg"}:
                    deferred.add(target)
                    continue
                if target not in actual_hashes:
                    try:
                        copied = target.read_bytes()
                        if copied:
                            actual_hashes[target] = hashlib.sha256(copied).hexdigest()
                        else:
                            actual_hashes[target] = None
                            errors.append(issue(cp, "declared local source copy is empty; a matching empty-file hash does not retain a source", "local_copy_empty"))
                    except OSError as e:
                        actual_hashes[target] = None
                        errors.append(issue(cp, f"cannot read local source copy: {e}", "local_copy_hash"))
                actual = actual_hashes[target]
                if actual is not None:
                    if actual != copy["sha256"].lower():
                        errors.append(issue(cp, f"hash mismatch for {copy['path']}: actual {actual}", "local_copy_hash"))
                    else:
                        verified.add(target)
    return errors, len(verified), len(reviewed), current_reviews, len(deferred)


def validate_repository(root=DEFAULT_ROOT, optional_jsonschema=True, defer_binary_copies=False):
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
    file_errors, verified, reviewed, current_reviews, deferred = verify_local_files(records, root, defer_binary_copies)
    result["errors"].extend(file_errors)
    result["counts"]["source_copies_verified"] = verified
    result["counts"]["binary_source_copies_deferred"] = deferred
    result["counts"]["review_files_verified"] = reviewed
    result["counts"]["current_review_records_verified"] = current_reviews
    result["valid"] = not result["errors"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="graph repository directory")
    parser.add_argument("--json", action="store_true", help="machine-readable result")
    parser.add_argument("--stdlib-only", action="store_true", help="disable optional installed-jsonschema cross-check")
    parser.add_argument("--strict-concerns", action="store_true", help="also return failure for review concerns")
    parser.add_argument("--metadata-only", action="store_true", help="validate graph, reviews and text captures while explicitly deferring local binary hashes")
    args = parser.parse_args(argv)
    try:
        result = validate_repository(args.root, not args.stdlib_only, args.metadata_only)
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
