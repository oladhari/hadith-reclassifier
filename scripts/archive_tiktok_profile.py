"""Resume a public TikTok profile archive into the project's R2, without Neon/AI.

Discover with yt-dlp --flat-playlist --dump-single-json first. This script accepts
that saved inventory, verifies content hashes and stores each unique video once.
It never publishes unreviewed entries to the website or deletes original files.
"""
import argparse
import concurrent.futures
import fcntl
import sqlite3
import shutil
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import sys
import threading
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from publish_research_database import configuration

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    os.umask(0o077)
    args.directory.mkdir(parents=True, exist_ok=True)
    lockfile = (args.directory / '.archive.lock').open('w')
    fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    inventory = json.loads(args.inventory.read_text())
    entries = {x['id']: x for x in inventory['entries']}
    if inventory['title'] != 'brad2557wtn':
        raise ValueError('This import is scoped to the requested profile')
    statepath = args.directory / 'manifest.json'
    state = json.loads(statepath.read_text()) if statepath.exists() else {
        'profile': 'https://www.tiktok.com/@brad2557wtn', 'discovered': len(entries), 'videos': {}}
    v = configuration(ROOT / '.env')
    client = boto3.client('s3', endpoint_url=v['R2_ENDPOINT'],
        aws_access_key_id=v['R2_ACCESS_KEY_ID'], aws_secret_access_key=v['R2_SECRET_ACCESS_KEY'],
        region_name='auto', config=Config(signature_version='s3v4',
        request_checksum_calculation='when_required', response_checksum_validation='when_required',
        max_pool_connections=12, connect_timeout=20, read_timeout=60,
        retries={'mode': 'standard', 'max_attempts': 4}))
    bucket = v['R2_BUCKET']
    if v.get('R2_PREFIX', 'othmani').strip('/') != 'othmani' or 'private' in bucket.lower() or bucket == v.get('R2_ARCHIVE_BUCKET'):
        raise ValueError('Wrong R2 publication scope')
    # Same existing public media namespace, content-addressed originals.
    prefix = 'othmani/imports/tiktok/brad2557wtn'
    with sqlite3.connect(f'file:{ROOT}/data/research/research.sqlite3?mode=ro', uri=True) as db:
        existing_objects = {sha: key for sha, key in db.execute(
            "SELECT o.sha256,l.key FROM research_objects o JOIN research_storage_locations l ON l.object_id=o.id WHERE l.provider='r2' AND l.bucket=? AND l.state='available'", (bucket,))}


    def record(id, row):
        with LOCK:
            state['videos'][id] = row
            state['updated_at'] = datetime.now(timezone.utc).isoformat()
            save(statepath, state)
            complete = sum(x.get('state') == 'verified' for x in state['videos'].values())
            print(f'{id}: {row["state"]} ({complete}/{len(entries)} verified)', flush=True)

    def upload(path, key, sha, mime):
        try:
            head = client.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            if exc.response['Error']['Code'] not in ('404', 'NoSuchKey', 'NotFound'):
                raise
            head = None
        if head is None:
            client.upload_file(str(path), bucket, key, ExtraArgs={
                'ContentType': mime, 'Metadata': {'sha256': sha},
                'CacheControl': 'public, max-age=31536000, immutable'})
        # Read back the complete stored object, not just the upload response.
        obj = client.get_object(Bucket=bucket, Key=key)
        h = hashlib.sha256()
        for chunk in obj['Body'].iter_chunks(chunk_size=1024 * 1024):
            h.update(chunk)
        obj['Body'].close()
        if obj['ContentLength'] != path.stat().st_size or h.hexdigest() != sha:
            raise ValueError('R2 content verification failed')

    def work(entry):
        id = entry['id']
        if not id.isdecimal() or entry['url'] != f'https://www.tiktok.com/@brad2557wtn/video/{id}':
            raise ValueError('Unexpected inventory video URL')
        row = {'id': id, 'source_url': entry['url'], 'caption': entry.get('description') or entry.get('title', ''),
               'timestamp': entry.get('timestamp'), 'duration': entry.get('duration')}
        try:
            if shutil.disk_usage(args.directory).free < 2 * 1024**3:
                raise ValueError('Insufficient local space; originals retained')
            log = args.directory / f'{id}.download.log'
            with log.open('w') as f:
                result = subprocess.run([sys.executable, '-m', 'yt_dlp', '--no-playlist',
                    '--socket-timeout', '20', '--retries', '2', '--fragment-retries', '2',
                    '--write-info-json', '--no-progress', '--output', str(args.directory / '%(id)s.%(ext)s'),
                    entry['url']], stdout=f, stderr=subprocess.STDOUT, timeout=480)
            if result.returncode:
                raise RuntimeError('Download failed; see local per-video log')
            info = json.loads((args.directory / f'{id}.info.json').read_text())
            files = [p for p in args.directory.glob(f'{id}.*') if p.suffix.lower() in ('.mp4', '.webm', '.mov')]
            if len(files) != 1:
                raise ValueError('Expected exactly one complete video')
            path = files[0]
            probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'json', str(path)], capture_output=True, text=True, check=True)
            duration = float(json.loads(probe.stdout)['format']['duration'])
            if duration <= 0:
                raise ValueError('Empty video')
            sha = digest(path)
            key = existing_objects.get(sha) or f'{prefix}/objects/{sha}{path.suffix.lower()}'
            upload(path, key, sha, mimetypes.guess_type(path.name)[0] or 'video/mp4')
            row.update(state='verified', sha256=sha, size=path.stat().st_size, object_key=key,
                local_path=str(path), duration=duration, width=info.get('width'), height=info.get('height'),
                caption=info.get('description') or row['caption'], uploader=info.get('uploader'),
                verified_at=datetime.now(timezone.utc).isoformat())
            # Public provenance excludes expiring CDN URLs, cookies and downloader diagnostics.
            provenance = args.directory / f'{id}.provenance.json'
            save(provenance, {k: val for k, val in row.items() if k != 'local_path'})
            upload(provenance, f'{prefix}/provenance/{id}.json', digest(provenance), 'application/json')
        except Exception as exc:
            # Do not put endpoint URLs, credentials or signed URLs in the summary.
            row.update(state='failed', error_type=type(exc).__name__)
        record(id, row)

    pending = [e for id, e in entries.items() if state['videos'].get(id, {}).get('state') != 'verified']
    if args.limit:
        pending = pending[:args.limit]
    save(statepath, state)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        list(executor.map(work, pending))
    print(json.dumps({'discovered': len(entries), 'verified': sum(x.get('state') == 'verified' for x in state['videos'].values()),
        'failed': sum(x.get('state') == 'failed' for x in state['videos'].values())}), flush=True)


if __name__ == '__main__':
    main()
