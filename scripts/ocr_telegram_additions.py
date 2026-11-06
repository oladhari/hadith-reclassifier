"""Free local OCR for imported scans/PDF pages; cache by input hash, no paid calls."""
import concurrent.futures,hashlib,json,os,sqlite3,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/research/imports/muawiya4n';CACHE=OUT/'ocr';CACHE.mkdir(exist_ok=True)
ARCHIVE=ROOT.parent/'telegram-archive/muawiya4n'
def recognize(task):
 sha,path,mime=task;target=CACHE/(sha+'.json')
 if target.exists():return json.loads(target.read_text())
 assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
 if mime=='application/pdf':
  folder=CACHE/sha;folder.mkdir(exist_ok=True)
  subprocess.run(['pdftoppm','-jpeg','-scale-to','2000',str(path),str(folder/'page')],capture_output=True,check=True,timeout=120)
  pages=sorted(folder.glob('page-*.jpg'),key=lambda p:int(p.stem.split('-')[-1]))
 else:pages=[path]
 results=[]
 for i,page in enumerate(pages,1):
  r=subprocess.run(['tesseract',str(page),'stdout','-l','ara+eng','--psm','3'],capture_output=True,text=True,timeout=120,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
  if r.returncode:raise RuntimeError(r.stderr[-500:])
  results.append({'page':i,'text':r.stdout.strip()})
 value={'sha256':sha,'method':'tesseract_ara_eng_unverified','pages':results,'text':'\n\n'.join(p['text'] for p in results),'review_state':'unverified'}
 tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False));tmp.replace(target)
 return value

def main():
 os.umask(0o077);db=sqlite3.connect(OUT/'filter.sqlite3',timeout=60);db.row_factory=sqlite3.Row
 db.execute('create table if not exists import_text_cache(sha256 TEXT PRIMARY KEY,text TEXT,method TEXT,pages INTEGER,review_state TEXT)');db.commit()
 tasks=[]
 for row in db.execute("select sha256,min(path) as path,mime from attachments where mime like 'image/%' or mime='application/pdf' group by sha256 order by mime,sha256"):
  if db.execute('select 1 from import_text_cache where sha256=?',(row['sha256'],)).fetchone():continue
  tasks.append((row['sha256'],ARCHIVE/row['path'],row['mime']))
 old=sqlite3.connect(f'file:{ROOT}/data/research/research.sqlite3?mode=ro',uri=True)
 exactcache={sha:text for sha,text in old.execute("select o.sha256,e.text from research_objects o join research_media m on m.object_id=o.id join research_extracts e on e.media_id=m.id where e.kind='ocr_text'")}
 pending=[]
 for sha,path,mime in tasks:
  if sha in exactcache:
   db.execute('insert or ignore into import_text_cache values(?,?,?,?,?)',(sha,exactcache[sha],'existing_exact_hash_ocr',1,'unverified'));db.commit()
  else:pending.append((sha,path,mime))
 processed=0
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  futures={pool.submit(recognize,task):task for task in pending}
  for future in concurrent.futures.as_completed(futures):
   task=futures[future]
   try:
    r=future.result();db.execute('insert or replace into import_text_cache values(?,?,?,?,?)',(r['sha256'],r['text'],r['method'],len(r['pages']),'unverified'));db.commit();processed+=1
    if processed%25==0 or task[2]=='application/pdf':print(json.dumps({'processed':processed,'pending_total':len(pending),'kind':task[2],'chars':len(r['text'])}),flush=True)
   except Exception as e:print(json.dumps({'failed_sha':task[0],'error':type(e).__name__+': '+str(e)}),flush=True)
 print('OCR_COMPLETE',db.execute('select count(*) from import_text_cache').fetchone()[0],flush=True)
if __name__=='__main__':main()
