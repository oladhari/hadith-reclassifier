"""Private, reversible comparison of a Telegram import with the research catalogue.
No public projection, scholarly decisions, original deletion or paid processing.
"""
import collections, concurrent.futures, hashlib, json, os, re, sqlite3, subprocess, unicodedata
from pathlib import Path
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT.parent/'telegram-archive/muawiya4n'
OLD=ROOT.parent/'telegram-archive/kkee9938'
OUT=ROOT/'data/research/imports/muawiya4n'

def normalize(s):
    s=unicodedata.normalize('NFKC',s)
    s=re.sub('[\u064b-\u065f\u0670\u0640]','',s)
    return re.sub(r'\W+','',s).lower()

def inspect(item):
    key,path,mime=item
    result={'id':key,'mime':mime}
    try:
        if mime=='application/pdf':
            info=subprocess.run(['pdfinfo',str(path)],capture_output=True,text=True,timeout=45)
            text=subprocess.run(['pdftotext','-layout',str(path),'-'],capture_output=True,text=True,timeout=60)
            result.update(pdf_info=info.stdout,text=text.stdout,error=(info.stderr+text.stderr)[:2000])
            match=re.search(r'^Pages:\s*(\d+)',info.stdout,re.M)
            result['pages']=int(match[1]) if match else None
            norm=normalize(text.stdout)
            result['text_hash']=hashlib.sha256(norm.encode()).hexdigest() if len(norm)>=200 else None
            result['characters']=len(norm)
        elif mime.startswith('image/'):
            with Image.open(path) as source:
                image=ImageOps.exif_transpose(source)
                result.update(width=image.width,height=image.height)
                # Candidate generation only: a small hash never establishes page identity.
                small=image.convert('L').resize((9,8))
                px=list(small.get_flattened_data() if hasattr(small,'get_flattened_data') else small.getdata()); bits=[px[y*9+x]>px[y*9+x+1] for y in range(8) for x in range(8)]
                result['dhash']=sum(int(b)<<i for i,b in enumerate(bits))
    except Exception as e: result['error']=type(e).__name__+': '+str(e)
    return result

def main():
    os.umask(0o077); OUT.mkdir(parents=True,exist_ok=True)
    archive=sqlite3.connect(f'file:{ARCHIVE}/archive.sqlite3?mode=ro',uri=True); archive.row_factory=sqlite3.Row
    old=sqlite3.connect(f'file:{ROOT}/data/research/research.sqlite3?mode=ro',uri=True); old.row_factory=sqlite3.Row
    db=sqlite3.connect(OUT/'filter.sqlite3')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY,text TEXT,permalink TEXT,payload TEXT);
    CREATE TABLE IF NOT EXISTS attachments(message_id INTEGER PRIMARY KEY,sha256 TEXT,path TEXT,mime TEXT,original_name TEXT,r2_key TEXT);
    CREATE TABLE IF NOT EXISTS explanation_links(text_message_id INTEGER,attachment_message_id INTEGER,relation TEXT,review_state TEXT,PRIMARY KEY(text_message_id,attachment_message_id,relation));
    CREATE TABLE IF NOT EXISTS exact_matches(message_id INTEGER,existing_media_id TEXT,existing_source_id TEXT,PRIMARY KEY(message_id,existing_media_id));
    CREATE TABLE IF NOT EXISTS inspections(id TEXT PRIMARY KEY,path TEXT,payload TEXT);
    CREATE TABLE IF NOT EXISTS candidates(import_id TEXT,other_id TEXT,reason TEXT,metrics TEXT,review_state TEXT,PRIMARY KEY(import_id,other_id,reason));
    ''')
    posts={r['id']:dict(r) for r in archive.execute('select * from messages')}
    payload={mid:json.loads(r['raw_json']) for mid,r in posts.items()}
    attachments={}; groups=collections.defaultdict(list)
    existing=list(old.execute('''select m.id,m.source_id,m.legacy_id,m.archive_relative_path,o.sha256,o.mime_type from research_media m join research_objects o on o.id=m.object_id'''))
    bysha=collections.defaultdict(list)
    for r in existing: bysha[r['sha256']].append(r)
    for mid,r in posts.items():
        d=payload[mid]; db.execute('insert or replace into posts values(?,?,?,?)',(mid,r['text'],r['permalink'],r['raw_json']))
        if d.get('grouped_id'): groups[str(d['grouped_id'])].append(mid)
        if r['media_status']!='downloaded':continue
        doc=(d.get('media') or {}).get('document') or {};mime=doc.get('mime_type') or ('image/jpeg' if (d.get('media') or {}).get('photo') else 'application/octet-stream')
        name=next((a['file_name'] for a in doc.get('attributes',[]) if a.get('file_name')),None)
        loc=archive.execute('select object_key from r2_imports where message_id=?',(mid,)).fetchone()
        db.execute('insert or replace into attachments values(?,?,?,?,?,?)',(mid,r['sha256'],r['media_path'],mime,name,loc[0] if loc else None))
        attachments[mid]=(r,mime)
        for e in bysha[r['sha256']]:db.execute('insert or ignore into exact_matches values(?,?,?)',(mid,e['id'],e['source_id']))
    def link(textid,targets,relation,state='source_link_unverified'):
        if not (posts.get(textid,{}).get('text') or '').strip():return
        for target in targets:
            if target in attachments:db.execute('insert or ignore into explanation_links values(?,?,?,?)',(textid,target,relation,state))
    for mid,d in payload.items():
        link(mid,[mid],'own_caption')
        if d.get('grouped_id'):link(mid,groups[str(d['grouped_id'])],'same_album_caption')
        reply=d.get('reply_to') or {};target=reply.get('reply_to_msg_id')
        peer=reply.get('reply_to_peer_id')
        if target in posts and (not peer or peer.get('channel_id')==2581749916):
            targets=[target]+groups.get(str(payload[target].get('grouped_id')),[])
            link(mid,targets,'explicit_reply')
            link(target,[mid],'attachment_replies_to_text')
    db.commit()
    items={}
    for mid,(r,mime) in attachments.items():items['new:'+r['sha256']]=('new:'+r['sha256'],ARCHIVE/r['media_path'],mime)
    for e in existing:
        if e['archive_relative_path']:items['old:'+e['sha256']]=('old:'+e['sha256'],OLD/e['archive_relative_path'],e['mime_type'])
    todo=[v for k,v in items.items() if not db.execute('select 1 from inspections where id=?',(k,)).fetchone() and (v[2]=='application/pdf' or v[2].startswith('image/'))]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(inspect,todo):
            db.execute('insert or replace into inspections values(?,?,?)',(result['id'],str(items[result['id']][1]),json.dumps(result,ensure_ascii=False)));db.commit()
    inspections={r[0]:json.loads(r[1]) for r in db.execute('select id,payload from inspections')}
    oldins=[(k,v) for k,v in inspections.items() if k.startswith('old:')]
    for key,a in inspections.items():
        if not key.startswith('new:'):continue
        others=oldins+[(k,v) for k,v in inspections.items() if k.startswith('new:') and k<key]
        for other,b in others:
            if key[4:]==other[4:]:continue
            reason=None;metrics={}
            if a.get('text_hash') and a.get('text_hash')==b.get('text_hash'):
                reason='same_normalized_pdf_text';metrics={'pages':[a.get('pages'),b.get('pages')],'characters':[a.get('characters'),b.get('characters')],'caution':'Compare page images, completeness and edition before selection'}
            elif 'dhash' in a and 'dhash' in b:
                distance=(a['dhash']^b['dhash']).bit_count()
                if distance<=3:
                    reason='similar_image_candidate';metrics={'hash_distance':distance,'dimensions':[[a['width'],a['height']],[b['width'],b['height']]],'caution':'May be distinct pages with the same layout; visual review required'}
            if reason:db.execute('insert into candidates values(?,?,?,?,?) on conflict(import_id,other_id,reason) do update set metrics=excluded.metrics',(key,other,reason,json.dumps(metrics),'needs_visual_review'))
    db.executescript("""
    CREATE VIEW IF NOT EXISTS canonical_files AS
    SELECT a.sha256,coalesce(min(e.existing_media_id),'muawiya4n:'||min(a.message_id)) AS canonical_id,
    count(distinct a.message_id) AS import_occurrences
    FROM attachments a LEFT JOIN exact_matches e ON e.message_id=a.message_id GROUP BY a.sha256;
    CREATE VIEW IF NOT EXISTS canonical_explanations AS
    SELECT DISTINCT c.canonical_id,c.sha256,p.id AS text_message_id,p.text,p.permalink,l.relation,l.review_state
    FROM explanation_links l JOIN posts p ON p.id=l.text_message_id
    JOIN attachments a ON a.message_id=l.attachment_message_id JOIN canonical_files c ON c.sha256=a.sha256;
    """)
    db.commit()
    pdfrows=[{'id':k,**v} for k,v in inspections.items() if k.startswith('new:') and v['mime']=='application/pdf']
    report={'posts':len(posts),'text_posts':sum(bool((r['text'] or '').strip()) for r in posts.values()),'attachment_occurrences':len(attachments),'unique_import_files':len({r['sha256'] for r,m in attachments.values()}),'matches_existing_occurrences':db.execute('select count(distinct message_id) from exact_matches').fetchone()[0],'exact_existing_unique_hashes':len({posts[r[0]]['sha256'] for r in db.execute('select distinct message_id from exact_matches')}),'explanation_links_by_type':dict(db.execute('select relation,count(*) from explanation_links group by relation')),'candidate_types':dict(db.execute('select reason,count(*) from candidates group by reason')),'pdfs_requiring_ocr':sum(v.get('characters',0)<200 for v in pdfrows),'inspection_errors':sum(bool(v.get('error')) for v in inspections.values()),'discussion_comments':'No linked discussion group or comment-enabled posts found at access check','status':'private_first_pass_complete; alternative_versions_need_visual_review','originals_deleted':0,'public_catalogue_changed':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (OUT/'pdf-inspections.json').write_text(json.dumps(pdfrows,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
