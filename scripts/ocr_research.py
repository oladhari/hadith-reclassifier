#!/usr/bin/env python3
"""Resumable local Arabic OCR. Raw output remains unverified, never a hadith verdict."""
import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=ROOT/'data/research/research.sqlite3')
    parser.add_argument('--archive', type=Path, default=ROOT.parent/'telegram-archive/kkee9938')
    parser.add_argument('--ids', nargs='*', type=int)
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    version = subprocess.check_output(['tesseract', '--version'], text=True).splitlines()[0]
    db = sqlite3.connect(args.database)
    db.execute('PRAGMA foreign_keys=ON')
    db.row_factory = sqlite3.Row
    rows = db.execute('''SELECT m.*,o.sha256 FROM research_media m
        JOIN research_objects o ON m.object_id=o.id WHERE m.kind='image'
        AND NOT EXISTS(SELECT 1 FROM research_processing_jobs j WHERE j.object_id=m.object_id
        AND j.kind='ocr' AND j.status='completed') ORDER BY m.legacy_id''').fetchall()
    selected = []; seen = set()
    for row in rows:
        if args.ids and row['legacy_id'] not in args.ids: continue
        if row['object_id'] in seen: continue
        seen.add(row['object_id']); selected.append(dict(row))
    selected = selected[:args.limit]
    def recognize(row):
        path = (args.archive / row['archive_relative_path']).resolve()
        if not path.is_relative_to(args.archive.resolve()): raise ValueError('Invalid media path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']: raise ValueError('Input checksum mismatch')
        result = subprocess.run(['tesseract',str(path),'stdout','-l','ara+eng','--psm','3'], capture_output=True,text=True,timeout=180,env={**os.environ,"OMP_THREAD_LIMIT":"1"})
        if result.returncode: raise RuntimeError(result.stderr[-1000:])
        return row,result.stdout.strip()
    if not selected:
        print(json.dumps({"processed": 0, "message": "No pending images in selection"}))
        return
    # A backup precedes all catalogue mutations.
    backup = args.database.parent/'backups'/f'pre-ocr-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.sqlite3'
    backup.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(backup) as dest: db.backup(dest)
    backup.chmod(0o600)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row, text in pool.map(recognize, selected):
            now=datetime.now(timezone.utc).isoformat(); extract_id=str(uuid.uuid4())
            with db:
                if text:
                    db.execute('''INSERT OR IGNORE INTO research_extracts
                     (id,source_id,media_id,kind,text,text_sha256,ordinal,language,review_state,method,created_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)''',(extract_id,row['source_id'],row['id'],'ocr_text',text,hashlib.sha256(text.encode()).hexdigest(),0,'ar','unverified',version,now))
                    extract_id=db.execute('SELECT id FROM research_extracts WHERE source_id=? AND kind=? AND text_sha256=?',(row['source_id'],'ocr_text',hashlib.sha256(text.encode()).hexdigest())).fetchone()[0]
                db.execute('''INSERT INTO research_processing_jobs
                 (id,object_id,kind,status,input_sha256,parameters,result_extract_ids,error,created_at)
                 VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(object_id,kind,input_sha256) DO UPDATE SET
                 status=excluded.status,parameters=excluded.parameters,result_extract_ids=excluded.result_extract_ids,error=NULL''',
                 (str(uuid.uuid4()),row['object_id'],'ocr','completed',row['sha256'],json.dumps({'engine':version,'language':'ara+eng','psm':3}),json.dumps([extract_id] if text else []),None,now))
            print(json.dumps({'id':row['legacy_id'],'characters':len(text),'review':'unverified'}),flush=True)
    print(json.dumps({'processed':len(selected),'backup':str(backup)}))
if __name__=='__main__': main()
