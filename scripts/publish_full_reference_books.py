#!/usr/bin/env python3
"""Publish validated full reference PDFs to R2 and build the website allowlist.

--watch uploads finished files while downloads continue; the public manifest is
written only after every expected book/set has been validated.
"""
import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError
from publish_research_assets import env_values
from download_full_reference_books import CACHE,ROOT,sha

EXPECTED={2170:9,3722:35,3310:12,8609:1,1692:4,12579:9}
SCANNED_EDITIONS={2170:'مطبعة دائرة المعارف العثمانية، حيدر آباد، 1371 هـ / 1952 م، مع غلاف إعادة نشر دار إحياء التراث العربي. أرقام ملفات الأرشيف ليست مقابلة بعد بأجزاء الطبعة.',3722:'تحقيق بشار عواد معروف، مؤسسة الرسالة، مجموعة من 35 مجلداً.',3310:'دار الكتاب الإسلامي، القاهرة، مجموعة من 12 جزءاً. تختلف بطاقة هذه النسخة المصورة عن بطاقة الطبعة الهندية الإلكترونية.',8609:'تحقيق محمد عوامة، دار الرشيد، الطبعة الثالثة المنقحة، 1411 هـ / 1991 م؛ تختلف عن طبعة النص الإلكتروني المرجعي الأولى 1406 هـ / 1986 م.',1692:'نسخة دار المعرفة من ميزان الاعتدال، أربعة أجزاء، مع ملفات الغلاف والمقدمة المصاحبة محفوظة منفصلة.',12579:'دار الكتب العلمية، تحقيق عادل أحمد عبد الموجود وعلي محمد معوض، بمشاركة عبد الفتاح أبو سنة، تسعة أجزاء.'}


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--watch',action='store_true');args=parser.parse_args()
 values=env_values(ROOT/'.env');bucket=values['R2_BUCKET'];prefix=values.get('R2_PREFIX','othmani').strip('/')
 if 'private' in bucket.lower() or bucket==values.get('R2_ARCHIVE_BUCKET') or prefix!='othmani':raise ValueError('Wrong destination scope')
 client=boto3.client('s3',endpoint_url=values['R2_ENDPOINT'],aws_access_key_id=values['R2_ACCESS_KEY_ID'],aws_secret_access_key=values['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(signature_version='s3v4',max_pool_connections=12,request_checksum_calculation='when_required',response_checksum_validation='when_required'))
 transfer=TransferConfig(multipart_threshold=32*1024*1024,max_concurrency=2)
 receipt_path=CACHE/'publish-receipt.json';completed=json.loads(receipt_path.read_text()).get('files',{}) if receipt_path.exists() else {}
 def publish(asset):
  path=ROOT/asset['local_path']
  if path.stat().st_size!=asset['bytes'] or sha(path)!=asset['sha256']:raise ValueError('Local PDF changed')
  key=asset.get('previous_r2_key') or f"{prefix}/reference-books/rijal/full/sha256/{asset['sha256']}.pdf"
  try:existing=client.head_object(Bucket=bucket,Key=key)
  except ClientError as error:
   if error.response['Error']['Code'] not in {'404','NoSuchKey','NotFound'}:raise
   existing=None
  if existing:
   if existing['ContentLength']!=asset['bytes'] or existing.get('Metadata',{}).get('sha256')!=asset['sha256']:raise ValueError('Different R2 object; refusing overwrite')
   state='verified_existing'
  else:
   client.upload_file(str(path),bucket,key,ExtraArgs={'ContentType':'application/pdf','CacheControl':'public, max-age=31536000, immutable','Metadata':{'sha256':asset['sha256']}},Config=transfer);state='uploaded'
  digest=hashlib.sha256()
  stream=client.get_object(Bucket=bucket,Key=key)['Body']
  try:
   for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
  finally:stream.close()
  if digest.hexdigest()!=asset['sha256']:raise ValueError('R2 readback checksum mismatch')
  print(f"{asset['book_id']}/{asset['part']}: {state}",flush=True)
  return {'book_id':asset['book_id'],'part':asset['part'],'sha256':asset['sha256'],'key':key,'bytes':asset['bytes'],'pages':asset['pages'],'state':state,'readback_verified':True}
 while True:
  final=CACHE/'download-assets.json';partial=CACHE/'download-assets.partial.json';path=final if final.exists() else partial
  try:assets=json.loads(path.read_text()) if path.exists() else []
  except json.JSONDecodeError:assets=[]
  pending=[a for a in assets if a['sha256'] not in completed]
  with ThreadPoolExecutor(max_workers=4) as pool:
   for record in pool.map(publish,pending):
    completed[record['sha256']]=record;receipt_path.write_text(json.dumps({'files':completed},ensure_ascii=False,indent=2))
  if final.exists():break
  if not args.watch:raise RuntimeError('Download all source sets first, or use --watch')
  time.sleep(10)
 # Re-read the final list, which may have arrived during a background upload.
 assets=json.loads(final.read_text());missing=[a for a in assets if a['sha256'] not in completed]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for record in pool.map(publish,missing):completed[record['sha256']]=record
 receipt_path.write_text(json.dumps({'files':completed},ensure_ascii=False,indent=2))
 manifest_path=ROOT/'frontend/src/content/reference-book-assets.json'
 public={k:v for k,v in json.loads(manifest_path.read_text()).items() if int(k) not in EXPECTED} if manifest_path.exists() else {}
 for book,expected in EXPECTED.items():
  items=sorted([a for a in assets if a['book_id']==book and 1<=a['part']<=expected],key=lambda a:a['part'])
  covers=sorted([a for a in assets if a['book_id']==book and a['part'] not in range(1,expected+1)],key=lambda a:a['part'])
  if len({a['part'] for a in covers})!=len(covers) or any(a['part'] not in {0,90} for a in covers):raise ValueError('Unknown or duplicate supplement')
  if [a['part'] for a in items]!=list(range(1,expected+1)):raise ValueError(f'Expected exactly {expected} ordered volumes for {book}; inspect source archive contents before publishing')
  files=[]
  for a in items+covers:
   r=completed[a['sha256']]
   files.append({'id':f"part-{a['part']:02}",'part':a['part'],'label':'الغلاف' if a['part']==0 else 'مقدمة المحقق' if a['part']==90 else f"الملف {a['part']}" if book==2170 else 'الكتاب كاملاً' if expected==1 else f"المجلد {a['part']}",
       'key':r['key'].removeprefix(prefix+'/'),'sha256':a['sha256'],'bytes':a['bytes'],'pages':a['pages'],
       'source_url':a['source_url'],'original_name':a['original_name'],'source_archive':a['source_archive']})
  public[str(book)]={'format':'pdf_scans','complete_source_set':True,'scanned_edition':SCANNED_EDITIONS[book],'file_count':len(files),'volume_count':expected,'pages':sum(f['pages'] for f in files),'files':files,
   'edition_note':'تُعرض طبعة الملفات المصورة مستقلة عن الطبعة الإلكترونية المرجعية. لا يُفترض تطابق أرقام صفحات PDF مع أرقام الشاملة دون مقابلة.'}
 body=json.dumps(public,ensure_ascii=False,sort_keys=True,indent=2).encode();digest=hashlib.sha256(body).hexdigest();key=f'{prefix}/reference-books/rijal/full/manifests/{digest}.json'
 client.put_object(Bucket=bucket,Key=key,Body=body,ContentType='application/json; charset=utf-8',CacheControl='public, max-age=31536000, immutable',Metadata={'sha256':digest})
 if hashlib.sha256(client.get_object(Bucket=bucket,Key=key)['Body'].read()).hexdigest()!=digest:raise ValueError('Manifest readback failed')
 (ROOT/'frontend/src/content/reference-book-assets.json').write_bytes(body+b'\n')
 (CACHE/'publication-summary.json').write_text(json.dumps({'books':len(public),'pdf_files':sum(b['file_count'] for b in public.values()),'bytes':sum(f['bytes'] for b in public.values() for f in b['files']),'manifest_key':key,'all_readback_verified':True},indent=2))
 print((CACHE/'publication-summary.json').read_text(),flush=True)


if __name__=='__main__':main()
