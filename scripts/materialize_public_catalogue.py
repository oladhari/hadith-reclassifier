"""Refresh small relational read models from reviewed settings in one transaction.
Avoid expanding multi-megabyte catalogue JSON during every public request.
Base tables have RLS and no website-reader grant; existing views enforce visibility.
"""
from psycopg import sql
from psycopg.types.json import Json

def refresh_public_read_tables(conn):
    settings = conn.execute("SELECT value FROM research.research_catalogue_settings WHERE key='media_catalogue'").fetchone()[0]
    extra = conn.execute("SELECT value FROM research.research_catalogue_settings WHERE key='telegram_additions'").fetchone()
    documents = extra[0].get('documents', {}) if extra else {}
    public = settings['public']
    tables = {
        'research_public_catalogue_entries': ('metadata', [(str(key), {k:v for k,v in row.items() if k!='transcript'}) for key,row in public.items()]),
        'research_public_transcript_entries': ('text', [(str(key), row['transcript']) for key,row in public.items() if row.get('visible') and str(key)==str(row['canonical_id']) and row.get('transcript')]),
        'research_public_document_entries': ('text', [(str(key), row['text']) for key,row in documents.items()]),
    }
    counts = {}
    for name, (column, rows) in tables.items():
        fieldtype = sql.SQL('jsonb') if column=='metadata' else sql.SQL('text')
        conn.execute(sql.SQL('CREATE TABLE IF NOT EXISTS research.{} (id text PRIMARY KEY, {} {} NOT NULL)').format(sql.Identifier(name),sql.Identifier(column),fieldtype))
        conn.execute(sql.SQL('ALTER TABLE research.{} ENABLE ROW LEVEL SECURITY').format(sql.Identifier(name)))
        conn.execute(sql.SQL('REVOKE ALL ON research.{} FROM PUBLIC,othmani_website_reader').format(sql.Identifier(name)))
        query=sql.SQL('INSERT INTO research.{} (id,{}) VALUES (%s,%s) ON CONFLICT(id) DO UPDATE SET {}=excluded.{}').format(sql.Identifier(name),sql.Identifier(column),sql.Identifier(column),sql.Identifier(column))
        with conn.cursor() as cursor:cursor.executemany(query,[(key,Json(value) if column=='metadata' else value) for key,value in rows])
        conn.execute(sql.SQL('DELETE FROM research.{} WHERE NOT (id=ANY(%s))').format(sql.Identifier(name)),([r[0] for r in rows],))
        count=conn.execute(sql.SQL('SELECT count(*) FROM research.{}').format(sql.Identifier(name))).fetchone()[0]
        assert count==len(rows)
        counts[name]=count
    return counts
