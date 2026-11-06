#!/usr/bin/env python3
"""Download complete, explicitly enumerated source sets; validate archives and PDFs.

No AI calls. Source ZIPs remain intact; extraction writes only generated basenames.
"""
import hashlib
import json
import re
import subprocess
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data/research/rijal-sources/full-books'
SETS={3722:('000226_201802',35,'zip'),3310:('13-14-15-164486',12,'pdf'),8609:('alfirdwsiy2018_gmail_1957',1,'pdf'),1692:('MizaneLitidal2',4,'pdf'),12579:('190581',9,'zip')}


def sha(path,algorithm='sha256'):
 h=hashlib.new(algorithm)
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()


def download(identifier,item):
 suffix='.zip' if item['name'].endswith('.zip') else '.pdf'
 path=CACHE/'packages'/(item['sha1']+suffix);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.stat().st_size==int(item['size']) and sha(path,'sha1')==item['sha1']:return path
 url='https://archive.org/download/'+identifier+'/'+quote(item['name'])
 partial=path.with_suffix(path.suffix+'.part')
 for attempt in range(3):
  try:
   offset=partial.stat().st_size if partial.exists() else 0
   headers={'User-Agent':'Othmani public reference library'}
   if offset:headers['Range']=f'bytes={offset}-'
   with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90) as response:
    append=offset>0 and response.status==206
    if append and not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):raise ValueError('Unexpected resumed range')
    with partial.open('ab' if append else 'wb') as output:
     while block:=response.read(1024*1024):output.write(block)
   if partial.stat().st_size!=int(item['size']) or sha(partial,'sha1')!=item['sha1']:raise ValueError('Upstream size/checksum mismatch')
   partial.replace(path);print('Downloaded '+identifier+'/'+item['name']+' '+str(path.stat().st_size),flush=True);return path
  except Exception:
   if partial.exists() and partial.stat().st_size>=int(item['size']):partial.unlink()
   if attempt==2:raise
   time.sleep(attempt+1)


def validate_pdf(path):
 if path.read_bytes()[:5]!=b'%PDF-':raise ValueError('Not a PDF: '+str(path))
 result=subprocess.run(['pdfinfo',str(path)],capture_output=True,text=True,check=True)
 match=re.search(r'^Pages:\s+(\d+)',result.stdout,re.M)
 if not match or int(match[1])<1:raise ValueError('PDF has no pages')
 return int(match[1])


def main():
 CACHE.mkdir(parents=True,exist_ok=True);jobs=[]
 for book,(identifier,expected,format) in SETS.items():
  metadata_path=CACHE/f'{identifier}.metadata.json'
  if not metadata_path.exists():
   with urllib.request.urlopen('https://archive.org/metadata/'+identifier,timeout=60) as response:metadata=json.load(response)
   metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
  metadata=json.loads(metadata_path.read_text())
  selected=[]
  for item in metadata['files']:
   name=item['name']
   if format=='zip':
    if name.endswith('.zip') and item.get('format')=='ZIP':selected.append((1,item))
   elif book==3310:
    match=re.search(r'/(\d{2})_\d+\.pdf$',name)
    if match and 1<=int(match[1])<=12:selected.append((int(match[1]),item))
   elif book==1692:
    match=re.fullmatch(r'(0[1-4])_\d+\.pdf',name)
    if match:selected.append((int(match[1]),item))
    elif name=='00_15344.pdf':selected.append((0,item))
    elif name=='01_15344p.pdf':selected.append((90,item))
   elif book==8609 and name.endswith('.pdf') and not name.endswith('_text.pdf'):selected.append((1,item))
  if len(selected)!=(1 if format=='zip' else expected+(2 if book==1692 else 0)):raise ValueError(f'Incomplete source selection: {book}')
  for part,item in selected:jobs.append((book,identifier,part,item))
 assets=[]
 def process(job):
  book,identifier,part,item=job;source=download(identifier,item);destination=CACHE/str(book);destination.mkdir(exist_ok=True);pdfs=[]
  if source.suffix=='.zip':
   with zipfile.ZipFile(source) as archive:
    if sum(i.file_size for i in archive.infolist())>2_000_000_000:raise ValueError('Archive expands beyond expected limit')
    files=[i for i in archive.infolist() if not i.is_dir() and i.filename.lower().endswith('.pdf')]
    print('ZIP contents '+str(book)+' '+json.dumps([(i.filename,i.file_size) for i in files],ensure_ascii=False),flush=True)
    for index,entry in enumerate(sorted(files,key=lambda i:i.filename),1):
     target=destination/f'extracted-{index:02}.pdf'
     body=archive.read(entry)
     if not target.exists() or hashlib.sha256(body).hexdigest()!=sha(target):target.write_bytes(body)
     part_match=re.search(r'(\d+)$',Path(entry.filename).stem)
     if not part_match:raise ValueError('Unknown source volume number')
     pdfs.append((int(part_match[1]),target,entry.filename))
  else:pdfs=[(part,source,item['name'])]
  results=[]
  for number,path,source_name in pdfs:
   pages=validate_pdf(path)
   results.append({'book_id':book,'part':number,'local_path':str(path.relative_to(ROOT)),
     'original_name':source_name,'source_archive':identifier,'source_url':'https://archive.org/download/'+identifier+'/'+quote(item['name']),
     'source_sha1':item['sha1'],'sha256':sha(path),'bytes':path.stat().st_size,'pages':pages})
  return results
 with ThreadPoolExecutor(max_workers=5) as pool:
  futures=[pool.submit(process,job) for job in jobs]
  for future in as_completed(futures):
   assets.extend(future.result())
   (CACHE/'download-assets.partial.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2))
 old=json.loads((CACHE.parent/'ibn-abi-hatim-r2-manifest.json').read_text())
 for obj in old['objects']:
  if obj['role'] not in {'scanned_volume','cover'}:continue
  part=0 if obj['role']=='cover' else obj['part']
  path=CACHE.parent/'ibn-abi-hatim-originals'/('cover.pdf' if part==0 else f'volume-{part:02}.pdf')
  if sha(path)!=obj['sha256']:raise ValueError('Previously archived PDF changed')
  assets.append({'book_id':2170,'part':part,'local_path':str(path.relative_to(ROOT)),
    'original_name':obj['original_name'],'source_archive':old['archive_identifier'],'source_url':obj['source_url'],
    'source_sha1':obj['sha1'],'sha256':obj['sha256'],'bytes':obj['bytes'],'pages':validate_pdf(path),'previous_r2_key':obj['r2_key']})
 assets.sort(key=lambda a:(a['book_id'],a['part']))
 (CACHE/'download-assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2))
 for book in [2170,*SETS]:print('Book PDF files:',book,sum(a['book_id']==book for a in assets),flush=True)
 print('Downloaded PDF bytes:',sum(a['bytes'] for a in assets),flush=True)


if __name__=='__main__':main()
