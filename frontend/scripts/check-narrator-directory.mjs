import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const directory=JSON.parse(await readFile(new URL('../src/content/narrator-directory.json',import.meta.url),'utf8'));
const books=JSON.parse(await readFile(new URL('../src/content/reference-books.json',import.meta.url),'utf8'));
const themes=JSON.parse(await readFile(new URL('../src/content/book-themes.json',import.meta.url),'utf8'));
const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';
async function html(path){const r=await fetch(base+path,{signal:AbortSignal.timeout(60000)});assert.equal(r.status,200,path);return r.text();}
const escape=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#x27;');
const index=await html('/narrators');assert.ok(index.includes('href="/narrators"'));assert.ok(index.includes(`data-narrator-result-count="${directory.entries.length}"`));
for(const person of directory.entries){
 assert.equal(person.scholarly_verdict,null);assert.equal(person.hadith_route_identity_linked,false);
 const page=await html('/narrators/'+person.slug);assert.ok(page.includes(escape(person.name)));
 for(const e of person.evidence){
  assert.ok(page.includes(e.url));assert.ok(page.includes(`/library/references/${e.book_id}`));
  assert.ok(e.context.startsWith(String(e.entry_number))||/^\(?[0-9٠-٩]|^\[/.test(e.context));
  for(const f of e.findings){assert.ok(e.context.includes(f.quote),person.slug+' quote boundary');assert.ok(page.includes(escape(f.quote)),person.slug+' displayed quote');assert.ok(page.includes(escape(f.critic)));}
 }
}
for(const [finding,count] of [['mild',2],['rafidi_jald',2],['shii_jald',3],['liar',3],['accused',3],['unknown',1]])assert.ok((await html('/narrators?finding='+finding)).includes(`data-narrator-result-count="${count}"`),finding);
assert.ok((await html('/narrators?source_book=2170')).includes('data-narrator-result-count="0"'));
assert.ok((await html('/narrators?q='+encodeURIComponent('زبيد'))).includes('data-narrator-result-count="1"'));
const contrary=await html('/narrators/abd-al-rahman-ibn-hatim');assert.ok(contrary.includes('متروك الحديث'));assert.ok(contrary.includes('ما علمت به بأسا'));
const library=await html('/library?section=books');assert.equal((library.match(/data-reference-index-id=/g)||[]).length,7);assert.equal((library.match(/data-book-index-id=/g)||[]).length,26);
for(const key of Object.keys(themes.themes)){assert.ok(library.includes(`data-book-theme="${key}"`));await html('/library?section=books&theme='+key);}
const rijal=await html('/library?section=books&theme=rijal');assert.ok(rijal.includes('data-reference-book-count="6"'));assert.ok(!rijal.includes('data-book-index-id="909"'));
for(const book of books){const page=await html(`/library/references/${book.id}`);assert.ok(page.includes(book.url));if(book.id===2170)assert.equal((page.replace(/<!--[\s\S]*?-->/g,"").match(/الملف المصور \d+ — PDF/g)||[]).length,9);}
const found=await html('/library?section=books&q='+encodeURIComponent('تقريب التهذيب'));assert.ok(found.includes('/library/references/8609'));
for(const path of ['/narrators/not-a-narrator','/library/references/999999'])assert.equal((await fetch(base+path)).status,404);
for(const path of ['/narrators?finding=not-real','/library?theme=not-real'])assert.equal((await fetch(base+path)).status,400);
const payload='<img src=x onerror=alert(1)>';assert.ok(!(await html('/narrators?q='+encodeURIComponent(payload))).includes(payload));
for(const [query,slug] of [['وكيع','waki-ibn-al-jarrah'],['الأعمش','sulayman-al-amash'],['سليمان بن مهران','sulayman-al-amash']]){
 const result=await html('/narrators?q='+encodeURIComponent(query));assert.ok(result.includes(`data-narrator-slug="${slug}"`));
 const page=await html('/narrators/'+slug);assert.ok(page.includes('data-narrator-library-evidence='));assert.ok(page.includes('/library/'+(slug==='waki-ibn-al-jarrah'?'760':'987')));
}
console.log(JSON.stringify({narrators:26,source_findings:60,citation_boundaries:'passed',all_profiles_and_filters:'passed',contradictory_assessments:'preserved',reference_books:7,thematic_groups:6,old_books:26,read_only_security:'passed'}));
