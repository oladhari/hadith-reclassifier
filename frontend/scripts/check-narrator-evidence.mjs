import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
const directory=JSON.parse(await readFile(new URL('src/content/narrator-directory.json',root),'utf8'));
const locations=JSON.parse(await readFile(new URL('src/content/narrator-scan-locations.json',root),'utf8'));
const assets=JSON.parse(await readFile(new URL('src/content/reference-book-assets.json',root),'utf8'));
const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';
const escape=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#x27;');
async function request(path){return fetch(base+path,{signal:AbortSignal.timeout(60000)});}
async function html(path){const r=await request(path);assert.equal(r.status,200,path);return r.text();}
let checked=0;const images=new Set();const pdfPages=new Set();
for(const person of directory.entries){
 for(const e of person.evidence){
  for(const [index,f] of e.findings.entries()){
   const key=`${person.slug}/${e.book_id}-${e.page_id}/${index}`;
   const path=`/narrators/${person.slug}/evidence/${e.book_id}-${e.page_id}?quote=${index}`;
   assert.ok(e.context.includes(f.quote),key);
   const page=await html(path);assert.ok(page.includes(`<mark>${escape(f.quote)}</mark>`),key+' exact highlight');assert.ok(page.includes(escape(f.critic)),key+' attributed critic');
   const scans=locations[key];assert.ok(scans?.length,key+' mapped scan');
   for(const scan of scans){
    assert.equal(scan.quote_sha256,createHash('sha256').update(f.critic+'\n'+f.quote).digest('hex'));
    const file=assets[e.book_id].files.find(f=>f.id===scan.file_id);assert.equal(file.sha256,scan.sha256);
    assert.ok(scan.pdf_page>=1&&scan.pdf_page<=file.pages);assert.match(scan.image,/^\/evidence\/narrators\/[a-f0-9]{16}-\d+\.webp$/);
    assert.ok(scan.rectangles.length);for(const r of scan.rectangles){assert.ok(r.x>=0&&r.y>=0&&r.width>0&&r.height>0&&r.x+r.width<=100&&r.y+r.height<=100,key+' valid rectangle');}
    assert.ok(page.includes(escape(scan.source_url)),key+' specific electronic source');
    assert.ok(page.includes(`src="${scan.image}"`));assert.ok(page.includes(`data-scan-page="${scan.pdf_page}"`));assert.ok(page.includes('أخفِ التظليل لفحص الأصل'));
    const full=`/library/references/${e.book_id}?file=${scan.file_id}&page=${scan.pdf_page}`;assert.ok(page.includes(escape(full)+'#read-book'));
    if(!pdfPages.has(full)){pdfPages.add(full);const reader=await html(full);assert.ok(reader.includes(`/api/reference-books/${e.book_id}/${scan.file_id}#page=${scan.pdf_page}&amp;view=FitH`));}
    if(!images.has(scan.image)){images.add(scan.image);const image=await request(scan.image);assert.equal(image.status,200);const hash=createHash('sha256').update(Buffer.from(await image.arrayBuffer())).digest('hex');assert.equal(hash,scan.image_sha256);}
   }
   checked++;
  }
 }
}
const list=await html('/narrators?q='+encodeURIComponent('وكيع'));assert.ok(list.includes('/narrators/waki-ibn-al-jarrah/evidence/1692-2365?quote=1'));
assert.equal(locations['waki-ibn-al-jarrah/1692-2365/1'][0].pdf_page,336);assert.equal(locations['waki-ibn-al-jarrah/1692-2365/1'][0].source_url,'https://shamela.ws/book/1692/2366');
assert.equal(locations['jafar-ibn-ziyad/8609-66/0'][0].pdf_page,147);
for(const path of ['/narrators/no-person/evidence/1692-5','/narrators/waki-ibn-al-jarrah/evidence/1692-5','/narrators/waki-ibn-al-jarrah/evidence/1692-2365?quote=99','/narrators/waki-ibn-al-jarrah/evidence/1692-2365?quote=-1','/narrators/waki-ibn-al-jarrah/evidence/1692-2365?quote=1e0','/library/references/1692?file=part-04&page=751'])assert.equal((await request(path)).status,404,path);
const malicious='/narrators/waki-ibn-al-jarrah/evidence/1692-2365?quote='+encodeURIComponent('<img src=x onerror=alert(1)>');assert.equal((await request(malicious)).status,404);
console.log(JSON.stringify({findings:checked,scan_images:images.size,exact_quotes:'passed',critic_attribution:'passed',source_pdf_checksums:'passed',page_fragments:'passed',image_integrity:'passed',invalid_selections:'passed'}));
