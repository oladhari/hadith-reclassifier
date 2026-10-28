// Read-only catalogue integration: public selection, deduplication and transcripts.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
const base = process.env.RESEARCH_TEST_URL || "http://127.0.0.1:3000";
const catalogue = JSON.parse(await readFile(new URL("../src/content/media-catalogue.json", import.meta.url), "utf8"));
const transcripts = JSON.parse(await readFile(new URL("../src/content/transcript-content.json", import.meta.url), "utf8"));
const archive = JSON.parse(await readFile(new URL("../src/content/archive-index.json", import.meta.url), "utf8"));
const collections = JSON.parse(await readFile(new URL("../src/content/media-collections.json", import.meta.url), "utf8"));
const visible = Object.values(catalogue).filter(row => row.visible && row.id === row.canonical_id);
assert.ok(visible.length > 0);
assert.equal(new Set(visible.map(row => row.canonical_id)).size, visible.length);
for (const row of visible) {
  assert.match(row.title, /[\u0600-\u06ff]/);
  assert.match(row.description, /[\u0600-\u06ff]/);
  assert.doesNotMatch(row.title, /^(?:IMG[ _-]?\d|merged|Image to PDF|صورة من مكتبة)/i);
  assert.doesNotMatch(row.description, /https?:\/\/(?:t\.me|telegram\.me)/i);
}
async function html(path) {
  const response = await fetch(base + path, { signal: AbortSignal.timeout(45000) });
  assert.equal(response.status, 200, path);
  return response.text();
}
const home = await html("/library");
assert.ok(home.includes('class="asset-description"'));
assert.ok(home.includes('name="topic"') && home.includes('name="scope"'));
assert.equal((home.match(/class="asset-card"/g) || []).length, Math.min(24, visible.length));
const duplicate = Object.values(catalogue).find(row => row.visible && row.id !== row.canonical_id);
assert.ok(duplicate, "A duplicate occurrence should remain resolvable");
const redirected = await fetch(`${base}/library/${duplicate.id}`, { redirect: "manual" });
assert.equal(redirected.status, 308);
assert.ok(redirected.headers.get("location").endsWith(`/library/${duplicate.canonical_id}`));
const hidden = Object.values(catalogue).find(row => !row.visible);
assert.ok(hidden);
assert.equal((await fetch(`${base}/library/${hidden.id}`)).status, 404);
for (const scope of ["full_book", "excerpt"]) {
  const expected = visible.filter(row => row.scope === scope);
  assert.ok(expected.length > 0);
  const page = await html(`/library?scope=${scope}`);
  assert.ok(page.includes(`data-result-count="${expected.length}"`));
}
const normalizedSearches = await Promise.all(["عائشة", "عَائِشَة"].map(query => html(`/library?q=${encodeURIComponent(query)}`)));
assert.equal(normalizedSearches[0].match(/data-result-count="(\d+)"/)?.[1], normalizedSearches[1].match(/data-result-count="(\d+)"/)?.[1]);
const audio = visible.find(row => archive.find(item => item.id === row.id)?.kind === "audio" && transcripts[row.id]);
assert.ok(audio);
const words = transcripts[audio.id].split(/\s+/).filter(Boolean);
const query = words.slice(Math.floor(words.length / 2), Math.floor(words.length / 2) + 6).join(" ");
const search = await html(`/library?kind=audio&q=${encodeURIComponent(query)}`);
assert.ok(search.includes(`/library/${audio.id}`), "Speech must be searchable beyond the title");
const detail = await html(`/library/${audio.id}`);
assert.ok(detail.includes("transcript-panel") && detail.includes(`/transcripts/${audio.id}.vtt`));
const captions = await fetch(`${base}/transcripts/${audio.id}.vtt`);
assert.equal(captions.status, 200);
assert.match(await captions.text(), /^WEBVTT\n[\s\S]*-->/);
const topic = visible.find(row => row.topics.length)?.topics[0];
const expectedTopic = visible.filter(row => row.topics.includes(topic));
const topicHtml = await html(`/library?topic=${topic}`);
assert.ok(topicHtml.includes(`data-result-count="${expectedTopic.length}"`));
const themed = await html(`/topics/${topic}`);
assert.ok(themed.includes("من المكتبة: كتب ومقاطع ومصادر مرتبطة"));
const chapterItem = visible.find(row => row.chapters.length);
assert.ok(chapterItem);
const chapter = chapterItem.chapters[0];
const clip = await html(`/library/${chapterItem.id}?start=${chapter.start}&end=${chapter.end}`);
assert.ok(clip.includes(chapter.title));
assert.ok(clip.includes("عرض التسجيل الكامل"));
for (const collection of Object.values(collections)) {
  const detail = await html(`/library/${collection.canonical_id}`);
  assert.ok(detail.includes(collection.asset_url));
  assert.ok(detail.includes("الأصول وترتيب الصفحات"));
  for (const id of collection.members.filter(id => id !== collection.canonical_id)) {
    const response = await fetch(`${base}/library/${id}`, { redirect: "manual" });
    assert.equal(response.status, 308);
    assert.ok(response.headers.get("location").endsWith(`/library/${collection.canonical_id}`));
    const search = await html(`/library?q=${id}`);
    assert.ok(search.includes(`href="/library/${collection.canonical_id}"`));
    assert.ok(!search.includes(`href="/library/${id}"`));
  }
  const file = await fetch(base + collection.asset_url);
  assert.equal(file.status, 200);
  const bytes = Buffer.from(await file.arrayBuffer());
  assert.equal(bytes.length, collection.asset_size);
  assert.equal(createHash("sha256").update(bytes).digest("hex"), collection.asset_sha256);
  const range = await fetch(base + collection.asset_url, { headers: { range: "bytes=0-127" } });
  assert.equal(range.status, 206);
  assert.deepEqual(Buffer.from(await range.arrayBuffer()), bytes.subarray(0, 128));
}
console.log(`Catalogue checks passed: ${visible.length} canonical listings, hidden materials, duplicate redirects, book/excerpt/theme filters, transcript search, Arabic captions and thematic playback sections.`);
