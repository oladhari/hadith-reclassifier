import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { parseHadithQuery,hadithWords } from '../src/lib/hadith-query.ts';
const books={ahmad:1374,darimi:3406,riyad_assalihin:1896,shamail_muhammadiyah:402,bulugh_almaram:1767,aladab_almufrad:1326,mishkat_almasabih:4428,nawawi40:42,qudsi40:40,shahwaliullah40:40};
const seed=JSON.parse(await readFile(new URL('../src/content/editorial-seed.json',import.meta.url),'utf8'));
const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';
async function html(path){const r=await fetch(base+path,{signal:AbortSignal.timeout(60000)});assert.equal(r.status,200,path);return r.text();}
const escape=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#x27;');
const corpus=await html('/corpus');
assert.match(corpus,/<details class="corpus-inventory" open="">/);
assert.equal((corpus.match(/data-corpus-collection=/g)||[]).length,17);
assert.ok(corpus.includes('51,111')||corpus.includes('51111'));
for(const [slug,count] of Object.entries(books)){
 assert.ok(corpus.includes(`data-corpus-collection="${slug}"`));
 assert.deepEqual(parseHadithQuery(`${seed.collections[slug]} ١`),{q:'',id:'1',collection:slug});
 const page=await html('/corpus?'+new URLSearchParams({collection:slug,id:'١'}));
 assert.ok(page.includes('data-hadith-number="1"'),slug);
 const first=JSON.parse(await readFile(new URL(`../../data/hadiths/ara-${slug}.json`,import.meta.url),'utf8')).hadiths[0];
 const reader=await html(`/corpus/${slug}/1`);assert.ok(reader.includes(escape(first.text)),slug);
 assert.ok(reader.includes('الأرقام محلية في مجموعة البيانات'),slug);
 if(slug==='ahmad')assert.ok(reader.includes('الأقسام 8–30 غير موجودة'));
 const words=hadithWords(first.text).filter(word=>word.length>3).slice(3,6).join(' ');
 const results=await html('/corpus?'+new URLSearchParams({collection:slug,q:words}));
 assert.ok(results.includes('data-hadith-number="1"'),`${slug} word search`);
 const section=corpus.split(`data-corpus-collection="${slug}"`)[1].split('</article>')[0];
 assert.ok(section.includes(new Intl.NumberFormat('ar-u-nu-latn').format(count)),`${slug} count`);
}
const home=await html('/explore?'+new URLSearchParams({q:'الدارمي 1'}));assert.ok(home.includes('/corpus/darimi/1'));
const old=await html('/corpus/bukhari/1');assert.ok(old.includes('data-ai-hadith-report="1"'));
console.log(JSON.stringify({collections:17,corpus_records:51111,new_records:14721,new_book_readers_and_word_search:'passed',number_and_book_alias_search:'passed',statistics_default_open:'passed',partial_coverage:'passed',existing_ai_reports:'preserved'}));
