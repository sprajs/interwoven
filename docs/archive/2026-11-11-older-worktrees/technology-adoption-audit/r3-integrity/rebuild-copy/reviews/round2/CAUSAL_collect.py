from pathlib import Path
import json,hashlib,shutil,subprocess,datetime,urllib.request
root=Path(__file__).resolve().parents[2]
out=Path(__file__).resolve().parent/'CAUSAL_evidence'
sources={s['id']:s for s in json.loads((root/'reviews/round2/full-snapshot/data/sources.json').read_text())}
cache={
'PSY-S01':'contributions/PSY/cache/S01.pdf', 'PSY-S02':'contributions/PSY/cache/S02.pdf','PSY-S03':'contributions/PSY/cache/S03.pdf',
'ENE-S01':'contributions/ENE/cache/ENE-S01.pdf','ENE-S02':'contributions/ENE/cache/ENE-S02.pdf','ENE-S03':'contributions/ENE/cache/ENE-S03.pdf',
'SKL-S08':'contributions/SKL/cache/grace.pdf','SKL-S10':'contributions/SKL/cache/collins1974.pdf',
'OCE-S05':'contributions/OCE/provenance/OCE-S05.pdf','OCE-S06':'contributions/OCE/provenance/OCE-S06.html','OCE-S07':'contributions/OCE/provenance/OCE-S07.pdf','OCE-S08':'contributions/OCE/provenance/OCE-S08.html',
'AGR-S13':'contributions/AGR/evidence/clasen2022.pdf','AGR-S11':'contributions/AGR/evidence/karlan2014.pdf',
'MED-S06':'reviews/round1/SOURCE_AUDIT_materials/MED-S06.pdf','LBR-S02':'reviews/round1/SOURCE_AUDIT_materials/LBR-S02.pdf'}
records=[]
for sid,rel in cache.items():
 src=root/rel; target=out/(sid+src.suffix); shutil.copy2(src,target)
 if target.suffix=='.pdf': subprocess.run(['pdftotext','-layout',str(target),str(target.with_suffix('.txt'))],check=True)
 elif target.suffix=='.html':
  from bs4 import BeautifulSoup
  target.with_suffix('.txt').write_text(BeautifulSoup(target.read_text(),'html.parser').get_text('\n',strip=True))
 records.append({'id':sid,'title':sources[sid]['title'],'edition_metadata':sources[sid]['year'],'url':sources[sid]['url'],'access':'copied original bytes from existing local cache; independently reopened selected passages; not previous reviewer findings','cache_path':rel,'frozen_path':str(target.relative_to(root)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'copied_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
for sid in ['NET-S16','AGR-S16']:
 target=out/(sid+'.pdf')
 try:
  req=urllib.request.Request(sources[sid]['url'],headers={'User-Agent':'Mozilla/5.0'})
  raw=urllib.request.urlopen(req,timeout=45).read()
  if not raw.startswith(b'%PDF'): raise ValueError('not PDF bytes')
  target.write_bytes(raw);subprocess.run(['pdftotext','-layout',str(target),str(target.with_suffix('.txt'))],check=True)
  records.append({'id':sid,'title':sources[sid]['title'],'edition_metadata':sources[sid]['year'],'url':sources[sid]['url'],'access':'fresh download of original','frozen_path':str(target.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'downloaded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 except Exception as ex: records.append({'id':sid,'url':sources[sid]['url'],'access':'failed download','error':str(ex)})
(out.parent/'CAUSAL_SOURCE_PROVENANCE_R2.json').write_text(json.dumps({'sources':records,'note':'Originals, not reports. Copying does not assert independent study lineage; selected passage review scope added separately.'},indent=2)+'\n')
print(json.dumps([{'id':r['id'],'access':r['access'],'bytes':r.get('bytes')} for r in records]))
