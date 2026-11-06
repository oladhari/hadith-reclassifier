#!/usr/bin/env python3
"""Archive Ibn Abi Hatim's source scans and unverified OCR without AI judgments."""
import argparse
import hashlib
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from publish_research_assets import env_values

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data/research/rijal-sources'
IDENTIFIER='Al-Jarah_wal_Tadeel_Li_Ibn-e-Abi-Hatim_Al-Razi'


def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2).encode()
def sha256(value):return hashlib.sha256(value).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--upload',action='store_true');args=parser.parse_args()
    metadata=json.loads((CACHE/'ibn-abi-hatim-archive-metadata.json').read_text())
    files=[f for f in metadata['files'] if (f['name'].endswith('.pdf') and not f['name'].endswith('_text.pdf')) or f['name'].endswith('_djvu.txt')]
    directory=CACHE/'ibn-abi-hatim-originals';directory.mkdir(parents=True,exist_ok=True)
    values=env_values(ROOT/'.env');prefix=values.get('R2_PREFIX','othmani').strip('/')
    root=f'{prefix}/reference-books/rijal/ibn-abi-hatim-al-jarh-wa-al-tadil'
    client=None
    if args.upload:
        bucket=values['R2_BUCKET']
        if 'private' in bucket.lower() or bucket==values.get('R2_ARCHIVE_BUCKET'):raise ValueError('Expected project reference bucket')
        client=boto3.client('s3',endpoint_url=values['R2_ENDPOINT'],aws_access_key_id=values['R2_ACCESS_KEY_ID'],aws_secret_access_key=values['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(signature_version='s3v4',s3={'addressing_style':'path'},request_checksum_calculation='when_required',response_checksum_validation='when_required'))
    def put(key,body,mime):
        if not client:return 'local_only'
        try:head=client.head_object(Bucket=bucket,Key=key)
        except ClientError as error:
            if error.response['Error']['Code'] not in {'404','NoSuchKey','NotFound'}:raise
            head=None
        if head:
            if head['ContentLength']!=len(body) or head.get('Metadata',{}).get('sha256')!=sha256(body):raise ValueError('Refusing different object overwrite')
            state='verified_existing'
        else:
            client.put_object(Bucket=bucket,Key=key,Body=body,ContentType=mime,CacheControl='public, max-age=31536000, immutable',Metadata={'sha256':sha256(body)})
            state='uploaded'
        if sha256(client.get_object(Bucket=bucket,Key=key)['Body'].read())!=sha256(body):raise ValueError('R2 readback failed')
        return state
    def archive(item):
        name=item['name'];is_pdf=name.endswith('.pdf');match=re.search(r'جلد (\d+)',name)
        part=int(match[1]) if match else None
        label=f'volume-{part:02}' if part else 'cover'
        suffix='.pdf' if is_pdf else '-ocr.txt';path=directory/(label+suffix)
        if path.exists():body=path.read_bytes()
        else:
            url='https://archive.org/download/'+IDENTIFIER+'/'+quote(name)
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Othmani reference archive'}),timeout=180) as response:body=response.read()
        if len(body)!=int(item['size']) or hashlib.sha1(body).hexdigest()!=item['sha1']:raise ValueError('Archive.org checksum mismatch: '+label)
        path.write_bytes(body)
        if is_pdf and not body.startswith(b'%PDF-'):raise ValueError('Not a PDF')
        key=f'{root}/sha256/{sha256(body)}'+('.pdf' if is_pdf else '.txt')
        state=put(key,body,'application/pdf' if is_pdf else 'text/plain; charset=utf-8')
        print(label+suffix+': '+state,flush=True)
        return {'original_name':name,'source_url':'https://archive.org/download/'+IDENTIFIER+'/'+quote(name),
            'part':part,'role':'scanned_volume' if part and is_pdf else 'cover' if is_pdf else 'unverified_ocr',
            'review_state':'unverified','sha1':item['sha1'],'sha256':sha256(body),'bytes':len(body),'r2_key':key,'storage_state':state}
    with ThreadPoolExecutor(max_workers=3) as pool:objects=list(pool.map(archive,files))
    manifest={'title':'الجرح والتعديل','author':'عبد الرحمن بن أبي حاتم الرازي','archive_identifier':IDENTIFIER,
        'archive_url':'https://archive.org/details/'+IDENTIFIER,'shamela_url':'https://shamela.ws/book/2170',
        'scan_cover_publisher':'دار إحياء التراث العربي، بيروت، لبنان',
        'shamela_edition':'مطبعة مجلس دائرة المعارف العثمانية، حيدر آباد، الطبعة الأولى 1371 هـ / 1952 م',
        'same_work':True,'scan_to_shamela_edition_and_page_alignment_verified':False,
        'ocr_status':'unverified; must compare quotations with scanned pages',
        'objects':[{k:v for k,v in o.items() if k!='storage_state'} for o in objects]}
    body=canonical(manifest);key=f'{root}/manifests/{sha256(body)}.json';state=put(key,body,'application/json; charset=utf-8')
    (CACHE/'ibn-abi-hatim-r2-manifest.json').write_bytes(body)
    receipt={'manifest_key':key,'manifest_state':state,'source_objects':len(objects),'numbered_volumes':sum(o['role']=='scanned_volume' for o in objects),
        'ocr_files':sum(o['role']=='unverified_ocr' for o in objects),'bytes':sum(o['bytes'] for o in objects),'scholarly_judgments_created':0}
    (CACHE/'ibn-abi-hatim-upload-receipt.json').write_bytes(canonical(receipt));print(json.dumps(receipt),flush=True)


if __name__=='__main__':main()
