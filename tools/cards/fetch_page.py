#!/usr/bin/env python3
"""Shared, content-addressed source text cache. Failed retrievals are deferred, not evidence.

``page_text(url)`` preserves the original string API; ``source_snapshot`` exposes
provenance and acquisition status. Cache hits never require a network request.
"""
import contextlib
import datetime
import fcntl
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

PAGES = Path(__file__).resolve().parents[2] / '.cache' / 'pages'
NEGATIVE_TTL = 900
MAX_ATTEMPTS = 2


def sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def path_for(url):
    return PAGES / (sha256(url) + '.txt')


def _meta_path(url):
    return path_for(url).with_suffix('.json')


def _read(path):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextlib.contextmanager
def _lock(url):
    PAGES.mkdir(parents=True, exist_ok=True)
    # flock is shared by threads and processes using separate open descriptions.
    with path_for(url).with_suffix('.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def fetch(url, plain=False):
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; ResearchSourceCache/1.0)',
               'Accept': 'text/plain' if plain else 'text/html,application/pdf,*/*',
               'Accept-Language': 'en'}
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return response.read(40_000_000), response.headers.get('Content-Type', '')


def norm(text):
    text = unicodedata.normalize('NFKD', html.unescape(text))
    text = ''.join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def text_status(text):
    low = text.lower()
    if any(marker in low for marker in (
        'search budget exhausted', 'search-budget-exhausted', 'search limit reached',
        'rate limit exceeded', 'quota exceeded', 'credits exhausted',
        'insufficient credits', 'usage limit exceeded', 'search is unavailable')):
        return 'search-budget-exhausted'
    if any(marker in low for marker in (
        'verify you are human', 'verify that you are human', 'checking your browser', 'just a moment...',
        'please enable javascript', 'checking if the site connection is secure',
        'access to this page has been denied', 'challenge-platform',
        'enable javascript and cookies to continue', 'captcha', 'access denied',
        'cf-chl-', 'robot check', 'security verification', 'unusual traffic')):
        return 'blocked'
    if len(norm(text)) < 80 or len(norm(text).split()) < 12:
        return 'extraction-failed'
    return 'fetched'


def _extract(data, ctype):
    if data[:5] == b'%PDF-' or 'pdf' in ctype:
        with tempfile.NamedTemporaryFile(suffix='.pdf') as stream:
            stream.write(data)
            stream.flush()
            result = subprocess.run(['pdftotext', '-q', stream.name, '-'],
                                    capture_output=True, timeout=60, check=False)
            return result.stdout.decode('utf-8', 'ignore') if result.returncode == 0 else ''
    raw = data.decode('utf-8', 'ignore')
    raw = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', raw)
    raw = re.sub(r'(?i)<(br|/p|/div|/li|/h[1-6]|/tr)[^>]*>', '\n', raw)
    text = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', raw))
    return re.sub(r'\n\s*\n+', '\n', re.sub(r'[ \t\r\f\v]+', ' ', text)).strip()


def _service_path(url):
    return PAGES / ('service-' + sha256(urlsplit(url).netloc) + '.json')


def source_snapshot(url):
    """Return validated saved text and metadata, without fetching or trusting legacy collisions."""
    if not isinstance(url, str) or not url:
        return {'url': url, 'status': 'missing', 'text': ''}
    meta = _read(_meta_path(url))
    if meta.get('url') != url or meta.get('url_sha256') != sha256(url):
        return {'url': url, 'status': 'missing', 'text': ''}
    if meta.get('status') == 'fetched':
        try:
            text = path_for(url).read_text(encoding='utf-8')
        except OSError:
            text = ''
        if sha256(text) != meta.get('content_sha256') or text_status(text) != 'fetched':
            return {'url': url, 'status': 'extraction-failed', 'text': ''}
        return dict(meta, text=text)
    return dict(meta, text='')


def import_saved(url, path, expected_sha256, provenance):
    """Explicitly import a frozen UTF-8 source with verified bytes and provenance.

    No URL identity is inferred from a legacy filename. ``provenance`` is a
    nonempty description or mapping supplied by the caller that binds this
    saved material to ``url``. Original access time is unknown unless supplied
    in provenance.accessed_at; import time is recorded separately.
    """
    if not isinstance(url, str) or urlsplit(url).scheme not in ('http', 'https') or not urlsplit(url).netloc:
        raise ValueError('saved source needs a public HTTP(S) URL')
    if not provenance or not isinstance(provenance, (str, dict)):
        raise ValueError('explicit saved-source provenance required')
    if not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ValueError('expected SHA-256 required')
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('saved source bytes do not match expected SHA-256')
    text = raw.decode('utf-8')
    if text_status(text) != 'fetched':
        raise ValueError('saved material is empty, blocked, or unavailable')
    accessed = provenance.get('accessed_at') if isinstance(provenance, dict) else None
    if accessed is not None:
        datetime.datetime.fromisoformat(accessed.replace('Z', '+00:00'))
    # Validate JSON before writing the text or metadata.
    json.dumps(provenance)
    now = time.time()
    with _lock(url):
        _save(url, text, 'fetched', now)
        meta = _read(_meta_path(url))
        meta.update({'acquired_via': 'saved-import', 'imported_at': meta['accessed_at'],
                     'imported_unix': now, 'accessed_at': accessed, 'accessed_unix': None,
                     'provenance': provenance, 'import_sha256': expected_sha256})
        _atomic(_meta_path(url), json.dumps(meta, indent=2))
    return source_snapshot(url)


def page_text(url, refresh=False):
    with _lock(url):
        saved = source_snapshot(url)
        if saved['status'] == 'fetched' and not refresh:
            return saved['text']
        now = time.time()
        if saved.get('retry_after', 0) > now:
            return ''
        service = _read(_service_path(url))
        if service.get('retry_after', 0) > now:
            _save(url, '', 'search-budget-exhausted', now, service['retry_after'])
            return ''
        status = 'extraction-failed'
        for attempt in range(MAX_ATTEMPTS):
            try:
                data, ctype = fetch(url)
                text = _extract(data, ctype) if data else ''
                status = text_status(text)
                if status == 'fetched':
                    _save(url, text, status, now)
                    return text
                # Bot checks, exhaustion and empty extraction do not benefit from immediate retry.
                break
            except HTTPError as error:
                status = ('search-budget-exhausted' if error.code == 429 else
                          'blocked' if error.code in (401, 403) else 'extraction-failed')
                if error.code < 500:
                    break
            except (OSError, ValueError, subprocess.SubprocessError):
                status = 'extraction-failed'
        retry_after = now + NEGATIVE_TTL
        _save(url, '', status, now, retry_after)
        if status == 'search-budget-exhausted':
            _atomic(_service_path(url), json.dumps({'status': status, 'retry_after': retry_after}))
        return ''


def _save(url, text, status, fetched_at, retry_after=None):
    meta = {'acquired_via': 'network', 'url': url, 'url_sha256': sha256(url), 'status': status,
            'accessed_at': datetime.datetime.fromtimestamp(fetched_at, datetime.timezone.utc).isoformat(),
            'accessed_unix': fetched_at, 'content_sha256': sha256(text) if text else None}
    if retry_after is not None:
        meta['retry_after'] = retry_after
    if text:
        _atomic(path_for(url), text)
        _atomic(PAGES / 'content' / (sha256(text) + '.txt'), text)
    _atomic(_meta_path(url), json.dumps(meta, indent=2))


if __name__ == '__main__':
    url = sys.argv[1]
    text = page_text(url)
    print(path_for(url), f'({len(text)} characters)' if text else source_snapshot(url)['status'])
    if '--show' in sys.argv:
        start = int(sys.argv[sys.argv.index('--show') + 1])
        print(text[start:start + 8000])
    if '--find' in sys.argv:
        needle = sys.argv[sys.argv.index('--find') + 1].lower()
        low = text.lower()
        i = low.find(needle)
        for _ in range(8):
            if i < 0:
                break
            print(f'--- at {i} ---\n{text[max(0, i - 300):i + 300]}')
            i = low.find(needle, i + 1)
