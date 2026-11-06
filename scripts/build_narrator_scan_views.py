#!/usr/bin/env python3
"""Re-render reviewed narrator page images from checksum-verified original PDFs.

The public manifest contains reviewed page coordinates. This command never
creates narrator judgments, guesses page offsets or automatically publishes OCR.
"""
import hashlib,json,subprocess,tempfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
 manifests=json.loads((ROOT/'frontend/src/content/narrator-scan-locations.json').read_text())
 editions=json.loads((ROOT/'frontend/src/content/reference-book-assets.json').read_text())
 local=json.loads((ROOT/'data/research/rijal-sources/full-books/download-assets.json').read_text())
 by_hash={a['sha256']:ROOT/a['local_path'] for a in local};seen=set();verified=set()
 with tempfile.TemporaryDirectory(prefix='othmani-scan-pages-') as temporary:
  for scans in manifests.values():
   for scan in scans:
    asset=next(f for f in editions[str(scan['book_id'])]['files'] if f['id']==scan['file_id'])
    if asset['sha256']!=scan['sha256'] or not 1<=scan['pdf_page']<=asset['pages']:raise ValueError('Stale source mapping')
    if scan['image'] in seen:continue
    seen.add(scan['image']);path=by_hash[scan['sha256']]
    if scan['sha256'] not in verified:
     if hashlib.sha256(path.read_bytes()).hexdigest()!=scan['sha256']:raise ValueError('Original PDF changed')
     verified.add(scan['sha256'])
    target=ROOT/'frontend/public'/scan['image'].lstrip('/')
    if not target.is_relative_to(ROOT/'frontend/public/evidence/narrators'):raise ValueError('Wrong output scope')
    prefix=Path(temporary)/'page';page=str(scan['pdf_page'])
    subprocess.run(['pdftoppm','-f',page,'-l',page,'-singlefile','-scale-to','2000','-png',str(path),str(prefix)],check=True,stderr=subprocess.DEVNULL)
    image=Image.open(prefix.with_suffix('.png')).convert('RGB')
    if image.size!=(scan['width'],scan['height']):raise ValueError('Page geometry changed')
    target.parent.mkdir(parents=True,exist_ok=True);image.save(target,'WEBP',quality=90)
    if hashlib.sha256(target.read_bytes()).hexdigest()!=scan['image_sha256']:raise ValueError('Rendered page bytes changed; review before updating manifest')
 print(f'Verified {len(seen)} original page images from {len(verified)} source PDFs.')
if __name__=='__main__':main()
