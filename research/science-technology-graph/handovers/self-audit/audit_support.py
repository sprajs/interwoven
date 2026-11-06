"""Read-only audit helpers. Never imports or changes canonical data or prior reviews.

python3 handovers/self-audit/audit_support.py extract
python3 handovers/self-audit/audit_support.py validate

Source text is temporary inspection material, not a replacement for the cited
document. Extraction is not a semantic verdict. Human findings are in JSONL.
"""
from __future__ import annotations

import collections
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CACHE = Path(tempfile.gettempdir()) / "big-idea-self-audit-source-text"


def records(name):
    return [json.loads(line) for line in pinned_text(f"research/science-technology-graph/data/{name}.jsonl").splitlines()]


def pinned_text(path):
    snapshot = json.loads((OUT / "scope.json").read_text())
    return subprocess.check_output(["git", "show", snapshot["audit_base_commit"] + ":" + path], cwd=ROOT, text=True)


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"): self.skip += 1
        if tag in ("p", "div", "br", "section", "h1", "h2", "h3", "tr", "abstract", "title", "article-title"): self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"): self.skip -= 1

    def handle_data(self, data):
        if not self.skip: self.parts.append(data)


def extract():
    CACHE.mkdir(exist_ok=True)
    log = []
    for source in records("sources"):
        copy = source.get("local_copy", {})
        item = {"id": source["id"], "url": source.get("url"), "path": copy.get("path"), "semantic_check": "not established by extraction"}
        if not copy.get("path"):
            item["extraction_status"] = "external_only"
        else:
            path = ROOT / copy["path"]
            raw = path.read_bytes()
            item["sha256"] = hashlib.sha256(raw).hexdigest()
            item["hash_matches"] = item["sha256"] == copy.get("sha256")
            if path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                item["extractor"] = "none; retained image requires visual inspection"
                item["extraction_status"] = "image_or_sparse_text"
                log.append(item)
                continue
            if path.suffix.lower() == ".pdf":
                proc = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True)
                content = proc.stdout.decode("utf-8", errors="replace")
                item["extractor"] = "pdftotext -layout (form-feed page boundaries retained)"
            else:
                content = raw.decode("utf-8", errors="replace")
                if path.suffix.lower() in (".html", ".xml"):
                    parser = Text(); parser.feed(content); content = "".join(parser.parts)
                item["extractor"] = "HTMLParser text" if path.suffix.lower() in (".html", ".xml") else "direct text"
            content = "\n".join(line.strip() for line in content.splitlines() if line.strip()) if path.suffix.lower() != ".pdf" else content
            (CACHE / (source["id"] + ".txt")).write_text(content)
            item["characters"] = len(content)
            item["extraction_status"] = "text_available" if len(content.strip()) > 250 else "image_or_sparse_text"
        log.append(item)
    (OUT / "source-extraction-log.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in log))
    print(json.dumps(dict(collections.Counter(x["extraction_status"] for x in log)), indent=2))
    print(CACHE)


def validate():
    rel = [json.loads(x) for x in (OUT / "connection-verdicts.jsonl").read_text().splitlines()]
    ent = [json.loads(x) for x in (OUT / "entry-verdicts.jsonl").read_text().splitlines()]
    for rows, canonical, required in [(rel, records("relationships"), {"id", "verdict", "severity", "issue", "proposed_change", "basis"}), (ent, records("nodes"), {"id", "kind_verdict", "identity_verdict", "tier_verdict", "proposed_kind", "proposed_tier", "issue", "basis"})]:
        assert len(rows) == len(canonical)
        assert len({x["id"] for x in rows}) == len(rows)
        assert {x["id"] for x in rows} == {x["id"] for x in canonical}
        for x in rows:
            assert required <= x.keys(), x["id"]
            assert x["basis"]["method"] in ("reopened the cited source", "used another source", "from knowledge only"), x["id"]
    assert all(x["verdict"] in ("agree", "change", "reject", "cannot_verify") for x in rel)
    snapshot = json.loads((OUT / "scope.json").read_text())
    for name, expected in snapshot["sha256"].items():
        raw = subprocess.check_output(["git", "show", snapshot["audit_base_commit"] + ":" + name], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == expected, name
    summary = {"connections": dict(collections.Counter(x["verdict"] for x in rel)), "entries": {k: dict(collections.Counter(x[k] for x in ent)) for k in ("kind_verdict", "identity_verdict", "tier_verdict")}}
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    {"extract": extract, "validate": validate}[sys.argv[1]]()
