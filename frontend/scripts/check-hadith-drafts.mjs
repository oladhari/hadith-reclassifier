import assert from 'node:assert/strict';
const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';
async function html(path){const r=await fetch(base+path,{signal:AbortSignal.timeout(60000)});assert.equal(r.status,200,path);return r.text();}
const overview=await html('/corpus/analysis');
const count=Number(overview.match(/data-ai-draft-count="(\d+)"/)?.[1]);
assert.ok(count>0&&count<=200,'pilot count');
if(process.env.EXPECT_AI_DRAFT_COUNT)assert.equal(count,Number(process.env.EXPECT_AI_DRAFT_COUNT));
const first=await html('/corpus/bukhari/1');
assert.ok(first.includes('data-ai-hadith-report="1"'));
assert.equal((first.match(/data-ai-layer="L\d\d"/g)||[]).length,22);
assert.ok(first.includes('ليست اجتيازًا للطبقة')||first.includes('تحتاج أدلة ومراجعة'));
assert.ok(first.includes('ليست حكمًا')||first.includes('ليس حكمًا'));
assert.ok(first.includes('مرجع الرواية'));
const other=await html('/corpus/muslim/3');assert.ok(!other.includes('data-ai-hadith-report='));
const corpus=await html('/corpus');assert.ok(corpus.includes('/corpus/analysis'));assert.ok(corpus.includes('data-corpus-stat="accepted"'));
if(count===200){const last=await html('/corpus/bukhari/200');assert.ok(last.includes('data-ai-hadith-report="200"'));assert.equal((last.match(/data-ai-layer="L\d\d"/g)||[]).length,22);}
console.log(JSON.stringify({draft_count:count,all_22_layers:'passed',original_reader:'preserved',unrelated_collection:'unchanged',scholarly_stats:'separate'}));
