#!/usr/bin/env python3
"""Fetch a web page or PDF and save its plain text, so that quotations can be copied from exactly
what the checker will read.

    python3 fetch_page.py <url>            # prints the path of the saved text file
    python3 fetch_page.py <url> --show 0   # also prints the text from character 0 (8000 characters)
    python3 fetch_page.py <url> --find "some words"   # prints 600 characters around each match
"""
import html, re, subprocess, sys, tempfile, unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

#: Saved pages live outside git, in the repository's local cache.
PAGES = Path(__file__).resolve().parents[2] / '.cache' / 'pages'
PAGES.mkdir(parents=True, exist_ok=True)

def path_for(url):
    return PAGES / (re.sub(r'[^a-zA-Z0-9]+', '_', url)[:150] + '.txt')

def fetch(url, plain=False):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36', 'Accept': 'text/plain' if plain else 'text/html,application/pdf,*/*', 'Accept-Language': 'en'}
        with urlopen(Request(url, headers=headers), timeout=60) as r:
            return r.read(40_000_000), r.headers.get('Content-Type', '')
    except Exception:
        return b'', ''

def page_text(url, refresh=False):
    cached = path_for(url)
    # A page that failed before is tried again; only pages with text are kept.
    if cached.exists() and not refresh and cached.stat().st_size > 0:
        return cached.read_text(errors='ignore')
    data, ctype = fetch(url)
    if not data or (len(data) < 4000 and b'%PDF-' not in data[:5]):
        # Many publishers refuse plain downloads. A reader service that renders the page as text
        # is tried next; it receives only the public address.
        data, ctype = fetch('https://r.jina.ai/' + url, plain=True)
        if data:
            text = data.decode('utf-8', 'ignore')
            cached.write_text(text)
            return text
    if not data:
        return ''
    if data[:5] == b'%PDF-' or 'pdf' in ctype:
        with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
            f.write(data); f.flush()
            try:
                text = subprocess.run(['pdftotext', '-q', f.name, '-'], capture_output=True, timeout=120).stdout.decode('utf-8', 'ignore')
            except Exception:
                text = ''
    else:
        raw = data.decode('utf-8', 'ignore')
        raw = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', raw)
        raw = re.sub(r'(?i)<(br|/p|/div|/li|/h[1-6]|/tr)[^>]*>', '\n', raw)
        text = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', raw))
        text = re.sub(r'[ \t\r\f\v]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n', text)
    cached.write_text(text)
    return text

def norm(text):
    text = unicodedata.normalize('NFKD', html.unescape(text))
    text = ''.join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()

if __name__ == '__main__':
    url = sys.argv[1]
    text = page_text(url)
    print(path_for(url), f'({len(text)} characters)' if text else '(COULD NOT BE FETCHED OR EMPTY: do not cite this page)')
    if '--show' in sys.argv:
        start = int(sys.argv[sys.argv.index('--show') + 1])
        print(text[start:start + 8000])
    if '--find' in sys.argv:
        needle = sys.argv[sys.argv.index('--find') + 1].lower()
        low = text.lower(); i = low.find(needle); n = 0
        while i >= 0 and n < 8:
            print(f'--- at {i} ---'); print(text[max(0, i - 300):i + 300]); n += 1
            i = low.find(needle, i + 1)
        if n == 0: print('(not found)')
