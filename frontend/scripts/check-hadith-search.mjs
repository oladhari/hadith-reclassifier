import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { latinDigits,hadithNumber,parseHadithQuery,hadithWords } from '../src/lib/hadith-query.ts';
assert.equal(latinDigits('١٢٣ ۱۲۳'),'123 123');assert.equal(hadithNumber('٠٠١'),'1');
for (const q of ['123','١٢٣','۱۲۳','#123','حديث رقم 123','رقم ١٢٣']) assert.deepEqual(parseHadithQuery(q),{q:'',id:'123',collection:''});
assert.deepEqual(parseHadithQuery('البخاري ١'),{q:'',id:'1',collection:'bukhari'});
assert.deepEqual(parseHadithQuery('صحيح مسلم: الإيمان'),{q:'الإيمان',id:'',collection:'muslim'});
assert.equal(hadithNumber("1' OR 1=1"),'');assert.equal(hadithNumber('Infinity'),'');
assert.deepEqual(hadithWords('«إِنَّمَا الأَعْمَالُ، بِالنِّيَّاتِ»'),['انما','الاعمال','بالنيات']);
const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';
async function html(path){const response=await fetch(base+path,{signal:AbortSignal.timeout(60000)});assert.equal(response.status,200,path);return response.text();}
const home=await html('/');assert.match(home,/<form[^>]+action="\/explore"/);
const main=await html('/explore?'+new URLSearchParams({q:'إنما الأعمال بالنيات'}));
assert.ok(main.includes('data-main-hadith-search'));assert.ok(main.includes('/corpus/bukhari/1'));
assert.ok(main.indexOf('data-main-hadith-search')<main.indexOf('ملفات مرتبطة'));
const latin=await html('/explore?q=123'), eastern=await html('/explore?q='+encodeURIComponent('١٢٣'));
assert.equal(latin.match(/data-hadith-result-count="(\d+)"/)?.[1],eastern.match(/data-hadith-result-count="(\d+)"/)?.[1]);
assert.ok(Number(latin.match(/data-hadith-result-count="(\d+)"/)?.[1])>0);
for(const path of ['/explore?q='+encodeURIComponent('البخاري 1'),'/corpus?q=1','/corpus?id='+encodeURIComponent('١'),'/corpus?q='+encodeURIComponent('«إنما الأعمال، بالنيات»')]){
 const page=await html(path);assert.ok(page.includes('/corpus/bukhari/1'),path);
}
const corpus=await html('/corpus');assert.ok(corpus.indexOf('id="corpus-search"')<corpus.indexOf('data-corpus-stat='));
assert.equal((corpus.match(/class="hadith-record"/g)||[]).length,0);
assert.ok((await html('/corpus?collection=bukhari')).includes('/corpus/bukhari/1'));
const first=JSON.parse(await readFile(new URL('../../data/hadiths/ara-bukhari.json',import.meta.url),'utf8')).hadiths[0];
const escape=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#x27;');
const reader=await html('/corpus/bukhari/1');assert.ok(reader.includes(escape(first.text)));assert.ok(reader.includes('مرجع الرواية'));
const alias=await fetch(base+'/corpus/bukhari/'+encodeURIComponent('١'),{redirect:'manual'});assert.equal(alias.status,308);assert.ok(alias.headers.get('location').endsWith('/corpus/bukhari/1'));
for(const path of ['/corpus/no-book/1','/corpus/bukhari/99999999'])assert.equal((await fetch(base+path)).status,404,path);
const old=await fetch(base+'/search?q=123',{redirect:'manual'});assert.ok([307,308].includes(old.status));assert.ok(old.headers.get('location').includes('/corpus?q=123'));
assert.equal((await fetch(base+'/corpus?status=accepted')).status,200);
console.log(JSON.stringify({homepage_hadith_results:'passed',word_and_number_search:'passed',both_digit_sets:'passed',direct_reader_and_references:'passed',legacy_search:'passed'}));
