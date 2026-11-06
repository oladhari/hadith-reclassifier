#!/usr/bin/env python3
"""Publish only the existing public Arabic corpus to immutable R2 build assets."""
import gzip,hashlib,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from publish_research_assets import env_values
ROOT=Path(__file__).resolve().parents[1]
def main():
 v=env_values(ROOT/'.env');bucket=v['R2_BUCKET'];prefix=v.get('R2_PREFIX','othmani').strip('/')
 if prefix!='othmani' or 'private' in bucket.lower() or bucket==v.get('R2_ARCHIVE_BUCKET'):raise ValueError('Wrong publication scope')
 s3=boto3.client('s3',endpoint_url=v['R2_ENDPOINT'],aws_access_key_id=v['R2_ACCESS_KEY_ID'],aws_secret_access_key=v['R2_SECRET_ACCESS_KEY'],region_name='auto',config=Config(signature_version='s3v4',max_pool_connections=8,request_checksum_calculation='when_required',response_checksum_validation='when_required'))
 seed=json.loads((ROOT/'frontend/src/content/editorial-seed.json').read_text());progress=json.loads((ROOT/'frontend/src/content/corpus-progress.json').read_text());counts={r['slug']:r['counts']['total'] for r in progress['collections']}
 def publish(name):
  raw=(ROOT/f'frontend/.corpus/ara-{name}.json').read_bytes();data=json.loads(raw);rows=data['hadiths']
  if len(rows)!=counts[name] or not all('hadithnumber' in row for row in rows):raise ValueError('Corpus differs from published counts')
  digest=hashlib.sha256(raw).hexdigest();body=gzip.compress(raw,mtime=0);compressed=hashlib.sha256(body).hexdigest();relative=f'site-snapshots/corpus/sha256/{compressed}.json.gz';key=f'{prefix}/{relative}'
  try:head=s3.head_object(Bucket=bucket,Key=key)
  except ClientError as e:
   if e.response['Error']['Code'] not in {'404','NoSuchKey','NotFound'}:raise
   head=None
  if head:
   if head['ContentLength']!=len(body) or head.get('Metadata',{}).get('sha256')!=compressed:raise ValueError('Refusing different object overwrite')
  else:s3.put_object(Bucket=bucket,Key=key,Body=body,ContentType='application/gzip',CacheControl='public, max-age=31536000, immutable',Metadata={'sha256':compressed,'uncompressed-sha256':digest})
  if hashlib.sha256(s3.get_object(Bucket=bucket,Key=key)['Body'].read()).hexdigest()!=compressed:raise ValueError('R2 readback mismatch')
  print(f'{name}: {len(rows)} public records verified',flush=True)
  return name,dict(key=relative,sha256=digest,gzip_sha256=compressed,bytes=len(raw),gzip_bytes=len(body),records=len(rows))
 with ThreadPoolExecutor(max_workers=4) as pool:assets=dict(pool.map(publish,seed['collections']))
 target=ROOT/'frontend/src/content/corpus-assets.json';target.write_text(json.dumps({'version':1,'collections':assets},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'collections':len(assets),'records':sum(a['records'] for a in assets.values()),'build_transfer_bytes':sum(a['gzip_bytes'] for a in assets.values()),'all_r2_readback_verified':True}))
if __name__=='__main__':main()
