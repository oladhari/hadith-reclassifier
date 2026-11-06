#!/usr/bin/env python3
"""Publish the matching nine-volume Minhaj set, preserving the separate introduction."""
import hashlib,json,sqlite3,subprocess
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from publish_research_assets import env_values
ROOT=Path(__file__).resolve().parents[1]
def main():
 cache=ROOT/'data/research/reference-additions/minhaj';v=env_values(ROOT/'.env');bucket=v['R2_BUCKET'];prefix=v.get('R2_PREFIX','othmani').strip('/')
 if prefix!='othmani' or 'private' in bucket.lower() or bucket==v.get('R2_ARCHIVE_BUCKET'):raise ValueError('Wrong destination')
 s3=boto3.client('s3',endpoint_url=v['R2_ENDPOINT'],aws_access_key_id=v['R2_ACCESS_KEY_ID'],aws_secret_access_key=v['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(signature_version='s3v4',request_checksum_calculation='when_required',response_checksum_validation='when_required'))
 db=sqlite3.connect(ROOT/'data/research/research.sqlite3');files=[];receipt=[]
 for part in [*range(1,10),90]:
  source='01.pdf' if part==1 else '10.pdf' if part==9 else '02.pdf' if part==90 else f'{part+1:02}.pdf'
  if part in (1,9):
   h='672bd7b40ffcece34402b626da872b58d17cc0a7' if part==1 else 'bcd1328b2671a26ec8a34b1e463fc410368df293';path=cache/'packages'/f'{h}.pdf'
   if hashlib.sha1(path.read_bytes()).hexdigest()!=h:raise ValueError('Source checksum mismatch')
  else:
   mid=908 if part==90 else part+907
   row=db.execute("select l.key from research_media m join research_storage_locations l on l.object_id=m.object_id where m.legacy_id=? and l.provider='local'",(mid,)).fetchone()
   path=ROOT.parent/'telegram-archive/kkee9938'/row[0]
  data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();key=f'{prefix}/reference-books/creed/minhaj/sha256/{digest}.pdf'
  pages=int(next(x.split(':',1)[1].strip() for x in subprocess.check_output(['pdfinfo',str(path)],text=True).splitlines() if x.startswith('Pages:')))
  try:head=s3.head_object(Bucket=bucket,Key=key)
  except ClientError as e:
   if e.response['Error']['Code'] not in ('404','NoSuchKey','NotFound'):raise
   head=None
  if head:
   if head['ContentLength']!=len(data) or head.get('Metadata',{}).get('sha256')!=digest:raise ValueError('Refusing different object overwrite')
  else:s3.put_object(Bucket=bucket,Key=key,Body=data,ContentType='application/pdf',CacheControl='public, max-age=31536000, immutable',Metadata={'sha256':digest})
  stream=s3.get_object(Bucket=bucket,Key=key)['Body'];check=hashlib.sha256()
  try:
   for block in iter(lambda:stream.read(1048576),b''):check.update(block)
  finally:stream.close()
  if check.hexdigest()!=digest:raise ValueError('Readback failed')
  files.append(dict(id=f'part-{part:02}',part=part,label='مقدمة المحقق — ملف مستقل' if part==90 else f'المجلد {part}',key=key.removeprefix(prefix+'/'),sha256=digest,bytes=len(data),pages=pages,source_url=f'https://archive.org/download/manhaj-ah-sonna/{source}',original_name=source,source_archive='manhaj-ah-sonna'))
  receipt.append(dict(part=part,sha256=digest,readback_verified=True,local_path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)))
  print(f'Part {part}: verified {pages} pages',flush=True)
 manifest=ROOT/'frontend/src/content/reference-book-assets.json';all_books=json.loads(manifest.read_text());all_books['927']=dict(format='pdf_scans',complete_source_set=True,scanned_edition='تحقيق محمد رشاد سالم، جامعة الإمام محمد بن سعود الإسلامية، الطبعة الأولى، 1406 هـ / 1986 م، تسعة مجلدات، ومقدمة المحقق محفوظة في ملف مستقل.',volume_count=9,file_count=len(files),pages=sum(f['pages'] for f in files),files=files,edition_note='المجلد الأول هنا متن الكتاب، ومقدمة المحقق محفوظة مستقلة وليست بديلاً عنه. طابقت بصمات ملفات المجلدات 2–8 النسخ المحفوظة سابقاً. أرقام صفحات PDF لا تطابق بالضرورة ترقيم النص الإلكتروني في الشاملة.')
 manifest.write_text(json.dumps(all_books,ensure_ascii=False,indent=2)+'\n');(cache/'publish-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
