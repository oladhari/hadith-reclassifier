import assert from 'node:assert/strict';
const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';
async function html(path){const r=await fetch(base+path,{signal:AbortSignal.timeout(60000)});assert.equal(r.status,200,path);return r.text();}
const page=await html('/library?section=books');
assert.equal((page.match(/data-reference-book-id="927"/g)||[]).length,1);
assert.ok(page.includes('data-book-card-count="26"'));assert.ok(page.includes('9 مجلدات'));
for(const key of ['rijal','hadith','history','uthman','creed','research'])assert.ok(page.includes(`data-book-card-theme="${key}"`));
for(const id of [909,910,911,912,913,914,915])assert.ok(!page.includes(`href="/library/${id}"`));
const creed=await html('/library?section=books&theme=creed');assert.ok(creed.includes('data-book-card-count="1"'));assert.ok(creed.includes('data-reference-book-id="927"'));assert.ok(!creed.includes('data-book-card-theme="rijal"'));
for(const q of ['منهاج','الجزء الثاني'])assert.ok((await html('/library?section=books&q='+encodeURIComponent(q))).includes('data-reference-book-id="927"'));
for(const id of [927,2170,3722,3310,8609,1692,12579])assert.equal((await fetch(base+`/thumbnails/reference-${id}.webp`)).status,200);
const volume=await html('/library/909');assert.ok(volume.includes('/library/references/927?file=part-02'));
console.log('Book thumbnails: six themes, 26 grouped works, one nine-volume Minhaj card, search and preserved volume links passed.');
