#!/usr/bin/env python3
"""Publish validated machine drafts through a restricted read-only view.

No changes to assessments, filter completion counts, book entries or originals.
"""
import hashlib
import json
import sqlite3
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb
from analyse_hadith_batch import DIRECTORY, PROFILE, ROOT, validate
from publish_research_database import configuration


def main():
    manifest=json.loads((DIRECTORY/'input-manifest.json').read_text())
    profile=json.loads(PROFILE.read_text())
    assert hashlib.sha256(PROFILE.read_bytes()).hexdigest()==manifest['profile_sha256']
    records={str(r['source_number']):r for r in manifest['records']}
    config=configuration(ROOT/'.env')
    drafts=[]
    with sqlite3.connect(ROOT/'data/research/research.sqlite3') as local:
        for number,record in records.items():
            path=DIRECTORY/f'{number}.json'
            if not path.exists(): continue
            data=json.loads(path.read_text());validate(data['report'],record)
            assert data['text_sha256']==record['text_sha256'] and data['profile_sha256']==manifest['profile_sha256']
            text=local.execute("SELECT text FROM research_hadith_texts WHERE hadith_id=? AND language='ar'",(record['id'],)).fetchone()[0]
            assert hashlib.sha256(text.encode()).hexdigest()==data['text_sha256']
            report=data['report']
            # Public report contains only validated source quotes and editorial
            # drafts, never credentials, raw API traces or private provenance.
            for layer,definition in zip(report['layers'],profile['layers']):
                layer['title']=definition['title']
            public={'summary':report['summary'],'report_type':report['report_type'],'themes':report['themes'],'layers':report['layers']}
            drafts.append((record,data,public))
    with psycopg.connect(config['RESEARCH_POSTGRES_URL']) as conn:
        # Avoid DDL lock upgrades during normal publication while readers are active.
        if conn.execute("SELECT to_regclass('research.website_ai_hadith_drafts')").fetchone()[0] is None:
            conn.execute('''CREATE TABLE IF NOT EXISTS research.research_ai_hadith_drafts (
                hadith_id varchar(36) PRIMARY KEY REFERENCES research.research_hadiths(id),
                collection varchar(80) NOT NULL, source_number varchar(80) NOT NULL,
                model text NOT NULL, profile_key text NOT NULL, profile_version integer NOT NULL,
                profile_sha256 varchar(64) NOT NULL, text_sha256 varchar(64) NOT NULL,
                created_at timestamptz NOT NULL, report jsonb NOT NULL,
                UNIQUE(collection,source_number))''')
            conn.execute('ALTER TABLE research.research_ai_hadith_drafts ENABLE ROW LEVEL SECURITY')
            conn.execute('REVOKE ALL ON research.research_ai_hadith_drafts FROM PUBLIC, othmani_website_reader')
            conn.execute('''CREATE OR REPLACE VIEW research.website_ai_hadith_drafts WITH (security_barrier=true) AS
                SELECT d.collection,d.source_number,d.model,d.profile_key,d.profile_version,d.created_at,d.report
                FROM research.research_ai_hadith_drafts d
                JOIN research.research_hadith_texts t ON t.hadith_id=d.hadith_id AND t.language='ar'
                WHERE encode(sha256(convert_to(t.text,'UTF8')),'hex')=d.text_sha256''')
            conn.execute('GRANT SELECT ON research.website_ai_hadith_drafts TO othmani_website_reader')
            conn.commit()
        live=dict(conn.execute("SELECT hadith_id,text FROM research.research_hadith_texts WHERE hadith_id=ANY(%s) AND language='ar'",([record['id'] for record,_,_ in drafts],)).fetchall())
        for record,data,_ in drafts:
            assert record['id'] in live and hashlib.sha256(live[record['id']].encode()).hexdigest()==data['text_sha256']
        with conn.cursor() as cursor:
            cursor.executemany('''INSERT INTO research.research_ai_hadith_drafts
                (hadith_id,collection,source_number,model,profile_key,profile_version,profile_sha256,text_sha256,created_at,report)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(hadith_id) DO UPDATE SET model=EXCLUDED.model,
                profile_key=EXCLUDED.profile_key,profile_version=EXCLUDED.profile_version,
                profile_sha256=EXCLUDED.profile_sha256,text_sha256=EXCLUDED.text_sha256,
                created_at=EXCLUDED.created_at,report=EXCLUDED.report''',
                [(record['id'],'bukhari',str(record['source_number']),data['model'],data['profile_key'],data['profile_version'],data['profile_sha256'],data['text_sha256'],data['created_at'],Jsonb(report)) for record,data,report in drafts])
        count=conn.execute('SELECT count(*) FROM research.website_ai_hadith_drafts').fetchone()[0]
    print(json.dumps({'published':len(drafts),'visible':count,'scholarly_verdicts_created':0}))


if __name__=='__main__':main()
