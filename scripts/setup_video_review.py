#!/usr/bin/env python3
"""Install limited manual video review permissions; preserve decisions on reruns."""
import json,os,secrets,sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,quote
import psycopg
from psycopg import sql
from enrich_media import config,ROOT
os.umask(0o077)
values=config(); destination=ROOT/'data/research/video-review-secrets.json'
if destination.exists(): credentials=json.loads(destination.read_text())
else:
 password=secrets.token_urlsafe(36);u=urlsplit(values['RESEARCH_POSTGRES_URL'])
 credentials={'VIDEO_REVIEW_DATABASE_URL':urlunsplit((u.scheme,'othmani_video_reviewer:'+quote(password,safe='')+'@'+u.netloc.split('@',1)[1],u.path,u.query,u.fragment)), 'VIDEO_REVIEW_ACCESS_CODE':secrets.token_urlsafe(24)}
 destination.write_text(json.dumps(credentials));destination.chmod(0o600)
with psycopg.connect(values['RESEARCH_POSTGRES_URL'],connect_timeout=30) as conn:
 if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='othmani_video_reviewer'").fetchone():
  from urllib.parse import unquote
  password=unquote(urlsplit(credentials['VIDEO_REVIEW_DATABASE_URL']).password)
  conn.execute(sql.SQL('CREATE ROLE othmani_video_reviewer LOGIN PASSWORD {}').format(sql.Literal(password)))
 conn.execute((ROOT/'scripts/video-review-schema.sql').read_text())
 conn.execute((ROOT/'scripts/media-catalogue-view.sql').read_text())
 print('Private review catalogue initialized:',conn.execute('SELECT count(*) FROM research.video_review_items').fetchone()[0])
with psycopg.connect(credentials['VIDEO_REVIEW_DATABASE_URL'],connect_timeout=30) as reviewer:
 assert reviewer.execute('SELECT count(*) FROM research.video_review_items').fetchone()[0]>0
try:
 with psycopg.connect(credentials['VIDEO_REVIEW_DATABASE_URL']) as reviewer: reviewer.execute('SELECT * FROM research.research_provenance LIMIT 1')
 raise RuntimeError('Reviewer unexpectedly has raw archive access')
except psycopg.errors.InsufficientPrivilege: pass
with psycopg.connect(values['RESEARCH_READ_DATABASE_URL']) as reader:
 assert reader.execute('SELECT count(*) FROM research.website_catalogue').fetchone()[0]>0
try:
 with psycopg.connect(values['RESEARCH_READ_DATABASE_URL']) as reader: reader.execute('SELECT * FROM research.video_review_items LIMIT 1')
 raise RuntimeError('Public reader unexpectedly has private review access')
except psycopg.errors.InsufficientPrivilege: pass
path=ROOT/'frontend/.env.local'
lines=path.read_text().splitlines() if path.exists() else []
lines=[line for line in lines if not any(line.startswith(k+'=') for k in credentials)]
path.write_text('\n'.join(lines+[k+'='+v for k,v in credentials.items()])+'\n');path.chmod(0o600)
out=ROOT/'output/video-review-access.txt';out.parent.mkdir(exist_ok=True)
out.write_text('Private video review\nhttps://othmani-encyclopedia.vercel.app/review/videos\n\nAccess code: '+credentials['VIDEO_REVIEW_ACCESS_CODE']+'\n\nKeep this code private. Hiding preserves the database and original file.\n');out.chmod(0o600)
print('Limited reviewer permissions verified; private access code saved locally.')
