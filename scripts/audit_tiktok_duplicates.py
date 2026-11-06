"""Find duplicate candidates using duration and five perceptual frame hashes.

Read-only comparison of the downloaded profile and the existing local video
archive, including hidden material. Candidates require manual visual/audio review;
this script never merges records or changes visibility. Requires OpenCV and NumPy.
"""
import json,sqlite3,hashlib,concurrent.futures
from pathlib import Path
import cv2,numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=Path('/mnt/linuxdata/othmani-tiktok/brad2557wtn/review');OUT.mkdir(exist_ok=True)
d=json.loads(Path('/mnt/linuxdata/othmani-tiktok/brad2557wtn/manifest.json').read_text())['videos'];jobs=[]
for id,v in d.items():
 if v.get('kind')!='audio':jobs.append({'id':'tt:'+id,'path':v['local_path'],'sha':v['sha256'],'duration':v['duration']})
archive=json.loads((ROOT/'frontend/src/content/archive-index.json').read_text());cat=json.loads((ROOT/'frontend/src/content/media-catalogue.json').read_text());db=sqlite3.connect(f'file:{ROOT}/data/research/research.sqlite3?mode=ro',uri=True)
for a in archive:
 if a['kind']!='video':continue
 row=db.execute('select o.sha256 from research_media m join research_objects o on o.id=m.object_id where m.legacy_id=?',(a['id'],)).fetchone()
 path=ROOT/'../telegram-archive/kkee9938'/a['path']
 if not path.exists():path=ROOT/'../telegram-archive'/a['path']
 if path.exists():jobs.append({'id':'old:'+str(a['id']),'path':str(path.resolve()),'sha':row[0] if row else '', 'duration':cat.get(str(a['id']),{}).get('duration',0)})
def work(j):
 p=OUT/(j['id'].replace(':','-')+'.json')
 if p.exists():return json.loads(p.read_text())
 c=cv2.VideoCapture(j['path'],cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1]);fps=c.get(cv2.CAP_PROP_FPS);count=c.get(cv2.CAP_PROP_FRAME_COUNT);duration=count/fps if fps else j['duration'];hashes=[]
 for fraction in [.1,.3,.5,.7,.9]:
  c.set(cv2.CAP_PROP_POS_MSEC,duration*fraction*1000);ok,f=c.read()
  if not ok:break
  gray=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY);small=cv2.resize(gray,(9,8),interpolation=cv2.INTER_AREA);bits=small[:,1:]>small[:,:-1];hashes.append(int.from_bytes(np.packbits(bits).tobytes(),'big'))
 c.release();r={**j,'duration':duration,'hashes':hashes};p.write_text(json.dumps(r));return r
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:rows=list(e.map(work,jobs))
print('Fingerprinted',len(rows),flush=True)
exact={}
for row in rows:
 if row['sha']:exact.setdefault(row['sha'],[]).append(row['id'])
(OUT/'exact-hash-groups.json').write_text(json.dumps({sha:ids for sha,ids in exact.items() if len(ids)>1 and any(id.startswith('tt:') for id in ids)}))
pairs=[]
for i,a in enumerate(rows):
 if not a['id'].startswith('tt:') or len(a['hashes'])!=5:continue
 for b in rows[i+1:]:
  if len(b['hashes'])!=5 or abs(a['duration']-b['duration'])>max(1.5,a['duration']*.01):continue
  dist=[(x^y).bit_count() for x,y in zip(a['hashes'],b['hashes'])]
  if sum(dist)<=25 and max(dist)<=10:pairs.append({'a':a,'b':b,'dist':dist})
(OUT/'candidates.json').write_text(json.dumps(pairs));(OUT/'inventory.json').write_text(json.dumps(rows));print('Candidate pairs',len(pairs),flush=True)
