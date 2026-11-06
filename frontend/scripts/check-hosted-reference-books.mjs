import assert from 'node:assert/strict';
import {readFile,open} from 'node:fs/promises';
const allEditions=JSON.parse(await readFile(new URL('../src/content/reference-book-assets.json',import.meta.url),'utf8'));
const editions=Object.fromEntries(Object.entries(allEditions).filter(([id])=>id!=='927'));
const expected={2170:9,3722:35,3310:12,8609:1,1692:4,12579:9};
const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';
const sourceAssets=JSON.parse(await readFile(new URL('../../data/research/rijal-sources/full-books/download-assets.json',import.meta.url),'utf8'));
const sourceByHash=new Map(sourceAssets.map(f=>[f.sha256,f]));
async function fetchTimed(url,options={}){return fetch(url,{signal:AbortSignal.timeout(60000),...options});}
async function html(path){const r=await fetchTimed(base+path);assert.equal(r.status,200,path);return r.text();}
assert.deepEqual(Object.keys(editions).sort(),Object.keys(expected).sort());
let fileCount=0;
for(const [id,edition] of Object.entries(editions)){
 assert.equal(edition.volume_count,expected[id]);assert.equal(edition.complete_source_set,true);
 assert.deepEqual(edition.files.filter(f=>f.part>0&&f.part<90).map(f=>f.part),Array.from({length:expected[id]},(_,i)=>i+1));
 const page=await html(`/library/references/${id}`);assert.ok(page.includes(`data-hosted-reference="${id}"`));assert.ok(page.includes('<iframe'));assert.ok(page.includes(`/api/reference-books/${id}/part-01`));
 const last=await html(`/library/references/${id}?file=part-${String(expected[id]).padStart(2,'0')}`);assert.ok(last.includes(`/api/reference-books/${id}/part-${String(expected[id]).padStart(2,'0')}`));
 const pending=edition.files.map(asset=>async()=>{
  const route=`${base}/api/reference-books/${id}/${asset.id}`;
  const redirect=await fetchTimed(route,{redirect:'manual'});assert.equal(redirect.status,307,route);
  const url=new URL(redirect.headers.get('location'));assert.equal(url.origin,'https://media.albaalaagh.com');assert.equal(url.pathname,'/othmani/'+asset.key);
  const response=await fetchTimed(url,{headers:{Range:'bytes=0-31'}});assert.equal(response.status,206,url.href);assert.match(response.headers.get('content-type')||'',/^application\/pdf/);
  assert.equal(response.headers.get('content-range'),`bytes 0-31/${asset.bytes}`);assert.ok(!response.headers.get('x-frame-options'));
  const body=new Uint8Array(await response.arrayBuffer());assert.equal(body.length,32);assert.equal(Buffer.from(body).subarray(0,5).toString(),'%PDF-');
  const local=sourceByHash.get(asset.sha256);assert.ok(local);const path=new URL('../../'+local.local_path,import.meta.url);const file=await open(path);try{const bytes=Buffer.alloc(32);await file.read(bytes,0,32,0);assert.deepEqual(Buffer.from(body),bytes);}finally{await file.close();}
  fileCount++;
 });
 for(let offset=0;offset<pending.length;offset+=4)await Promise.all(pending.slice(offset,offset+4).map(task=>task()));
 const asset=edition.files[0];const endpoint=`/api/reference-books/${id}/${asset.id}`;
 const bad=await fetchTimed(base+endpoint,{headers:{Range:`bytes=${asset.bytes}-`},redirect:'manual'});assert.equal(bad.status,416);
 const head=await fetchTimed(base+endpoint,{method:'HEAD',redirect:'manual'});assert.equal(head.status,307);
 assert.equal((await fetchTimed(base+endpoint,{method:'POST',body:'audit'})).status,405);
 const noSsrF=await fetchTimed(base+endpoint+'?url=https://example.invalid',{redirect:'manual'});assert.equal(new URL(noSsrF.headers.get('location')).origin,'https://media.albaalaagh.com');
}
assert.equal(fileCount,75);
for(const path of ['/api/reference-books/999999/part-01','/api/reference-books/8609/part-99','/library/references/8609?file=part-99'])assert.equal((await fetchTimed(base+path)).status,404,path);
for(const range of ['bytes=0-1,2-3','bytes=-0','bytes=9999999999999999999999-'])assert.equal((await fetchTimed(base+'/api/reference-books/8609/part-01',{headers:{Range:range},redirect:'manual'})).status,416,range);
const pdfs=await html('/library?section=books&theme=rijal&kind=pdf');assert.ok(pdfs.includes('data-reference-book-count="6"'));
const taqrib=await html('/library/references/8609');assert.ok(taqrib.includes('1991'));assert.ok(taqrib.includes('1986'));
console.log(JSON.stringify({books:6,main_parts:70,pdf_files:fileCount,own_storage_delivery:'passed',all_pdf_byte_ranges:'passed',reader_and_volume_selector:'passed',editions_distinguished:'passed',read_only_allowlist_and_ranges:'passed'}));
