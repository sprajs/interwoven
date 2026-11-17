"""Render independently reviewed results using only the Python standard library."""
import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlsplit


def esc(value):
    return html.escape(str(value), quote=True)


def evidence(items, sources):
    rows = []
    for item in items:
        source = sources.get(item.get('source'), {})
        label = esc(source.get('title', item.get('source', 'Source')))
        url = source.get('url', '')
        if urlsplit(url).scheme in {'http', 'https'}:
            label = f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{label}</a>'
        rows.append(f'<li>{label} · {esc(item.get("locator", ""))}<div>{esc(item.get("supports", ""))}</div></li>')
    return '<details><summary>Source passages</summary><ul>' + ''.join(rows) + '</ul></details>' if rows else ''


def render(data, fragment=False):
    edges = data.get('accepted_established_edges', [])
    context = data.get('supported_circumstances', [])
    if any(e.get('status') != 'established' or e.get('review_decision') != 'accept' for e in edges):
        raise ValueError('Only accepted established relationships may enter the graph')
    if any(c.get('review_decision') != 'accept' for c in context):
        raise ValueError('Context must be independently accepted')
    options, panels = [], []
    for n, (key, lane) in enumerate(data['lanes'].items()):
        options.append(f'<option value="lane-{n}">{esc(lane["title"])}</option>')
        rows = [f'<h3>{esc(lane["title"])}</h3>']
        selected = [e for e in edges if e['lane'] == key]
        if not selected:
            rows.append('<div>No new established relationship admitted.</div>')
        for edge in selected:
            relation = {'uses_process': 'process used by', 'uses_instrument': 'instrument used by',
                        'uses_theory': 'theory used by', 'builds_on': 'built on by',
                        'requires': 'required by', 'adapts': 'adapted by',
                        'transmitted_from': 'transmitted to'}.get(edge['type'], edge['type'].replace('_', ' '))
            rows.append('<div class="edge" role="group" aria-label="Established relationship">'
                        f'<div class="node">{esc(edge["from_name"])}</div>'
                        f'<div class="arrow">{esc(relation)}<br><span>→</span></div>'
                        f'<div class="node">{esc(edge["to_name"])}</div></div>'
                        f'<div>{esc(edge["statement"])}</div>')
            if edge.get('scope'):
                rows.append(f'<div><strong>Scope:</strong> {esc(edge["scope"])}</div>')
            if edge.get('caveats'):
                rows.append(f'<div><strong>Uncertainty:</strong> {esc(edge["caveats"])}</div>')
            rows.append(evidence(edge.get('evidence', []), data.get('sources', {})))
        for item in (c for c in context if c['lane'] == key):
            rows.append(f'<h3>{esc(item["record_name"])} · {esc(item["facet"])}</h3>')
            rows.append(f'<div>{esc(item["statement"])}</div>')
            rows.append(f'<div class="text-small">{esc(item.get("qualification", ""))}</div>')
            rows.append(evidence(item.get('evidence', []), data.get('sources', {})))
        questions = lane.get('next_questions', []) + [e['statement'] for e in data.get('unresolved_edges', []) if e['lane'] == key]
        if questions:
            rows.append('<details><summary>Unresolved questions</summary><ul>' + ''.join(f'<li>{esc(q)}</li>' for q in dict.fromkeys(questions)) + '</ul></details>')
        hidden = ' hidden' if n else ''
        panels.append(f'<section class="lane" id="lane-{n}"{hidden}>' + ''.join(rows) + '</section>')
    output = STYLE + f'<h2>{esc(data.get("title", "Reviewed research connections"))}</h2>'
    relationship_word = 'relationship' if len(edges) == 1 else 'relationships'
    context_label = esc(data.get('context_label', 'reviewed context changes'))
    output += f'<div class="text-small">{len(edges)} established {relationship_word} · {len(context)} {context_label}</div>'
    output += '<div class="viz-controls"><label class="form-label">Research lane<select class="form-select">' + ''.join(options) + '</select></label></div>'
    output += '<div aria-live="polite">' + ''.join(panels) + '</div>' + SCRIPT
    return output + '\n' if fragment else DOCUMENT + output + '</body></html>\n'


STYLE = '''<div id="research-round-view"><style>
#research-round-view {display:grid;grid-template-columns:minmax(0,1fr);overflow-wrap:anywhere;gap:calc(var(--font-size-base)*1)}
#research-round-view .lane:not([hidden]) {display:grid;gap:calc(var(--font-size-base)*.75)}
#research-round-view .edge {display:flex;align-items:center;gap:calc(var(--font-size-base)*1)}
#research-round-view .node {flex:1;background:color-mix(in srgb,var(--viz-series-1) 10%,transparent);padding:calc(var(--font-size-base)*.75);overflow-wrap:anywhere}
#research-round-view .arrow {text-align:center}
#research-round-view ul {margin:0;padding-left:calc(var(--font-size-base)*1.5)}
#research-round-view li+li {margin-top:calc(var(--font-size-base)*.5)}
@media(max-width:480px) {#research-round-view .edge {flex-direction:column;align-items:stretch} #research-round-view .arrow span {display:inline-block;transform:rotate(90deg)}}
</style>'''

SCRIPT = '''<script>
(() => {
 const root=document.getElementById('research-round-view');
 const select=root.querySelector('select');
 const panels=Array.from(root.querySelectorAll('.lane'));
 function show(id) {
  if(!panels.some(panel=>panel.id===id))return;
  select.value=id;panels.forEach(panel=>{panel.hidden=panel.id!==id;});
 }
 select.addEventListener('change',()=>{
  show(select.value);
  window.openai?.setWidgetState?.({modelContent:{selectedResearchLane:select.options[select.selectedIndex].text},privateContent:{panel:select.value}})?.catch(()=>{});
 });
 const saved=window.openai?.widgetState?.privateContent?.panel;if(saved)show(saved);
 window.addEventListener('openai:set_globals',event=>{const id=event.detail?.globals?.widgetState?.privateContent?.panel;if(id)show(id);});
})();
</script></div>'''

DOCUMENT = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reviewed research connections</title><style>
:root {color-scheme:light dark;--font-size-base:14px;--background:light-dark(#fff,#181818);--foreground:light-dark(#202020,#eee);--muted-foreground:light-dark(#555,#bbb);--viz-series-1:light-dark(#386b59,#9bd5bd)}
body {margin:24px auto;padding:0 16px;max-width:880px;background:var(--background);color:var(--foreground);font:400 var(--font-size-base)/1.5 system-ui,sans-serif}
h2,h3 {margin:0;font-weight:500} h2 {font-size:1.4em} h3 {font-size:1.1em}
.text-small {font-size:.86em;color:var(--muted-foreground)}
.form-label {display:grid;grid-template-columns:minmax(0,1fr);gap:6px} .form-select {font:inherit;padding:8px;max-width:100%}
a {color:var(--viz-series-1)} summary {cursor:pointer}
</style></head><body>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--fragment', action='store_true')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(json.loads(args.results.read_text()), args.fragment))
    print(args.output)


if __name__ == '__main__':
    main()
