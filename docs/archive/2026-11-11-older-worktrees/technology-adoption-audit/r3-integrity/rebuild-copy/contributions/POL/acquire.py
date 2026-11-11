from pathlib import Path
import urllib.request, hashlib, json, subprocess, concurrent.futures, datetime
ROOT=Path(__file__).parent
URLS={
'POL-S01':'https://www.isc.meiji.ac.jp/~transfer/papers/en/pdf/06/04_Enomoto.pdf',
'POL-S03':'https://www.cambridge.org/core/services/aop-cambridge-core/content/view/AD08FBBF2D32EDBC28B3AE2D7200CBCF/S1479591426100886a.pdf/introduction_the_reception_of_the_harquebus_in_east_and_southeast_asia.pdf',
'POL-S04':'https://www.hoover.org/sites/default/files/2025-01/Rise%20and%20Demise%20of%20Paper%20Money%20in%20Yuan%20China.pdf',
'POL-S06':'https://afe.easia.columbia.edu/mongols/figures/ser_xxiv.pdf',
'POL-S07':'https://assets.aeaweb.org/asset-server/files/13141.pdf',
'POL-S10':'https://annales.ensmp.fr/articles/1812-1/235-245.pdf',
'POL-S11':'https://comptes-rendus.academie-sciences.fr/physique/item/10.1016/j.crhy.2018.12.002.pdf',
'POL-S12':'https://archives.isere.fr/sites/isere-archives-fr/files/inline-files/ca_13_poids_mesures_protege.pdf',
'POL-S13':'https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nbsspecialpublication345-10.pdf',
}
def acquire(x):
 sid,url=x; row={'source_id':sid,'url':url,'accessed':'2026-11-05'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req, timeout=35) as r: data=r.read(); row.update(status=r.status,content_type=r.headers.get('Content-Type'),final_url=r.url)
  if not data.startswith(b'%PDF'): raise RuntimeError('Response not PDF')
  f=ROOT/'evidence'/f'{sid}.pdf'; f.write_bytes(data)
  row.update(file=str(f.relative_to(ROOT)),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
  subprocess.run(['pdftotext','-layout',str(f),str(f.with_suffix('.txt'))],check=True,capture_output=True)
 except Exception as e: row['error']=str(e)
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 results=list(pool.map(acquire,URLS.items()))
(ROOT/'evidence'/'download_manifest_latest_run.json').write_text(json.dumps(results,indent=2)+'\n')
for x in results: print(x['source_id'],x.get('bytes',x.get('error')))
