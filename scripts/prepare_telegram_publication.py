"""Prepare reviewed source additions, Arabic thematic bundles and edited commentary.
Original discussion is private. Source descriptions never create scholarly verdicts.
"""
import collections,hashlib,json,os,re,sqlite3,sys,unicodedata
from pathlib import Path
from PIL import Image,ImageOps
from telegram_theme_definitions import DEFINITIONS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/research/imports/muawiya4n';ARCHIVE=ROOT.parent/'telegram-archive/muawiya4n'
OFFSET=1_000_000
PDF_THEMES={324:'thursday',1632:'prophet-prayer',1633:'muhammad-abibakr',1635:'wali-after',1636:'mutah',1637:'loyalty-faith',1729:'basra-treasury',1736:'du-khuwaysira',1745:'private-advice',1746:'battle-women',1747:'battle-women',1748:'battle-women',1751:'adult-nursing',1752:'amash',1755:'narrators',1756:'quran-recitation',1757:'mubahala',1760:'adult-nursing'}
PDF_TITLES={324:'رزية الخميس: محاضرة رامي عيسى',1632:'شواهد التشهد والصلاة على النبي',1633:'روايات موقف عائشة من مقتل محمد بن أبي بكر',1635:'طرق رواية «ولي كل مؤمن بعدي»',1636:'روايات المتعة وموقف ابن عباس وأصحابه',1637:'روايات «إن آل أبي طالب ليسوا بأوليائي»',1729:'بيت المال في البصرة: روايات سيطرة جيش الزبير',1736:'ذو الخويصرة: مجموعة روايات وشواهد',1745:'أبو سعيد الخدري ومروان: روايات النصيحة',1746:'رواية «أتتكم حمراء في كتيبة»: شواهد وطرق',1747:'روايات «وإن طائفتان من المؤمنين اقتتلوا»',1748:'روايات مشاركة النساء في الغزو',1751:'رضاع الكبير: مقارنة الروايات بالموطأ',1752:'الأعمش: شواهد من الروايات وكتب التراجم',1755:'الإمام مالك وإمامة دار الهجرة: نقول ومناقشة',1756:'رواية «توفي رسول الله وهي مما يقرأ في القرآن»',1757:'وفد نجران والمباهلة: مجموعة روايات',1760:'أقوال عمر وابن عمر في روايات رضاع الكبير'}
# Two more precise PDF subjects avoid assigning a file from its rhetoric alone.
EXTRA=[('quran-reconciliation','روايات الإصلاح بين طوائف المؤمنين','camel',[],['وإن طائفتان','طائفتان من المؤمنين'],'تجمع المادة الروايات المتعلقة بنزول آية الإصلاح بين طائفتين من المؤمنين. وتناقش تعليقات المصدر سياق الخبر وطرق نقله، مع الفصل بين واقعة النزول وتطبيق الآية على أحداث لاحقة.'),('malik','الإمام مالك ومكانته في مصادر التراجم','narrators',[],['إمام دار الهجرة','الإمام مالك','مالك بن أنس'],'تعرض تعليقات المصدر نقولًا تتعلق بمكانة الإمام مالك ووصفه بإمام دار الهجرة. تُجمع الشواهد للمقارنة بين نصوص التراجم وبين الاعتراضات التي يعرضها صاحب التعليق.')]
PDF_THEMES[1747]='quran-reconciliation';PDF_THEMES[1755]='malik'
def norm(s):
 s=unicodedata.normalize('NFKC',s);s=re.sub('[\u064b-\u065f\u0670\u0640]','',s)
 return re.sub(r'\s+',' ',s.translate(str.maketrans('أإآٱى','ااااي'))).lower()
def main():
 os.umask(0o077)
 c=sqlite3.connect(OUT/'filter.sqlite3');c.row_factory=sqlite3.Row
 old=sqlite3.connect(f'file:{ROOT}/data/research/research.sqlite3?mode=ro',uri=True);old.row_factory=sqlite3.Row
 existing=json.loads(old.execute("select value from research_catalogue_settings where key='media_catalogue'").fetchone()[0])['public']
 defs={slug:{'slug':slug,'title':title,'topic':topic,'cases':cases,'terms':terms,'explanation':summary,'items':[]} for slug,title,topic,cases,terms,summary in DEFINITIONS+EXTRA}
 posts={r['id']:dict(r) for r in c.execute('select * from posts')}
 payloads={mid:json.loads(r['payload']) for mid,r in posts.items()}
 album_files=collections.defaultdict(list)
 attachments={r['message_id']:dict(r) for r in c.execute('select * from attachments')}
 ocr={r['sha256']:dict(r) for r in c.execute('select * from import_text_cache')}
 pdfs=json.loads((OUT/'visual-review/pdf/manifest.json').read_text());pdf_by_sha={d['id'][4:]:d for d in pdfs}
 listings=json.loads((OUT/'consolidated-import.json').read_text())
 aliases={r['message_id']:r['canonical_key'] for r in c.execute('select * from consolidated_import_aliases')}
 canonical_ids={row['canonical_key']:int(row['canonical_key'].split(':')[1]) if row['canonical_key'].startswith('library:') else OFFSET+min(row['source_message_ids']) for row in listings}
 public={};metadata={};archive=[];sources={};texts={};editorial={};thumbnails={};upgrades={};pending=[]
 oldsha={r['sha256']:r['object_key'] for r in old.execute('select sha256,object_key from research_objects')}
 # Retain source bundles, but publish only edited commentary, not raw captions.
 for mid in attachments:
  gid=payloads[mid].get('grouped_id')
  if gid:album_files[gid].append(OFFSET+mid)
 for mid,a in attachments.items():
  p=posts[mid];gid=payloads[mid].get('grouped_id')
  members=album_files[gid] if gid else [OFFSET+mid]
  sources[str(OFFSET+mid)]={'id':OFFSET+mid,'date':json.loads(p['payload']).get('date') or '', 'files':sorted(members),'quotes':[]}
  path=ARCHIVE/a['path'];payload=json.loads(p['payload']);doc=(payload.get('media') or {}).get('document') or {}
  kind='pdf' if a['mime']=='application/pdf' else a['mime'].split('/')[0]
  name=a['original_name'] or path.name
  archive.append({'id':OFFSET+mid,'date':payload.get('date') or '2026-11-06T00:00:00+00:00','kind':kind,'mime':a['mime'],'path':'muawiya4n/'+a['path'],'size':path.stat().st_size,'name':name,'object_key':oldsha.get(a['sha256'],'imports/muawiya4n/originals/sha256/'+a['sha256']),'storage_state':'available'})
 for listing in listings:
  mids=listing['source_message_ids'];cid=canonical_ids[listing['canonical_key']]
  reps=[mid for mid in mids if attachments[mid]['sha256']==listing['preferred_object_id'][4:]]
  representative=min(reps or mids);a=attachments[representative];mime=a['mime'];sha=a['sha256']
  contexts=list(dict.fromkeys(e['text'] for e in listing['explanations'] if e['text'] and len(e['text'].strip())>=40))
  context='\n'.join(contexts);content=ocr.get(sha,{}).get('text','');filename=' '.join(attachments[mid]['original_name'] or '' for mid in mids)
  normalized_context=norm(context+' '+filename)
  scored=[]
  for slug,d in defs.items():
   hits=[term for term in d['terms'] if norm(term) in normalized_context]
   # Only strong source context links are public. OCR remains a separate searchable extract.
   score=sum(3 if len(norm(t))>=10 else 1 for t in hits)
   if slug=='narrators' and len(hits)<2:score=0
   if score:scored.append((score,slug,hits))
  scored.sort(reverse=True)
  themes=[s for _,s,_ in scored[:2]]
  pdfmid=next((mid for mid in mids if mid in PDF_THEMES),None)
  if mime=='application/pdf' and pdfmid is not None:themes=[PDF_THEMES[pdfmid]]
  is_upgrade=listing['action']=='upgrade_existing'
  is_old=listing['canonical_key'].startswith('library:')
  entry=dict(existing.get(str(cid),{})) if is_old else {}
  if is_old and entry.get('manual_video_hidden'):themes=[]
  if mime.startswith(('video/','audio/')):
   publish=False;reason='recording_requires_separate_review'
  elif is_old:
   publish=bool(entry.get('visible'));reason='existing_visibility_preserved'
  else:
   publish=bool(themes and (mime=='application/pdf' or (len(content.strip())>=100 and len(context.strip())>=60)))
   reason='source_context_and_readable_scan' if publish else 'needs_individual_identification_or_context'
  if is_old and not entry:
   publish=False;reason='existing_listing_not_public'
  if not publish:pending.append({'canonical_id':cid,'reason':reason,'mids':mids})
  primary=defs[themes[0]] if themes else None
  if not is_old:
   title=PDF_TITLES[pdfmid] if mime=='application/pdf' and pdfmid else ('شاهد مصوّر: '+primary['title']+f' — {cid-OFFSET}' if primary else 'مادة محفوظة بانتظار التوصيف')
   description=('مجموعة مقتطفات مصوّرة مع تظليل ونقول من مصادر متعددة حول '+primary['title']+'.' if mime=='application/pdf' and pdfmid!=324 and primary else 'صفحة مصوّرة مرتبطة بشرح المصدر حول '+primary['title']+'.' if primary else '')
   if pdfmid==324:description='كتيّب المحاضرة السابعة لرامي عيسى حول روايات رزية الخميس؛ تُنسب مناقشته واستنتاجاته إلى مؤلفه.'
   entry={'id':cid,'canonical_id':cid,'visible':publish,'title':title if publish else '', 'description':description if publish else '', 'work_title':'','author':'رامي عيسى' if pdfmid==324 else '', 'page_label':'','scope':'article' if pdfmid==324 else 'excerpt' if mime=='application/pdf' else 'page','topics':[],'cases':[],'tags':[],'chapters':[],'occurrences':[]}
  if themes and publish:
   entry['topics']=list(dict.fromkeys(entry.get('topics',[])+[defs[t]['topic'] for t in themes]))
   entry['cases']=list(dict.fromkeys(entry.get('cases',[])+[s for t in themes for s in defs[t]['cases']]))
   entry['tags']=list(dict.fromkeys(entry.get('tags',[])+[defs[t]['title'] for t in themes]))
   entry['bundles']=list(dict.fromkeys(entry.get('bundles',[])+themes))
   commentary=[]
   if context or mime=='application/pdf':
    for t in themes:
     commentary.append({'text':defs[t]['explanation'],'attribution':'صياغة تحريرية لوجه الاستدلال في تعليقات المصدر؛ ليست نقلًا حرفيًا من الوثيقة.','kind':'source_commentary_paraphrase'})
   entry['explanations']=commentary
   for t in themes:defs[t]['items'].append(cid)
  entry['occurrences']=sorted(set(entry.get('occurrences',[])+[OFFSET+mid for mid in mids]))
  if mime=='application/pdf' and sha in pdf_by_sha:entry['page_count']=len(pdf_by_sha[sha]['pages']);entry['library_section']='books' if pdfmid==324 else 'excerpts'
  if publish and content.strip():
   texts[str(cid)]={'text':content,'method':ocr[sha]['method'],'review_state':'unverified'};entry['has_document_text']=True
  if publish and (not is_old or is_upgrade) and OFFSET+representative!=cid:
   entry['preferred_media_id']=OFFSET+representative;entry['asset_size']=(ARCHIVE/a['path']).stat().st_size
  if is_upgrade:
   # Preserve original source identity and visibility. Only the viewer's preferred bytes change.
   if mime.startswith('image/') and publish:
    entry['preferred_media_id']=OFFSET+representative;entry['asset_size']=(ARCHIVE/a['path']).stat().st_size
    upgrades[str(cid)]={'preferred_media_id':OFFSET+representative,'sha256':sha}
  for mid in mids:
   public[str(OFFSET+mid)]={**entry,'id':OFFSET+mid}
  public[str(cid)]=entry
  metadata[str(cid)]=entry
  editorial[str(cid)]={'contexts':contexts,'theme_scores':scored,'selection_reason':reason,'source_message_ids':mids,'sha256':sha}
  if publish and (not is_old or is_upgrade):
   source=Path(pdf_by_sha[sha]['pages'][0]) if mime=='application/pdf' else ARCHIVE/a['path']
   if mime.startswith('image/') or mime=='application/pdf':
    target=ROOT/'frontend/public/thumbnails'/('import-'+sha+'.webp')
    if not target.exists():
     with Image.open(source) as im:
      im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((640,850));im.save(target,'WEBP',quality=86)
    url='/thumbnails/'+target.name
    for mid in mids:thumbnails[str(OFFSET+mid)]=url
    thumbnails[str(cid)]=url
 bundles=[]
 for d in defs.values():
  d['items']=sorted(set(d['items']),key=lambda id:(metadata.get(str(id),{}).get('scope')=='page',id))
  if d['items']:bundles.append({k:d[k] for k in ['slug','title','topic','cases','explanation','items']})
 result={'public':public,'archive':archive,'sources':sources,'documents':texts,'bundles':bundles,'editorial':editorial,'upgrades':upgrades}
 (OUT/'publication-plan.json').write_text(json.dumps(result,ensure_ascii=False))
 # Reviewed projections contain only edited Arabic copy, never raw captions or source payloads.
 safe={'bundles':bundles,'explanations':{k:v.get('explanations',[]) for k,v in metadata.items() if v.get('visible')},'upgrades':upgrades}
 (ROOT/'frontend/src/content/research-bundles.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2))
 thumbfile=ROOT/'frontend/src/content/thumbnails.json';oldthumb=json.loads(thumbfile.read_text());oldthumb.update(thumbnails);thumbfile.write_text(json.dumps(oldthumb,ensure_ascii=False,indent=2))
 visible_new=[v for k,v in metadata.items() if v.get('visible') and int(k)>=OFFSET]
 report={'new_public_items':len(visible_new),'new_pdfs':sum(v['scope'] in ['excerpt','article'] for v in visible_new),'new_images':sum(v['scope']=='page' for v in visible_new),'public_theme_bundles':len(bundles),'upgrades':len(upgrades),'pending_private':len([p for p in pending if p['canonical_id']>=OFFSET]),'edited_document_explanations':sum(bool(v.get('explanations')) for v in metadata.values() if v.get('visible')),'ocr_cached':len(ocr),'source_text_posts_preserved':sum(bool(r['text']) for r in posts.values()),'pending':pending}
 (OUT/'publication-preparation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!='pending'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
