"""Acquire the versions actually inspected for the ENE contribution."""
import concurrent.futures, hashlib, json, pathlib, datetime
import requests
from pypdf import PdfReader
from bs4 import BeautifulSoup

BASE=pathlib.Path(__file__).resolve().parent
CACHE=BASE/'cache'
CACHE.mkdir(exist_ok=True)
URLS={
 'ENE-S01':'https://wikis.mit.edu/confluence/download/attachments/21139745/Nemet_BeyondtheLearningCurve_EP_06.pdf?api=v2',
 'ENE-S02':'https://static1.squarespace.com/static/56afb881e321406be6160228/t/5bff10822b6a2884d7267f17/1543442566890/Evaluating%2Bthe%2Bcauses%2Bof%2Bcost%2Breduction%2Bin%2Bphotovoltaic%2Bmodules.pdf',
 'ENE-S03':'https://minesparis-psl.hal.science/hal-00498578v1/document',
 'ENE-S04':'https://core.ac.uk/download/pdf/82188133.pdf',
 'ENE-S05':'https://pure.iiasa.ac.at/id/eprint/11077/1/The%20French%20Pressurised%20Water%20Reactor%20Programme.pdf',
 'ENE-S06':'https://dspace.mit.edu/bitstream/handle/1721.1/133049/Jacopo%27s%20and%20Jessika%27s%20paper%20on%20nuclear%20cost%20Sep%202020.pdf',
 'ENE-S07':'https://patents.google.com/patent/US3025589A/en',
 'ENE-S08':'https://www.nasa.gov/wp-content/uploads/static/history/computers/Ch2-4.html',
 'ENE-S09':'https://gwern.net/doc/economics/experience-curve/1994-irwin.pdf',
 'ENE-S10':'https://www.nobelprize.org/uploads/2019/10/yoshino-lecture.pdf',
 'ENE-S11':'https://pubs.rsc.org/en/content/articlepdf/2021/ee/d1ee01313k',
 'ENE-S12':'https://escholarship.org/content/qt0d05f8v9/qt0d05f8v9.pdf',
 'ENE-S13':'https://itspubs.ucdavis.edu/download_pdf.php?id=1289',
 'ENE-S14':'https://www.computerhistory.org/siliconengine/invention-of-the-planar-manufacturing-process/',
}

def acquire(item):
 sid,url=item
 result={'source_id':sid,'requested_url':url,'accessed':'2026-11-05'}
 try:
  r=requests.get(url, timeout=45)
  result.update(status=r.status_code, final_url=r.url, content_type=r.headers.get('content-type',''))
  r.raise_for_status()
  ext='.pdf' if r.content.startswith(b'%PDF') else '.html'
  path=CACHE/(sid+ext)
  path.write_bytes(r.content)
  result.update(path=str(path.relative_to(BASE)),sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content))
  if ext=='.pdf':
   reader=PdfReader(path)
   txt='\n\n'.join(f'--- PDF PAGE {i+1} ---\n'+(p.extract_text() or '') for i,p in enumerate(reader.pages))
   result['pages']=len(reader.pages)
  else:
   soup=BeautifulSoup(r.text,'html.parser')
   for el in soup(['script','style']):el.decompose()
   txt=soup.get_text('\n',strip=True)
  (CACHE/(sid+'.txt')).write_text(txt)
  result['text_characters']=len(txt)
 except Exception as e:result['error']=str(e)
 return result

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  results=list(pool.map(acquire,URLS.items()))
 (CACHE/'download_manifest.json').write_text(json.dumps(results,indent=2))
 for r in results:print(r['source_id'],r.get('status'),r.get('pages'),r.get('text_characters'),r.get('error',''))
