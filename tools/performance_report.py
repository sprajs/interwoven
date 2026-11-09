#!/usr/bin/env python3
"""Summarise measured browser/research samples and draw a reproducible standalone SVG."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics
from xml.sax.saxutils import escape


def percentile(values, p):
    values=sorted(values); pos=(len(values)-1)*p
    lo,hi=math.floor(pos),math.ceil(pos)
    return values[lo]+(values[hi]-values[lo])*(pos-lo)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    browser=json.loads((args.directory/'browser.json').read_text())
    research=json.loads((args.directory/'research.json').read_text())
    groups=defaultdict(list)
    for row in browser['measurements']:
        groups[(row['profile'],row['cache'],row['variant'])].append(row)
    summary=[]
    for (profile,cache,variant),rows in groups.items():
        ready=[r['ready_ms'] for r in rows]
        summary.append({'profile':profile,'cache':cache,'variant':variant,'n':len(rows),'median_ms':statistics.median(ready),'p95_ms':percentile(ready,.95),'min_ms':min(ready),'max_ms':max(ready),'median_transfer_bytes':statistics.median(sum(x['bytes'] for x in r['resources'])+r['document_bytes'] for r in rows)})
    (args.directory/'summary.json').write_text(json.dumps({'browser':summary,'detail':browser['detail'],'disk_restart_ms':browser['disk_restart']['ready_ms'],'invalidation_ms':browser['invalidation']['ready_ms'],'research':research['timings'],'quantile_method':'linear interpolation, small lab samples'},indent=2)+'\n')
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="650" viewBox="0 0 1100 650" role="img" aria-label="Measured first data draw, median milliseconds, baseline and updated app with a deliberately incomplete canvas control.">','<rect width="1100" height="650" fill="#fff"/>','<g font-family="sans-serif" fill="#17222c">','<text x="24" y="35" font-size="22">Time to first data draw · median milliseconds</text>',f'<text x="24" y="60" font-size="14">{browser["metadata"]["runs"]} trials per condition · Chrome · same {browser["metadata"].get("discoveries", "measured")} records · lower is better</text>']
    colors={'baseline':'#9aa4ad','candidate':'#2b64a0','control':'#9c792c'}
    labels={'baseline':'Previous app','candidate':'Updated app','control':'Minimal canvas control'}
    panels=[('local','cold'),('local','warm'),('10mbps-40ms-4x','cold'),('10mbps-40ms-4x','warm')]
    for panel,(profile,cache) in enumerate(panels):
        x=24+(panel%2)*540;y=105+(panel//2)*245
        rows=[next(r for r in summary if (r['profile'],r['cache'],r['variant'])==(profile,cache,v)) for v in ('baseline','candidate','control')]
        ceiling=max(r['median_ms'] for r in rows)*1.18
        title=('Local' if profile=='local' else '10 Mbps · 40 ms · CPU 4×')+' / '+cache
        parts.append(f'<text x="{x}" y="{y}" font-size="17">{escape(title)}</text>')
        for i,row in enumerate(rows):
            yy=y+35+i*48; width=280*row['median_ms']/ceiling
            parts.append(f'<text x="{x}" y="{yy+15}" font-size="13">{labels[row["variant"]]}</text><rect x="{x+170}" y="{yy}" width="{width:.2f}" height="22" fill="{colors[row["variant"]]}"/><text x="{x+177+width:.2f}" y="{yy+16}" font-size="13">{row["median_ms"]:.1f}</text>')
        for fraction in (0,.5,1):
            xx=x+170+280*fraction
            parts.append(f'<text x="{xx:.2f}" y="{y+198}" text-anchor="middle" font-size="12">{ceiling*fraction:.0f}</text>')
        parts.append(f'<text x="{x+310}" y="{y+218}" text-anchor="middle" font-size="12">Milliseconds (ms)</text>')
    parts.extend(['<text x="24" y="615" font-size="13">Control omits labels, layout, filtering and other app features; it is an optimistic reference, not an equivalent app.</text>','<text x="24" y="637" font-size="13">Cold browser cache; warm OS cache. This canvas metric is not LCP or a field measurement.</text>','</g></svg>'])
    (args.directory/'comparison.svg').write_text(''.join(parts)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
