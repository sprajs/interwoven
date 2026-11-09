"""Integrity checks for opt-in downloads into the local evidence cache."""
import contextlib
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest


SPEC = importlib.util.spec_from_file_location("evidence_cache", Path(__file__).resolve().parents[1] / "tools/evidence_cache.py")
cache = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cache)
GOOD = b"%PDF-1.4\nA synthetic source capture.\n"


class CacheTests(unittest.TestCase):
    @contextlib.contextmanager
    def source(self, body):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/source.pdf", requests
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def entry(self, root, name, url):
        entry = {"schema_version": 1, "path": f"evidence/{name}.pdf", "sha256": hashlib.sha256(GOOD).hexdigest(),
                 "bytes": len(GOOD), "source_ids": [name], "retrieval": {"kind": "download", "urls": [url]}}
        descriptor = root / (entry["path"] + ".cache.json")
        descriptor.parent.mkdir(exist_ok=True)
        descriptor.write_text(json.dumps(entry))
        return entry

    def test_selected_download_is_verified_cached_and_does_not_fetch_other_items(self):
        with tempfile.TemporaryDirectory() as directory, self.source(GOOD) as (url, requests):
            root = Path(directory)
            self.entry(root, "chosen", url)
            other = self.entry(root, "other", url)
            selected = cache.selected(cache.load_catalog(root), ["chosen"], False)
            self.assertEqual(1, len(selected))
            target = cache.fetch_entry(root, selected[0])
            self.assertEqual(GOOD, target.read_bytes())
            self.assertFalse((root / other["path"]).exists())
            cache.fetch_entry(root, selected[0])
            self.assertEqual(["/source.pdf"], requests)

    def test_changed_remote_bytes_are_never_promoted_or_used_to_overwrite_local_evidence(self):
        changed = GOOD.replace(b"source", b"edited")
        with tempfile.TemporaryDirectory() as directory, self.source(changed) as (url, _):
            root = Path(directory)
            entry = self.entry(root, "chosen", url)
            target = root / entry["path"]
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                cache.fetch_entry(root, entry)
            self.assertFalse(target.exists())
            target.write_bytes(b"Existing local research")
            with self.assertRaisesRegex(ValueError, "Existing file differs"):
                cache.fetch_entry(root, entry)
            self.assertEqual(b"Existing local research", target.read_bytes())
            self.assertEqual([], list(target.parent.glob(".download-*")))


if __name__ == "__main__":
    unittest.main()
