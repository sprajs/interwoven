"""Test helper: publish an edited copy into a disposable built-app directory only."""
import argparse
import json
from pathlib import Path
import re
from build import build
from dataset import Dataset
from publish import atomic_write, encoded, publish
from serve import prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('id')
    args = parser.parse_args()
    directory = args.directory.resolve()
    if directory == Path(__file__).resolve().parent.parent / 'app/dist':
        parser.error('Use a disposable copy, not app/dist.')
    bundle = build(Dataset.load())
    record = next(d for d in bundle['discoveries'] if d['id'] == args.id)
    record['description'] += ' Cache invalidation fixture.'
    record['summary'] = (record.get('summary') or '') + ' Cache invalidation fixture.'
    old = json.loads((directory/'data/manifest.json').read_text())
    new = publish(bundle, directory/'data')
    html = (directory/'index.html').read_text().replace(old['core'],new['core'])
    html = re.sub(r'(<script[^>]*id="dataset-manifest"[^>]*>).*?(</script>)', lambda m: m[1]+encoded(new).decode().strip()+m[2], html, flags=re.S)
    atomic_write(directory/'index.html',html.encode())
    prepare(directory)
    print(json.dumps({'before':old,'after':new}))


if __name__=='__main__':
    main()
