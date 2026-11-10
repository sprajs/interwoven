"""Check whole quotations against source snapshots. This does not establish entailment."""
import collections
import concurrent.futures as cf
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[1] / '.cache' / 'quote-checks.json'
sys.path.insert(0, str(HERE))
from fetch_page import page_text, norm, source_snapshot
from gates import exact_quote, meaningful_quote, valid_source


def check(url, quote):
    text = page_text(url)
    if not text:
        return 'unreachable'
    if not meaningful_quote(quote):
        return 'insufficient_quote'
    if exact_quote(text, quote):
        return 'exact'
    # Keep near as a diagnostic only. No admission gate accepts it.
    words = norm(quote).split()
    normalized = ' ' + norm(text) + ' '
    best = 0
    for start in range(len(words)):
        for end in range(start + best + 1, len(words) + 1):
            if ' ' + ' '.join(words[start:end]) + ' ' in normalized:
                best = max(best, end - start)
            else:
                break
    return 'near' if best / len(words) >= .6 else 'absent'


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    jobs = {}
    for path in sys.argv[1:]:
        for card in json.loads(Path(path).read_text()).get('cards', []):
            sources = card.get('sources') or []
            for item in (card.get('events') or []) + (card.get('links') or []):
                index = item.get('source')
                if not valid_source(index, sources) or not item.get('quote'):
                    continue
                url, quote = sources[index]['url'], item['quote']
                jobs[url + ' || ' + quote] = (url, quote)
    # Reuse saved source pages; never trust an unversioned historical quote verdict.
    with cf.ThreadPoolExecutor(8) as pool:
        for key, result in zip(jobs, pool.map(lambda pair: check(*pair), jobs.values())):
            url, _ = jobs[key]
            cache[key] = {'status': result,
                          'content_sha256': source_snapshot(url).get('content_sha256'),
                          'policy_version': 2}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
    print(collections.Counter(v.get('status') if isinstance(v, dict) else 'legacy-untrusted'
                              for v in cache.values()))


if __name__ == '__main__':
    main()
