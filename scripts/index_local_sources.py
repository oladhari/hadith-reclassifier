"""Build a public local-source index without exporting collection-chat links or credentials.
Albums are linked only by actual grouped_id; proximity alone never implies association.
Raw discussion text stays in the original private/local SQLite archive.
"""
import json,re,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
c=sqlite3.connect(f'file:{ROOT.parent / "telegram-archive/kkee9938/archive.sqlite3"}?mode=ro',uri=True)
rows=c.execute('SELECT id,date,text,raw_json,media_path FROM messages ORDER BY id').fetchall()
albums={}
for mid,date,text,raw,media in rows:
 g=json.loads(raw).get('grouped_id')
 if g and media:albums.setdefault(str(g),[]).append(mid)
# Only extracted quote fragments are made available as unverified research leads.
# Full source pages/media remain unmodified. Discussion and invective are not publications.
blocked=re.compile(r'كلاب|كهنة|الكلب|الأنجاس|الانجاس|مجوس|خبيث|الخبيث|المزبلة|مزابل|سكرجي|الخمرجي|انبح|دجل|الخنزير|يهودي|اليهودي|المجرم|المجرمين|الأنذال|لعنة|لعنهم|النذل')
out={}
for mid,date,text,raw,media in rows:
 text=text or '';g=json.loads(raw).get('grouped_id');files=list(albums.get(str(g),[])) if g else ([mid] if media else [])
 quotes=[]
 for match in re.finditer(r'«([^«»]{25,1200})»|"([^"\n]{25,1200})"|\(([^()]{25,1200})\)',text):
  q=next(v for v in match.groups() if v is not None).strip()
  if not blocked.search(q) and not re.search(r'https?://|t\.me',q) and q not in quotes:quotes.append(q)
 out[str(mid)]={'id':mid,'date':date,'files':files,'quotes':quotes[:12]}
p=ROOT/'frontend/src/content/local-sources.json';p.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
print('Indexed source records:',len(out),'albums:',len(albums),'records with attached originals:',sum(bool(v['files']) for v in out.values()),'records with quote fragments:',sum(bool(v['quotes']) for v in out.values()))
for mid in [195,196,1315,2380,219]:print(mid,out[str(mid)]['files'])
