import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const all=JSON.parse(await readFile(new URL('../src/content/reference-book-assets.json',import.meta.url),'utf8'));
const edition=all['927'];const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';
assert.equal(edition.volume_count,9);assert.equal(edition.file_count,10);
assert.deepEqual(edition.files.map(f=>f.part),[1,2,3,4,5,6,7,8,9,90]);
assert.equal(edition.files[0].pages,580);assert.equal(edition.files[8].pages,592);assert.equal(edition.files[9].pages,179);
for(const f of edition.files){
 const response=await fetch(`${base}/api/reference-books/927/${f.id}`,{redirect:'manual'});assert.equal(response.status,307);
 const pdf=await fetch(response.headers.get('location'),{headers:{Range:'bytes=0-31'}});assert.equal(pdf.status,206);assert.equal(pdf.headers.get('content-range'),`bytes 0-31/${f.bytes}`);assert.equal(Buffer.from(await pdf.arrayBuffer()).subarray(0,5).toString(),'%PDF-');
 const page=await fetch(`${base}/library/references/927?file=${f.id}`);assert.equal(page.status,200);assert.ok((await page.text()).includes(`/api/reference-books/927/${f.id}`));
}
const page=await(await fetch(base+'/library?section=books&theme=creed')).text();assert.ok(page.includes('data-reference-book-id="927"'));
assert.equal((await fetch(base+'/api/reference-books/927/part-99')).status,404);
console.log('Minhaj: nine volumes, separate introduction, ten public PDFs and thematic listing verified.');
