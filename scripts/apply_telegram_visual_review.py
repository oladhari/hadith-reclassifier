"""Persist the completed Codex visual review in private staging, retaining history.
Does not modify production/public catalogue, media bytes, captions or source posts.
"""
import collections,hashlib,json,os,sqlite3
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/research/imports/muawiya4n'
REVIEW=OUT/'visual-review'

def main():
 os.umask(0o077)
 pairs=json.loads((REVIEW/'pairs.json').read_text())
 obs=json.loads((REVIEW/'observations.json').read_text())
 covered={n for start,end in obs['reviewed_ranges'] for n in range(start,end+1)}
 assert covered=={r['pair'] for r in pairs},'Every candidate must have recorded visual inspection'
 c=sqlite3.connect(OUT/'filter.sqlite3');c.row_factory=sqlite3.Row
 now=datetime.now(timezone.utc).isoformat()
 backup=REVIEW/('pre-review-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3')
 with sqlite3.connect(backup) as b:c.backup(b)
 c.executescript('''
 CREATE TABLE IF NOT EXISTS visual_review_decisions(
 import_id TEXT,other_id TEXT,reason TEXT,pair_number INTEGER,decision TEXT,preferred_id TEXT,
 notes TEXT,evidence TEXT,reviewer TEXT,reviewed_at TEXT,PRIMARY KEY(import_id,other_id,reason));
 CREATE TABLE IF NOT EXISTS visual_review_history(
 fingerprint TEXT PRIMARY KEY,import_id TEXT,other_id TEXT,decision_payload TEXT,recorded_at TEXT);
 CREATE TABLE IF NOT EXISTS visual_groups(
 group_id TEXT PRIMARY KEY,preferred_id TEXT,selection_basis TEXT);
 CREATE TABLE IF NOT EXISTS visual_group_members(
 object_id TEXT PRIMARY KEY,group_id TEXT REFERENCES visual_groups(group_id));
 ''')
 decisions=[];parent={};quality_winners=set();quality_losers=set()
 def find(x):
  parent.setdefault(x,x)
  if parent[x]!=x:parent[x]=find(parent[x])
  return parent[x]
 def union(a,b):
  a=find(a);b=find(b)
  if a!=b:parent[max(a,b)]=min(a,b)
 inspections={r['id']:json.loads(r['payload']) for r in c.execute('select * from inspections')}
 # Prefixes identify archives, not content. Exact bytes always share identity.
 byhash=collections.defaultdict(list)
 for key in inspections:byhash[key.split(':',1)[1]].append(key)
 for ids in byhash.values():
  for other in ids[1:]:union(ids[0],other)
 for row in pairs:
  n=str(row['pair']);a=row['a'];b=row['b'];preferred=None
  if n in obs['distinct_pairs']:
   decision='distinct_keep_separate';notes=obs['distinct_pairs'][n]
  elif n in obs['annotation_variants']:
   decision='annotation_variant_keep_both';notes=obs['annotation_variants'][n]
  else:
   decision='same_page_or_image';notes='Matching page/image content and composition in side-by-side visual comparison; originals and source explanations retained.'
   union(a,b)
   if row['pair'] in obs.get('quality_preferred_a',[]):preferred=a
   elif row['pair'] in obs.get('quality_preferred_b',[]):preferred=b
   if preferred:
    quality_winners.add(preferred);quality_losers.add(b if preferred==a else a)
    notes+=' Enlarged corresponding detail confirms preferred version has clearer detail.'
   else:notes+=' No material clarity advantage established; keep existing catalogue identity when available.'
  evidence=[f"sheet-{(row['pair']-1)//16+1:02}.jpg"]
  if (REVIEW/f"detail-{row['pair']}.jpg").exists():evidence.append(f"detail-{row['pair']}.jpg")
  if preferred:evidence.extend(['quality-1.jpg','quality-2.jpg','quality-3.jpg','quality-4.jpg','quality-5.jpg'])
  record={'pair':row['pair'],'a':a,'b':b,'decision':decision,'preferred':preferred,'notes':notes,'evidence':evidence,'reviewer':'codex_visual_review_not_scholarly_approval'}
  decisions.append(record)
  payload=json.dumps(record,ensure_ascii=False,sort_keys=True);fingerprint=hashlib.sha256(payload.encode()).hexdigest()
  c.execute('insert or ignore into visual_review_history values(?,?,?,?,?)',(fingerprint,a,b,payload,now))
  c.execute('insert into visual_review_decisions values(?,?,?,?,?,?,?,?,?,?) on conflict(import_id,other_id,reason) do update set decision=excluded.decision,preferred_id=excluded.preferred_id,notes=excluded.notes,evidence=excluded.evidence,reviewer=excluded.reviewer,reviewed_at=excluded.reviewed_at',(a,b,'similar_image_candidate',row['pair'],decision,preferred,notes,json.dumps(evidence),record['reviewer'],now))
  c.execute('update candidates set review_state=? where import_id=? and other_id=? and reason=?',(decision,a,b,'similar_image_candidate'))
  find(a);find(b)
 # Fail closed if a transitive chain would absorb a protected distinct/variant pair.
 for row in decisions:
  if row['decision']!='same_page_or_image':assert find(row['a'])!=find(row['b']),('Protected pair incorrectly grouped',row['pair'])
 components=collections.defaultdict(list)
 for key in parent:components[find(key)].append(key)
 c.execute('delete from visual_group_members');c.execute('delete from visual_groups')
 groups=[]
 for keys in components.values():
  if len(keys)<2:continue
  winners=[k for k in keys if k in quality_winners and k not in quality_losers]
  if winners:
   preferred=sorted(winners,key=lambda k:(-(inspections[k].get('width',0)*inspections[k].get('height',0)),not k.startswith('old:'),k))[0]
   basis='Visually confirmed detail advantage; all alternative originals retained'
  else:
   preferred=sorted(keys,key=lambda k:(not k.startswith('old:'),k))[0]
   basis='Visually equivalent page/image; preserve existing identity where available, no quality superiority claimed'
  gid='visual:'+hashlib.sha256('|'.join(sorted(keys)).encode()).hexdigest()[:24]
  c.execute('insert into visual_groups values(?,?,?)',(gid,preferred,basis))
  for key in keys:c.execute('insert into visual_group_members values(?,?)',(key,gid))
  groups.append({'group_id':gid,'preferred_id':preferred,'selection_basis':basis,'members':sorted(keys)})
 c.commit()
 assert c.execute("select count(*) from candidates where review_state='needs_visual_review'").fetchone()[0]==0
 assert c.execute('pragma integrity_check').fetchone()[0]=='ok'
 # Preserve every imported explanation and its own attachment context when grouping.
 groups_by_object={key:g for g in groups for key in g['members']}
 explanations=[]
 for r in c.execute('''select l.*,a.sha256,p.text,p.permalink from explanation_links l
 join attachments a on a.message_id=l.attachment_message_id join posts p on p.id=l.text_message_id'''):
  item=dict(r);g=groups_by_object.get('new:'+r['sha256']);item['visual_group_id']=g['group_id'] if g else None
  item['preferred_object_id']=g['preferred_id'] if g else 'new:'+r['sha256'];explanations.append(item)
 (REVIEW/'decisions.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2))
 (REVIEW/'groups.json').write_text(json.dumps(groups,ensure_ascii=False,indent=2))
 (REVIEW/'explanations.json').write_text(json.dumps(explanations,ensure_ascii=False,indent=2))
 summary={'reviewed_pairs':len(decisions),'decisions':dict(collections.Counter(r['decision'] for r in decisions)),
 'preferred_quality_comparisons':sum(r['preferred'] is not None for r in decisions),'same_content_groups':len(groups),
 'groups_with_imported_quality_upgrade':sum(g['preferred_id'].startswith('new:') and g['preferred_id'] in quality_winners and any(k.startswith('old:') for k in g['members']) for g in groups),
 'explanation_associations_preserved':len(explanations),'originals_deleted':0,'production_catalogue_modified':False,
 'scope':'All 305 flagged image pairs. PDF page-by-page review is separate; no scholarly approval implied.'}
 (REVIEW/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
