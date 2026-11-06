#!/usr/bin/env python3
"""Add verified R2 JSON supplements to local/Neon searchable corpus, without verdicts."""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import UTC,datetime
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.types.json import Json
from sqlalchemy import select

from publish_research_database import configuration, fingerprint
from sync_missing_hadith_books import CACHE, ROOT
sys.path.insert(0,str(ROOT/'backend'))
from app.research import schema as s
from app.research.catalogue import uid,normalize,open_database
from app.research.corpus_progress import project_progress


def build():
    index=json.loads((CACHE/'r2-books-index.json').read_text())
    rows={table:[] for table in [s.collections,s.corpus_files,s.hadiths,s.hadith_texts]}
    timestamp=datetime.now(UTC).isoformat()
    public={}
    for book in index['books']:
        raw=(CACHE/book['filename']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=book['sha256']:raise ValueError('Source checksum mismatch')
        data=json.loads(raw);slug=book['slug'];cid=uid('collection',slug)
        rows[s.collections].append(dict(id=cid,slug=slug,title=book['title'],created_at=timestamp))
        source={k:book[k] for k in ['repository','revision','source_url','r2_key','sha256','coverage','coverage_note','numbering_note']}
        counters=Counter();arabic=[]
        for i,h in enumerate(data['hadiths']):
            number=str(h['idInBook']);hid=uid('hadith',slug,number);counters[h['chapterId']]+=1
            reference={'book':h['chapterId'],'hadith':counters[h['chapterId']]}
            rows[s.hadiths].append(dict(id=hid,collection_id=cid,source_number=number,source_ordinal=i,book_number=str(h['chapterId']),book_hadith_number=str(reference['hadith']),review_state='unreviewed',created_at=timestamp))
            for language in ['ar','en']:
                value=h['arabic'] if language=='ar' else '\n'.join(filter(None,[h['english'].get('narrator'),h['english'].get('text')]))
                # Repair literal upstream Unicode escape artifacts; raw original
                # bytes remain immutable in R2 and are checksum-referenced here.
                text=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m[1],16)),value)
                original={'hadithnumber':int(number),'text':text,'reference':reference,'upstream_id':h['id'],'dataset_source':source}
                rows[s.hadith_texts].append(dict(id=uid('hadith_text',slug,'ara' if language=='ar' else 'eng',i),hadith_id=hid,collection_id=cid,language=language,source_ordinal=i,source_number=number,text=text,normalized_text=normalize(text),original_data=original,source_file=book['filename'],source_file_sha256=book['sha256'],created_at=timestamp))
                if language=='ar':arabic.append(original)
        for language in ['ar','en']:
            rows[s.corpus_files].append(dict(id=uid('corpus_file',slug,language,book['sha256']),collection_id=cid,language=language,filename=book['filename'],sha256=book['sha256'],metadata={**data['metadata'],'dataset_source':source},record_count=len(data['hadiths']),created_at=timestamp))
        public[slug]={'metadata':{'name':book['title'],'dataset_source':source},'hadiths':arabic}
    return index,rows,public


def comparable(rows):return [{k:v for k,v in row.items() if k!='created_at'} for row in rows]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--sync-cloud',action='store_true');args=parser.parse_args()
    index,rows,public=build();ids=[row['id'] for row in rows[s.collections]]
    stamp=datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ');backup=ROOT/f'data/research/backups/pre-supplement-{stamp}.sqlite3';backup.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(ROOT/'data/research/research.sqlite3') as source,sqlite3.connect(backup) as target:source.backup(target)
    backup.chmod(0o600)
    if args.sync_cloud:
        config=configuration(ROOT/'.env')
        with psycopg.connect(config['RESEARCH_POSTGRES_URL']) as conn:
            baseline=conn.execute('SELECT slug,count(h.id) FROM research.research_collections c LEFT JOIN research.research_hadiths h ON h.collection_id=c.id WHERE c.id<>ALL(%s) GROUP BY slug ORDER BY slug',(ids,)).fetchall()
            for table,values in rows.items():
                columns=list(values[0]);temp='supplement_'+table.name
                conn.execute(sql.SQL('CREATE TEMP TABLE {} (LIKE research.{} INCLUDING DEFAULTS) ON COMMIT DROP').format(sql.Identifier(temp),sql.Identifier(table.name)))
                with conn.cursor().copy(sql.SQL('COPY {} ({}) FROM STDIN').format(sql.Identifier(temp),sql.SQL(',').join(map(sql.Identifier,columns)))) as copy:
                    for row in values:copy.write_row([Json(row[k]) if k in {'original_data','metadata'} else row[k] for k in columns])
                conn.execute(sql.SQL('INSERT INTO research.{} ({}) SELECT {} FROM {} ON CONFLICT(id) DO NOTHING').format(sql.Identifier(table.name),sql.SQL(',').join(map(sql.Identifier,columns)),sql.SQL(',').join(map(sql.Identifier,columns)),sql.Identifier(temp)))
                condition='id=ANY(%s)' if table==s.collections else 'collection_id=ANY(%s)'
                with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                    cursor.execute(sql.SQL('SELECT * FROM research.{} WHERE '+condition).format(sql.Identifier(table.name)),(ids,));actual=cursor.fetchall()
                if fingerprint(comparable(actual))!=fingerprint(comparable(values)):raise ValueError('Remote verification failed: '+table.name)
                print('Cloud verified:',table.name,len(values),flush=True)
            after=conn.execute('SELECT slug,count(h.id) FROM research.research_collections c LEFT JOIN research.research_hadiths h ON h.collection_id=c.id WHERE c.id<>ALL(%s) GROUP BY slug ORDER BY slug',(ids,)).fetchall()
            if baseline!=after:raise ValueError('Existing corpus changed')
    engine=open_database(ROOT/'data/research/research.sqlite3')
    with engine.begin() as conn:
        for table,values in rows.items():
            known=set(conn.execute(select(table.c.id)).scalars());new=[r for r in values if r['id'] not in known]
            for offset in range(0,len(new),500):conn.execute(table.insert(),new[offset:offset+500])
            condition=table.c.id.in_(ids) if table==s.collections else table.c.collection_id.in_(ids)
            actual=list(conn.execute(select(table).where(condition)).mappings())
            if fingerprint(comparable(actual))!=fingerprint(comparable(values)):raise ValueError('Local verification failed: '+table.name)
    for slug,data in public.items():
        (ROOT/f'data/hadiths/ara-{slug}.json').write_text(json.dumps(data,ensure_ascii=False))
        english=[row['original_data'] for row in rows[s.hadith_texts] if row['collection_id']==uid('collection',slug) and row['language']=='en']
        (ROOT/f'data/hadiths/eng-{slug}.json').write_text(json.dumps({'metadata':data['metadata'],'hadiths':english},ensure_ascii=False))
    with engine.connect() as conn:progress=project_progress(conn)
    (ROOT/'frontend/src/content/corpus-progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'added_collections':len(ids),'hadith_records':index['records'],'corpus_total':progress['counts']['total'],'cloud_synced':args.sync_cloud,'scholarly_verdicts_created':0}))


if __name__=='__main__':main()
