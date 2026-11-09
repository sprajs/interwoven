#!/usr/bin/env python3
"""Measure research queries, refresh checks and process overhead against real data."""
from __future__ import annotations

import argparse
import hashlib
from contextlib import closing
import json
import platform
import statistics
from performance_report import percentile
import subprocess
import sys
import time
from pathlib import Path

from dataset import Dataset, ROOT
import research


def measure(fn, runs=101):
    # Warm the code/data explicitly; report this separately from opening the cache or a process.
    for _ in range(5):
        fn()
    samples = []
    for _ in range(runs):
        start = time.perf_counter_ns()
        fn()
        samples.append((time.perf_counter_ns()-start)/1e6)
    ordered = sorted(samples)
    return {'median_ms':statistics.median(samples), 'p95_ms':percentile(ordered,.95), 'min_ms':min(samples), 'runs':runs}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'.cache/performance/research.json')
    args=parser.parse_args()
    start=time.perf_counter()
    version=research.rebuild()
    rebuild_ms=(time.perf_counter()-start)*1000
    data=Dataset.load()
    with closing(research.connect()) as con:
        seed=con.execute('SELECT dst FROM edges WHERE status="established" GROUP BY dst ORDER BY count(*) DESC,dst LIMIT 1').fetchone()[0]
        queries=['steam','printing','electricity','water','Watt','China','instrument','agriculture']
        expected={query:[r['id'] for r in research.search(con,query,1000)] for query in queries}
        # Smoke-check result identities; semantic fixtures and traversal oracles are in unit tests.
        for query, ids in expected.items():
            assert all(key in data.discoveries for key in ids)
        timings={
            'source_load':measure(Dataset.load,31),
            'input_stat_check':measure(research.signature,31),
            'input_content_verification':measure(research.fingerprint,31),
            'sqlite_select1_control':measure(lambda:con.execute('SELECT 1').fetchone()),
            'sqlite_id_lookup':measure(lambda:con.execute('SELECT id,name,path FROM discoveries WHERE id=?',(seed,)).fetchone()),
            'fts_searches':{q:measure(lambda q=q:research.search(con,q)) for q in queries},
            'fts_with_snippets':measure(lambda:research.search(con,'water',snippets=True)),
            'walk_incoming_depth4':measure(lambda:research.walk(con,seed,depth=4)),
            'shared_entities':measure(lambda:research.shared(con,seed)),
        }
        def fresh_connection():
            with closing(research.connect()) as fresh:
                return research.search(fresh,'steam')
        timings['checked_connection_search']=measure(fresh_connection,31)
    timings['browser_build_noop']=measure(lambda:subprocess.run([sys.executable,str(ROOT/'tools/build.py')],check=True,stdout=subprocess.DEVNULL),11)
    timings['python_process_control']=measure(lambda:subprocess.run([sys.executable,'-c','pass'],check=True,stdout=subprocess.DEVNULL),11)
    timings['cli_search']=measure(lambda:subprocess.run([sys.executable,str(ROOT/'tools/research.py'),'search','steam'],check=True,stdout=subprocess.DEVNULL),11)
    # An adjacency map is an optimistic in-memory traversal control with no SQL, paths or names.
    edges={}
    for d,l in data.links():
        if l['status']=='established' and l['type'] in sum([data.vocab['link']['layers'][k] for k in ('dependence','transmission')],[]):
            edges.setdefault(d['id'],[]).append(l['from'])
    def memory_walk():
        seen={seed}; frontier=[seed]
        for _ in range(4):
            following={other for node in frontier for other in edges.get(node,[]) if other not in seen}
            seen.update(following);frontier=following
        return seen
    timings['resident_adjacency_control']=measure(memory_walk)
    result={'metadata':{'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dataset':version,'query_source_sha256':hashlib.sha256(Path(research.__file__).read_bytes()).hexdigest(),'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)),'python':sys.version,'platform':platform.platform(),'sqlite':research.sqlite3.sqlite_version,'seed':seed,'discoveries':len(data.discoveries),'meaning':'Warm OS cache, real data. Controls omit useful work and are optimistic reference points, not equivalent implementations.'},'rebuild_ms':rebuild_ms,'timings':timings}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
