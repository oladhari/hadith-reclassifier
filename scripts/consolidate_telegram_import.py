"""Consolidate private import listings and remove redundant byte-identical disk copies.
Archive filenames, original bytes, source occurrences and explanations remain accessible.
No public/production writes, R2 deletion or visual-variant original deletion.
"""
import collections,hashlib,json,os,sqlite3
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/research/imports/muawiya4n'
ARCHIVE=ROOT.parent/'telegram-archive/muawiya4n'

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
 os.umask(0o077)
 c=sqlite3.connect(OUT/'filter.sqlite3');c.row_factory=sqlite3.Row
 old=sqlite3.connect(f'file:{ROOT}/data/research/research.sqlite3?mode=ro',uri=True);old.row_factory=sqlite3.Row
 now=datetime.now(timezone.utc).isoformat()
 with sqlite3.connect(OUT/('pre-consolidation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.sqlite3')) as b:c.backup(b)
 objects={}
 for r in c.execute('select * from attachments order by message_id'):
  obj=objects.setdefault(r['sha256'],{'sha':r['sha256'],'mime':r['mime'],'occurrences':[],'paths':[]})
  obj['occurrences'].append(r['message_id']);obj['paths'].append(r['path'])
 oldhashes=collections.defaultdict(list)
 for r in old.execute('select o.sha256,m.legacy_id from research_objects o join research_media m on m.object_id=o.id'):
  oldhashes[r['sha256']].append(r['legacy_id'])
 settings=old.execute("select value from research_catalogue_settings where key='media_catalogue'").fetchone()
 public=json.loads(settings[0]).get('public',{}) if settings else {}
 def existing_target(hashes):
  ids=sorted({mid for sha in hashes for mid in oldhashes[sha]})
  assert ids
  return min(public.get(str(mid),{}).get('canonical_id',mid) for mid in ids)
 groups=json.loads((OUT/'visual-review/groups.json').read_text())
 mapping={k:g for g in groups for k in g['members']}
 listings={};aliases=[]
 for sha,obj in objects.items():
  g=mapping.get('new:'+sha);members=g['members'] if g else ['new:'+sha]
  existing_hashes={key[4:] for key in members if key.startswith('old:')}
  if sha in oldhashes:existing_hashes.add(sha)
  if existing_hashes:
   target='library:'+str(existing_target(existing_hashes));action='upgrade_existing' if g and g['preferred_id'].startswith('new:') else 'link_existing'
  else:
   target=g['group_id'] if g else 'sha256:'+sha;action='new_item'
  preferred=g['preferred_id'] if g else 'new:'+sha
  listing=listings.setdefault(target,{'canonical_key':target,'action':action,'preferred_object_id':preferred,'import_hashes':[],'source_message_ids':[],'explanations':[]})
  listing['import_hashes'].append(sha);listing['source_message_ids'].extend(obj['occurrences'])
  for mid in obj['occurrences']:aliases.append({'message_id':mid,'sha256':sha,'canonical_key':target})
 # Attach original explanations, with relationship/context and source IDs intact.
 alias_by_mid={a['message_id']:a['canonical_key'] for a in aliases}
 for r in c.execute('select l.*,p.text,p.permalink from explanation_links l join posts p on p.id=l.text_message_id'):
  listings[alias_by_mid[r['attachment_message_id']]]['explanations'].append(dict(r))
 # Keep variants/distinct pairs separate even when transitively consolidating.
 for r in c.execute("select import_id,other_id from visual_review_decisions where decision!='same_page_or_image'"):
  if r['import_id'].startswith('new:') and r['other_id'].startswith('new:'):
   keys=[]
   for key in r:keys.append(alias_by_mid[objects[key[4:]]['occurrences'][0]])
   assert keys[0]!=keys[1],'Protected variant would be lost'
 c.executescript('''CREATE TABLE IF NOT EXISTS consolidated_import_listings(canonical_key TEXT PRIMARY KEY,action TEXT,preferred_object_id TEXT,payload TEXT);
 CREATE TABLE IF NOT EXISTS consolidated_import_aliases(message_id INTEGER PRIMARY KEY,sha256 TEXT,canonical_key TEXT);
 CREATE TABLE IF NOT EXISTS consolidation_history(fingerprint TEXT PRIMARY KEY,payload TEXT,recorded_at TEXT);
 CREATE TABLE IF NOT EXISTS storage_copy_consolidations(path TEXT PRIMARY KEY,canonical_path TEXT,sha256 TEXT,bytes INTEGER,consolidated_at TEXT);''')
 # Atomic hardlink replacement removes redundant disk copies without breaking names.
 reclaimed=0;replaced=0
 for sha,obj in objects.items():
  paths=[ARCHIVE/p for p in obj['paths']]
  base=paths[0]
  if len(paths)<2:continue
  assert not base.is_symlink() and base.resolve().is_relative_to(ARCHIVE.resolve())
  assert digest(base)==sha
  for path in paths[1:]:
   assert not path.is_symlink() and path.resolve().is_relative_to(ARCHIVE.resolve())
   if os.path.samefile(base,path):continue
   assert path.stat().st_dev==base.stat().st_dev and path.stat().st_size==base.stat().st_size and digest(path)==sha
   size=path.stat().st_size;tmp=path.with_name(path.name+'.dedup-link')
   if tmp.exists():raise RuntimeError('Unexpected dedup temporary file')
   try:
    os.link(base,tmp);os.replace(tmp,path)
   finally:
    if tmp.exists():tmp.unlink()
   assert os.path.samefile(base,path) and digest(path)==sha
   c.execute('insert or replace into storage_copy_consolidations values(?,?,?,?,?)',(str(path),str(base),sha,size,now));c.commit()
   reclaimed+=size;replaced+=1
 for row in listings.values():
  payload=json.dumps(row,ensure_ascii=False,sort_keys=True)
  c.execute('insert or replace into consolidated_import_listings values(?,?,?,?)',(row['canonical_key'],row['action'],row['preferred_object_id'],payload))
  c.execute('insert or ignore into consolidation_history values(?,?,?)',(hashlib.sha256(payload.encode()).hexdigest(),payload,now))
 for a in aliases:c.execute('insert or replace into consolidated_import_aliases values(?,?,?)',(a['message_id'],a['sha256'],a['canonical_key']))
 c.commit()
 assert len(aliases)==1428 and sum(len(x['explanations']) for x in listings.values())==1798
 assert c.execute('pragma integrity_check').fetchone()[0]=='ok'
 counts=dict(collections.Counter(r['action'] for r in listings.values()))
 report={'source_attachment_occurrences':len(aliases),'unique_import_files':len(objects),'consolidated_targets':len(listings),'repeated_import_cards_suppressed':len(aliases)-len(listings),'actions':counts,'new_byte_copies_removed':replaced,'new_bytes_reclaimed':reclaimed,'total_local_copies_consolidated':c.execute('select count(*) from storage_copy_consolidations').fetchone()[0],'all_source_paths_retained':True,'explanation_associations_retained':1798,'r2_files_deleted':0,'production_changed':False,'publication_state':'private_prepared_import; needs OCR and Arabic editorial metadata before website publication'}
 (OUT/'consolidated-import.json').write_text(json.dumps(list(listings.values()),ensure_ascii=False,indent=2))
 (OUT/'consolidation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
