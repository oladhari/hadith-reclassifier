#!/usr/bin/env python3
"""Export validated, previously completed public drafts; makes no API/DB calls."""
import hashlib,json
from pathlib import Path
from analyse_hadith_batch import DIRECTORY,PROFILE,ROOT,validate

def main():
 manifest=json.loads((DIRECTORY/'input-manifest.json').read_text());profile=json.loads(PROFILE.read_text());assert hashlib.sha256(PROFILE.read_bytes()).hexdigest()==manifest['profile_sha256']
 drafts=[]
 for record in manifest['records']:
  n=str(record['source_number']);data=json.loads((DIRECTORY/f'{n}.json').read_text());validate(data['report'],record)
  assert data['text_sha256']==record['text_sha256'] and data['profile_sha256']==manifest['profile_sha256']
  report=data['report'];layers=[]
  for layer,definition in zip(report['layers'],profile['layers']):layers.append({**layer,'title':definition['title']})
  public={'summary':report['summary'],'report_type':report['report_type'],'themes':report['themes'],'layers':layers}
  drafts.append(dict(collection='bukhari',source_number=n,model=data['model'],profile_key=data['profile_key'],profile_version=data['profile_version'],created_at=data['created_at'],report=public))
 assert len(drafts)==200
 (ROOT/'frontend/src/content/ai-hadith-drafts.json').write_text(json.dumps(drafts,ensure_ascii=False,separators=(',',':'))+'\n')
 print('Exported 200 validated public drafts; no API or database calls.')
if __name__=='__main__':main()
