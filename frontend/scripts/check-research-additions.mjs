import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const root = new URL('../src/content/', import.meta.url);
const catalogue = JSON.parse(await readFile(new URL('media-catalogue.json', root), 'utf8'));
const bundles = JSON.parse(await readFile(new URL('research-bundles.json', root), 'utf8')).bundles;
const documents = JSON.parse(await readFile(new URL('document-texts.json', root), 'utf8'));
const base = process.env.RESEARCH_TEST_URL || 'http://127.0.0.1:3015';
async function html(path) {
 const response = await fetch(base + path, { signal: AbortSignal.timeout(45000) });
 assert.equal(response.status, 200, path); return response.text();
}
assert.equal(bundles.length,30);
const index = await html('/themes');
for (const b of bundles) assert.ok(index.includes(`/themes/${b.slug}`));
for (const slug of ['basra-treasury','adult-nursing','amash','abu-bakra']) {
 const b=bundles.find(b=>b.slug===slug); const text=await html(`/themes/${slug}`);
 assert.ok(text.includes(`data-theme-explanation="${slug}"`));assert.ok(text.includes(b.explanation));
 for (const id of b.items.slice(0,18)) assert.ok(text.includes(`/library/${id}`));
}
const newPdfs = Object.values(catalogue).filter(e=>e.visible && e.id===e.canonical_id && e.id>=1000000 && e.page_count);
assert.equal(newPdfs.length,14);
for (const entry of newPdfs) {
 const text=await html(`/library/${entry.id}`);
 assert.ok(text.includes(`data-source-commentary="${entry.id}"`));
 assert.ok(text.includes(`data-document-text="${entry.id}"`));
 const response=await fetch(`${base}/api/media/${entry.id}`,{redirect:'manual',signal:AbortSignal.timeout(30000)});
 assert.equal(response.status,307);assert.match(response.headers.get('location'),/\/imports\/muawiya4n\/originals\/sha256\/[a-f0-9]{64}$/);
}
const doc=newPdfs.find(e=>documents[e.id]?.text.length>500);
const query=documents[doc.id].text.split(/\s+/).filter(w=>/^[\u0600-\u06ff]{3,}$/.test(w)).slice(12,16).join(' ');
assert.ok(query);const search=await html(`/library?section=all&q=${encodeURIComponent(query)}`);
assert.ok(search.includes(`/library/${doc.id}`),'OCR text must be searchable beyond metadata');
const duplicate=Object.values(catalogue).find(e=>e.id>=1000000 && e.visible && e.id!==e.canonical_id);
const redirect=await fetch(`${base}/library/${duplicate.id}`,{redirect:'manual'});assert.equal(redirect.status,308);
assert.ok(redirect.headers.get('location').endsWith(`/library/${duplicate.canonical_id}`));
assert.equal((await fetch(`${base}/themes/not-a-theme`)).status,404);
console.log(JSON.stringify({thematic_collections:bundles.length,new_pdfs_checked:newPdfs.length,ocr_search:'passed',canonical_redirect:'passed'}));
