#!/usr/bin/env python3
"""Read-only media traversal probe using our own temporary symlink fixture."""
import json,os,signal,subprocess,tempfile,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='othmani-security-fixture-') as directory:
 base=Path(directory);archive=base/'archive';target=archive/'media/195';target.mkdir(parents=True)
 marker='OWNED_SECURITY_FIXTURE_NOT_A_REAL_SECRET';outside=base/'outside.txt';outside.write_text(marker)
 (target/'attachment.jpg').symlink_to(outside)
 env=dict(os.environ,TELEGRAM_ARCHIVE_DIR=str(archive),MEDIA_PUBLIC_BASE_URL='',RESEARCH_READ_DATABASE_URL='',NODE_OPTIONS='--network-family-autoselection-attempt-timeout=2000')
 with (base/'server.log').open('w') as log:
  process=subprocess.Popen(['npm','--prefix','frontend','run','start','--','--hostname','127.0.0.1','--port','3111'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   url='http://127.0.0.1:3111/api/media/195'
   for attempt in range(60):
    try:
     with urllib.request.urlopen(url,timeout=2) as response: status,body=response.status,response.read().decode()
     break
    except urllib.error.HTTPError as error:status,body=error.code,error.read().decode();break
    except (OSError,urllib.error.URLError):time.sleep(.25)
   else:raise RuntimeError('Fixture server did not start')
   assert status==404 and marker not in body,(status,body[:100])
   report={'passed':True,'status':status,'scope':'Owned temporary symlink outside configured archive root; no original archive changes or real secrets accessed'}
   (ROOT/'output/security/media-symlink-test.json').write_text(json.dumps(report,indent=2)+'\n')
   print('Media real-path boundary verified: outside-root symlink returns 404.')
  finally:
   os.killpg(process.pid,signal.SIGTERM)
   process.wait(timeout=10)
