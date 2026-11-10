"""Re-fetch every cited page and check that each quotation is really on it.

usage: python3 tools/cards/check_quotes.py <cards.json> [...]

The result is added to .cache/quote-checks.json, keyed by address and quotation.
"""
import html, json, re, subprocess, sys, tempfile, unicodedata, concurrent.futures as cf
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).parent
CACHE = HERE.resolve().parents[1] / '.cache' / 'quote-checks.json'
sys.path.insert(0, str(HERE))
from fetch_page import page_text, norm

def check(url, quote):
    text = norm(page_text(url))
    q = norm(quote)
    if not text:
        return 'unreachable'
    if not q:
        return 'no_quote'
    if q in text:
        return 'exact'
    words = q.split()
    # the longest run of the quotation's words found on the page, as a share of the quotation
    best = 0
    i = 0
    while i < len(words):
        j = i + 4
        if ' '.join(words[i:j]) in text:
            while j < len(words) and ' '.join(words[i:j + 1]) in text:
                j += 1
            best = max(best, j - i)
            i = j
        else:
            i += 1
    share = best / max(1, len(words))
    return 'near' if share >= 0.6 else 'absent'

def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    jobs = []
    for path in sys.argv[1:]:
        for card in json.load(open(path)).get('cards', []):
            srcs = card.get('sources') or []
            for item in (card.get('events') or []) + (card.get('links') or []):
                i = item.get('source')
                if not isinstance(i, int) or i >= len(srcs) or not item.get('quote'):
                    continue
                key = srcs[i]['url'] + ' || ' + item['quote']
                if key not in cache:
                    jobs.append((key, srcs[i]['url'], item['quote']))
    jobs = list({k: (k, u, q) for k, u, q in jobs}.values())
    with cf.ThreadPoolExecutor(8) as pool:
        for key, result in zip([j[0] for j in jobs], pool.map(lambda j: check(j[1], j[2]), jobs)):
            cache[key] = result
    CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
    import collections
    print(collections.Counter(cache.values()))

if __name__ == '__main__':
    main()
