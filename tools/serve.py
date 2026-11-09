#!/usr/bin/env python3
"""Serve a built app with the same compression and caching used by performance checks.

    python3 tools/serve.py --directory app/dist --port 4173
    python3 tools/serve.py --directory app/dist --prepare

Deploy static files elsewhere with the equivalent headers documented in docs/performance.md.
"""
from __future__ import annotations

import argparse
import functools
import gzip
import hashlib
import mimetypes
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from publish import atomic_write

IMMUTABLE = re.compile(r'(?:^|/)(?:data/(?:core|details|population)/[a-f0-9]{24}\.json|assets/[^/]+-[A-Za-z0-9_-]{8,}\.[^/]+)$')


def prepare(directory: Path) -> None:
    for path in directory.rglob('*'):
        if path.suffix in ('.html', '.json', '.js', '.css', '.svg'):
            atomic_write(Path(str(path) + '.gz'), gzip.compress(path.read_bytes(), compresslevel=9, mtime=0))


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError):
            pass  # Normal cancellation when a browser closes a tab or navigates away.

    def send_head(self):
        urlpath = unquote(urlsplit(self.path).path)
        path = Path(self.translate_path(urlpath))
        root = Path(self.directory).resolve()
        if not path.resolve().is_relative_to(root):
            self.send_error(403)
            return None
        if path.is_dir():
            path /= 'index.html'
        if not path.is_file():
            # A missing data asset must be a 404, never SPA HTML with a 200 response.
            self.send_error(404)
            return None
        compressed = Path(str(path) + '.gz')
        accepts_gzip = any(part.strip().split(';')[0] == 'gzip' and not re.search(r';\s*q=0(?:\.0*)?$', part.strip()) for part in self.headers.get('Accept-Encoding', '').split(','))
        use_gzip = accepts_gzip and compressed.is_file()
        chosen = compressed if use_gzip else path
        etag = '"' + hashlib.sha256(chosen.read_bytes()).hexdigest() + '"'
        cache = 'public, max-age=31536000, immutable' if IMMUTABLE.search(urlpath) else 'no-cache'
        if self.headers.get('If-None-Match') == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_header('Cache-Control', cache)
            self.send_header('Vary', 'Accept-Encoding')
            self.end_headers()
            return None
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(path)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(chosen.stat().st_size))
        self.send_header('ETag', etag)
        self.send_header('Cache-Control', cache)
        self.send_header('Vary', 'Accept-Encoding')
        if use_gzip:
            self.send_header('Content-Encoding', 'gzip')
        self.end_headers()
        return chosen.open('rb')

    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent.parent / 'app/dist')
    parser.add_argument('--port', type=int, default=4173)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    prepare(args.directory)
    if args.prepare:
        return
    handler = functools.partial(Handler, directory=str(args.directory.resolve()))
    with ThreadingHTTPServer((args.host, args.port), handler) as server:
        print(f'Serving {args.directory} at http://{args.host}:{server.server_port}', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
