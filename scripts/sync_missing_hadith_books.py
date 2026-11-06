#!/usr/bin/env python3
"""Archive missing AhmedBaset collections as immutable JSON objects in project R2.

Preserves upstream bytes and dataset-local numbering; does not create scholarly
assessments or publish searchable corpus records. No paid AI/API calls.
"""
import argparse
import hashlib
import json
import sqlite3
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from publish_research_assets import env_values

ROOT=Path(__file__).resolve().parents[1]
REVISION='70b83d6d21995bb32f8d7271cd75501be5a922a7'
REPOSITORY='https://github.com/AhmedBaset/hadith-json'
CACHE=ROOT/'data/research/source-checks/ahmed-baset'
ALIASES={'ahmed':'ahmad'}


def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2).encode()
def sha256(body):return hashlib.sha256(body).hexdigest()
def git_sha(body):return hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Othmani-source-archive'}),timeout=90) as response:
        return response.read()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upload',action='store_true',help='Upload and read back validated objects; default is inspection only')
    args=parser.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True)
    tree_path=CACHE/'repository-tree.json'
    if tree_path.exists():tree=json.loads(tree_path.read_text())
    else:
        tree=json.loads(fetch(f'https://api.github.com/repos/AhmedBaset/hadith-json/git/trees/{REVISION}?recursive=1'))
        tree_path.write_bytes(canonical(tree))
    if tree['sha']!=REVISION or tree.get('truncated'):raise ValueError('Repository tree is not complete or pinned')
    with sqlite3.connect(f'file:{ROOT / "data/research/research.sqlite3"}?mode=ro',uri=True) as db:
        existing={row[0] for row in db.execute('SELECT slug FROM research_collections')}
    books=[row for row in tree['tree'] if row['path'].startswith('db/by_book/') and row['path'].endswith('.json')]
    missing=[row for row in books if ALIASES.get(Path(row['path']).stem,Path(row['path']).stem) not in existing]
    if not missing:
        # Keep the previous archive index for provenance/recovery after books
        # have been promoted into the searchable corpus.
        print(json.dumps({"missing_books":0,"existing_collections":len(existing),"archive_index_preserved":(CACHE/"r2-books-index.json").exists()}),flush=True)
        return
    def download(entry):
        filename=Path(entry['path']).name
        path=CACHE/filename
        if path.exists():body=path.read_bytes()
        else:
            body=fetch(f'https://raw.githubusercontent.com/AhmedBaset/hadith-json/{REVISION}/{entry["path"]}')
        if git_sha(body)!=entry['sha'] or len(body)!=entry['size']:raise ValueError('Upstream checksum mismatch: '+filename)
        path.write_bytes(body)
        data=json.loads(body);rows=data['hadiths'];metadata=data['metadata']
        if len(rows)!=metadata['length'] or len({row['idInBook'] for row in rows})!=len(rows):raise ValueError('Inconsistent count or duplicate dataset numbers: '+filename)
        if any(row['bookId']!=data['id'] or not isinstance(row['arabic'],str) for row in rows):raise ValueError('Invalid book/text association: '+filename)
        result={'slug':ALIASES.get(path.stem,path.stem),'filename':filename,'title':metadata['arabic']['title'],
            'author':metadata['arabic']['author'],'records':len(rows),'chapter_ids':[chapter['id'] for chapter in data['chapters']],
            'empty_arabic_records':sum(not row['arabic'].strip() for row in rows),'bytes':len(body),'sha256':sha256(body),
            'git_blob_sha':entry['sha'],'repository':REPOSITORY,'revision':REVISION,'source_path':entry['path'],
            'source_url':f'https://raw.githubusercontent.com/AhmedBaset/hadith-json/{REVISION}/{entry["path"]}',
            'coverage':'partial' if path.stem=='ahmed' else 'not_independently_verified',
            'coverage_note':'مجموعة جزئية؛ الأقسام 8–30 غير موجودة في المصدر.' if path.stem=='ahmed' else 'أُرشف الملف كما هو في المصدر؛ لم تُتحقق مقابلته بطبعة كاملة مستقلة.',
            'numbering_note':'الأرقام محلية في مجموعة البيانات؛ لم تُطابق بترقيم طبعة مطبوعة.',
            'corpus_imported':False}
        return result,body
    with ThreadPoolExecutor(max_workers=4) as pool:downloads=list(pool.map(download,missing))
    config=env_values(ROOT/'.env')
    prefix=config.get('R2_PREFIX','othmani').strip('/')
    if not prefix.startswith('othmani'):raise ValueError('Unexpected project prefix')
    root=f'{prefix}/datasets/hadith-json/{REVISION}'
    client=None
    if args.upload:
        bucket=config['R2_BUCKET']
        if 'private' in bucket.lower() or bucket==config.get('R2_ARCHIVE_BUCKET'):raise ValueError('Expected project source bucket')
        client=boto3.client('s3',endpoint_url=config['R2_ENDPOINT'],aws_access_key_id=config['R2_ACCESS_KEY_ID'],aws_secret_access_key=config['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(signature_version='s3v4',s3={'addressing_style':'path'},request_checksum_calculation='when_required',response_checksum_validation='when_required'))
    def put(key,body):
        if not client:return 'inspection_only'
        try:head=client.head_object(Bucket=bucket,Key=key)
        except ClientError as error:
            if error.response['Error']['Code'] not in {'404','NoSuchKey','NotFound'}:raise
            head=None
        if head:
            if head['ContentLength']!=len(body) or head.get('Metadata',{}).get('sha256')!=sha256(body):raise ValueError('Refusing to overwrite different object: '+key)
            state='verified_existing'
        else:
            client.put_object(Bucket=bucket,Key=key,Body=body,ContentType='application/json; charset=utf-8',CacheControl='public, max-age=31536000, immutable',Metadata={'sha256':sha256(body)})
            state='uploaded'
        remote=client.get_object(Bucket=bucket,Key=key)['Body'].read()
        if sha256(remote)!=sha256(body):raise ValueError('R2 readback checksum mismatch: '+key)
        return state
    results=[]
    for metadata,body in downloads:
        directory='musnad-ahmad-partial' if metadata['slug']=='ahmad' else Path(metadata['filename']).stem
        key=f'{root}/{directory}/{metadata["filename"]}'
        metadata['r2_key']=key
        metadata_key=f'{root}/{directory}/catalogue-metadata.json'
        source_state=put(key,body)
        metadata_state=put(metadata_key,canonical(metadata))
        results.append({**metadata,'metadata_key':metadata_key,'source_state':source_state,'metadata_state':metadata_state})
        print(json.dumps({'title':metadata['title'],'records':metadata['records'],'source':source_state,'metadata':metadata_state},ensure_ascii=False),flush=True)
    # Stable content-addressed index preserves previous inventories on reruns.
    index={'repository':REPOSITORY,'revision':REVISION,'existing_corpus_collections':sorted(existing),
        'books':[{k:v for k,v in row.items() if k not in {'source_state','metadata_state'}} for row in results],
        'records':sum(row['records'] for row in results),'status':'source_archive_only_not_imported_into_search'}
    body=canonical(index);index_key=f'{root}/indexes/{sha256(body)}.json';index_state=put(index_key,body)
    (CACHE/'r2-books-index.json').write_bytes(body)
    receipt={'mode':'uploaded' if args.upload else 'inspection_only','index_key':index_key,'index_state':index_state,
        'books':len(results),'records':index['records'],'source_uploaded':sum(row['source_state']=='uploaded' for row in results),
        'source_reused':sum(row['source_state']=='verified_existing' for row in results),'bytes':sum(row['bytes'] for row in results),
        'objects_verified':len(results)*2+1 if args.upload else 0,'results':results}
    (CACHE/('r2-books-receipt.json' if args.upload else 'books-inspection.json')).write_bytes(canonical(receipt))
    print(json.dumps({k:v for k,v in receipt.items() if k!='results'},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
