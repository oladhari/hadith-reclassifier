"""Add a channel-scoped catalogue import and reviewed public projection to Othmani.
Private provenance remains private; all writes are transactional and backed up.
"""
import argparse,hashlib,json,os,sqlite3,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
import psycopg
from psycopg import sql
from psycopg.types.json import Json
from publish_research_database import configuration
from materialize_public_catalogue import refresh_public_read_tables
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.research.catalogue import uid
OUT=ROOT/'data/research/imports/muawiya4n';OFFSET=1_000_000

def ident(kind,value):return str(uuid.uuid5(uuid.NAMESPACE_URL,f'othmani:muawiya4n:{kind}:{value}'))
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
JSONCOLS={'inputs','original_payload','parameters','result_extract_ids'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--sync-cloud',action='store_true');args=p.parse_args();os.umask(0o077)
 plan=json.loads((OUT/'publication-plan.json').read_text())
 stage=sqlite3.connect(OUT/'filter.sqlite3');stage.row_factory=sqlite3.Row
 local=sqlite3.connect(ROOT/'data/research/research.sqlite3');local.row_factory=sqlite3.Row
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 with sqlite3.connect(OUT/f'pre-publication-{stamp}.sqlite3') as b:local.backup(b)
 local.execute('pragma foreign_keys=on')
 values=configuration(ROOT/'.env')
 rows={t:[] for t in ['research_imports','research_sources','research_provenance','research_albums','research_album_members','research_objects','research_storage_locations','research_media','research_extracts']}
 posts=stage.execute('select * from posts order by id').fetchall();attachments={r['message_id']:dict(r) for r in stage.execute('select * from attachments')}
 fingerprint=digest(''.join(r['payload'] for r in posts));batch=ident('import',fingerprint)
 rows['research_imports'].append(dict(id=batch,fingerprint=fingerprint,inputs={'channel':'muawiya4n','snapshot_posts':len(posts),'method':'reviewed_additive_import'},created_at=now))
 object_ids={r['sha256']:r['id'] for r in local.execute('select id,sha256 from research_objects')}
 archive={r['id']:r for r in plan['archive']};albums={};seenobjects=set()
 textcache={r['sha256']:dict(r) for r in stage.execute('select * from import_text_cache')}
 for post in posts:
  mid=post['id'];numeric=OFFSET+mid;sourceid=ident('source',mid);payload=json.loads(post['payload']);date=payload.get('date');a=attachments.get(mid)
  entry=plan['public'].get(str(numeric),{})
  rows['research_sources'].append(dict(id=sourceid,legacy_id=numeric,reference_code=f'MUW-{mid:06d}',source_date=date,kind='attachment' if a else 'research_lead',review_state='imported',reviewed_by=None,reviewed_at=None,editorial_title=entry.get('title') or None,created_at=now))
  rows['research_provenance'].append(dict(id=ident('provenance',str(mid)+digest(post['payload'])),source_id=sourceid,import_id=batch,provider='telegram_collection',external_id=f'muawiya4n:{mid}',content_sha256=digest(post['payload']),original_text=post['text'],original_payload=payload,created_at=now))
  group=payload.get('grouped_id')
  if group:albums.setdefault(str(group),[]).append(mid)
  if not a:continue
  sha=a['sha256'];objectid=object_ids.get(sha,uid('object',sha));item=archive[numeric]
  if sha not in seenobjects:
   rows['research_objects'].append(dict(id=objectid,sha256=sha,byte_size=item['size'],mime_type=a['mime'],object_key=item['object_key'],created_at=now))
   seenobjects.add(sha)
   upload=stage.execute('select r2_key from attachments where sha256=? and r2_key is not null limit 1',(sha,)).fetchone()
   assert upload and upload[0].endswith(sha)
   rows['research_storage_locations'].append(dict(id=ident('local-location',sha),object_id=objectid,provider='local',bucket='',key=item['path'],state='available',verified_at=now))
   rows['research_storage_locations'].append(dict(id=ident('location',sha),object_id=objectid,provider='r2',bucket=values['R2_BUCKET'],key=upload[0],state='available',verified_at=now))
  mediaid=ident('media',mid)
  rows['research_media'].append(dict(id=mediaid,source_id=sourceid,object_id=objectid,legacy_id=numeric,kind=item['kind'],original_name=item['name'],mime_type=a['mime'],archive_relative_path=item['path'],source_date=date,created_at=now))
  cached=textcache.get(sha)
  if cached and cached['text'].strip():
   text=cached['text'];kind='pdf_text' if a['mime']=='application/pdf' else 'ocr_text'
   rows['research_extracts'].append(dict(id=ident('extract',str(mid)+digest(text)),source_id=sourceid,media_id=mediaid,kind=kind,text=text,text_sha256=digest(text),ordinal=0,language='ar',start_ms=None,end_ms=None,review_state='unverified',method=cached['method'][:80],created_at=now))
 for group,members in albums.items():
  aid=ident('album',group);rows['research_albums'].append(dict(id=aid,external_group_id='muawiya4n:'+group,created_at=now))
  for pos,mid in enumerate(sorted(members)):rows['research_album_members'].append(dict(album_id=aid,source_id=ident('source',mid),position=pos))
 def merge_setting(previous):
  current=dict(previous['public'])
  allowed=['topics','cases','tags','bundles','explanations','has_document_text','preferred_media_id','asset_size','occurrences']
  for key,entry in plan['public'].items():
   if int(key)<OFFSET and key in current:
    merged=dict(current[key])
    for field in allowed:
     if field in entry:merged[field]=entry[field]
    previous['public'][key]=merged
   else:previous['public'][key]=entry
  # Imported aliases inherit live canonical visibility and editorial identity.
  for key,entry in plan['public'].items():
   if int(key)>=OFFSET and entry['canonical_id']<OFFSET:
    target=previous['public'].get(str(entry['canonical_id']))
    if target:previous['public'][key]={**target,'id':int(key)}
  previous['updated_at']=now
  previous.setdefault('additional_imports',{})['muawiya4n']={'sources':len(posts),'review':'visual_and_descriptive_not_scholarly'}
  return previous
 settings=merge_setting(json.loads(local.execute("select value from research_catalogue_settings where key='media_catalogue'").fetchone()[0]))
 extra={'documents':plan['documents'],'bundles':plan['bundles'],'review_state':'edited_source_commentary_and_unverified_ocr'}
 def localinsert(table,record):
  cols=list(record);params=[json.dumps(record[k],ensure_ascii=False) if isinstance(record[k],(dict,list)) else record[k] for k in cols]
  local.execute('insert or ignore into '+table+' ('+','.join(cols)+') values('+','.join('?' for _ in cols)+')',params)
 with local:
  for table,records in rows.items():
   for record in records:localinsert(table,record)
  for key,value in [('media_catalogue',settings),('telegram_additions',extra)]:
   local.execute('insert into research_catalogue_settings(key,value) values(?,?) on conflict(key) do update set value=excluded.value',(key,json.dumps(value,ensure_ascii=False)))
  assert not local.execute('pragma foreign_key_check').fetchall()
 # Save bounded public fallback snapshots; never serialize provenance or editorial selection reasons.
 content=ROOT/'frontend/src/content'
 (content/'document-texts.json').write_text(json.dumps(plan['documents'],ensure_ascii=False))
 (content/'media-catalogue.json').write_text(json.dumps({k:{field:v for field,v in r.items() if field!='transcript'} for k,r in settings['public'].items()},ensure_ascii=False,indent=2))
 for filename,incoming in [('archive-index.json',plan['archive']),('local-sources.json',plan['sources'])]:
  path=content/filename;old=json.loads(path.read_text())
  if isinstance(old,list):
   ids={r['id']:r for r in old};ids.update({r['id']:r for r in incoming});merged=sorted(ids.values(),key=lambda r:r['id'])
  else:merged={**old,**incoming}
  path.write_text(json.dumps(merged,ensure_ascii=False,indent=2))
 if args.sync_cloud:
  assert urlparse(values['RESEARCH_POSTGRES_URL']).hostname==values['NEON_DATABASE_HOST']
  with psycopg.connect(values['RESEARCH_POSTGRES_URL'],connect_timeout=30) as cloud:
   before=cloud.execute('select id,decision from research.video_review_decisions order by id').fetchall()
   remote=cloud.execute("select value from research.research_catalogue_settings where key='media_catalogue' for update").fetchone()[0]
   (OUT/f'cloud-pre-publication-{stamp}.json').write_text(json.dumps({'catalogue':remote,'video_decisions':before},ensure_ascii=False,default=str))
   # Ensure the website reader cannot access private source captions/payloads.
   assert not cloud.execute("select has_table_privilege('othmani_website_reader','research.research_provenance','SELECT')").fetchone()[0]
   for table,records in rows.items():
    if table=='research_storage_locations':records=[r for r in records if r['provider']=='r2']
    if not records:continue
    cols=list(records[0]);statement=sql.SQL('insert into research.{} ({}) values ({}) on conflict do nothing').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,cols)),sql.SQL(',').join(sql.Placeholder() for _ in cols))
    with cloud.cursor() as cur:cur.executemany(statement,[[Json(r[k]) if isinstance(r[k],(dict,list)) else r[k] for k in cols] for r in records])
   merged=merge_setting(remote)
   for key,value in [('media_catalogue',merged),('telegram_additions',extra)]:
    cloud.execute('insert into research.research_catalogue_settings(key,value) values(%s,%s) on conflict(key) do update set value=excluded.value',(key,Json(value)))
   refresh_public_read_tables(cloud)
   cloud.execute((ROOT/'scripts/media-catalogue-view.sql').read_text())
   cloud.execute((ROOT/'scripts/telegram-additions-view.sql').read_text())
   assert before==cloud.execute('select id,decision from research.video_review_decisions order by id').fetchall()
   assert cloud.execute('select count(*) from research.research_media where legacy_id between 1000000 and 1999999').fetchone()[0]==1428
  with psycopg.connect(values['RESEARCH_READ_DATABASE_URL'],connect_timeout=30) as reader:
   assert reader.execute('select count(*) from research.website_media where id between 1000000 and 1999999').fetchone()[0]==1428
   count=reader.execute('select count(*) from research.website_document_texts').fetchone()[0]
  print('CLOUD_VERIFIED',count,'searchable_document_texts',flush=True)
 report={'source_posts_imported':len(posts),'attachment_occurrences_imported':len(attachments),'ocr_extracts':len(rows['research_extracts']),'content_objects_verified':len(rows['research_objects']),'cloud_synced':args.sync_cloud,'video_review_decisions_preserved':True}
 (OUT/'publication-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
if __name__=='__main__':main()
