import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
const base = process.env.RESEARCH_TEST_URL || "http://127.0.0.1:3015";
const read = async name => JSON.parse(await readFile(new URL(`../src/content/${name}.json`, import.meta.url), "utf8"));
const [catalogue, archive, summary, thumbs] = await Promise.all([read("media-catalogue"), read("archive-index"), read("tiktok-collection"), read("thumbnails")]);
const rows = Object.values(catalogue).filter(row => row.source_account === "brad2557wtn" && row.id >= 2_000_000);
assert.equal(rows.length, summary.visible_records);
assert.equal(summary.discovered, rows.length + summary.previously_hidden);
const visible = Object.values(catalogue).filter(row => row.source_account === "brad2557wtn" && row.visible && row.id === row.canonical_id);
const videos = visible.filter(row => archive.find(a => a.id === row.id)?.kind === "video");
const audio = visible.filter(row => archive.find(a => a.id === row.id)?.kind === "audio");
assert.equal(videos.length, summary.video); assert.equal(audio.length, summary.audio);
assert.equal(new Set(visible.map(row => row.title)).size, visible.length, "Titles should distinguish independent posts");
for (const row of rows) {
  assert.match(row.title, /[\u0600-\u06ff]/);
  assert.ok(row.description && !row.has_transcript);
  assert.match(row.source_url, /^https:\/\/www\.tiktok\.com\/@brad2557wtn\/video\/\d+$/);
  for (const post of row.source_posts) assert.match(post.url, /^https:\/\/www\.tiktok\.com\/@brad2557wtn\/video\/\d+$/);
  const asset = archive.find(a => a.id === row.id); assert.ok(asset);
  assert.ok(asset.object_key.startsWith("imports/tiktok/brad2557wtn/objects/"));
  if (row.visible && row.id === row.canonical_id && asset.kind === "video") assert.ok(thumbs[row.id]);
}
for (const section of ["video", "audio"]) {
  const response = await fetch(`${base}/library?section=${section}&q=brad2557wtn`); assert.equal(response.status, 200);
  const html = await response.text(); assert.ok(html.includes(`data-result-count="${summary[section]}"`));
  assert.equal((html.match(/class="asset-card(?: [^"]*)?"/g) || []).length, Math.min(24, summary[section]));
}
const escaped = s => s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#x27;");
for (const row of [videos[0], videos.at(-1), ...audio]) {
  const response = await fetch(`${base}/library/${row.id}`); assert.equal(response.status, 200);
  const html = await response.text(); assert.ok(html.includes(escaped(row.title)));
  assert.ok(html.includes(row.source_url) && html.includes("وصف الناشر والمصدر الأصلي"));
  assert.ok(!html.includes(`/sources/${row.id}`));
  const media = await fetch(`${base}/api/media/${row.preferred_media_id || row.id}`, { redirect: "manual" }); assert.equal(media.status, 307);
  const remote = media.headers.get("location"); assert.equal(new URL(remote).hostname, "media.albaalaagh.com");
  const bytes = await fetch(remote, { headers: { Range: "bytes=0-1023" } }); assert.equal(bytes.status, 206);
  assert.equal((await bytes.arrayBuffer()).byteLength, 1024);
}
for (const row of rows.filter(row => row.visible && row.id !== row.canonical_id)) {
  const response = await fetch(`${base}/library/${row.id}`, { redirect: "manual" }); assert.equal(response.status, 308);
  assert.ok(response.headers.get("location").endsWith(`/library/${row.canonical_id}`));
  const html = await (await fetch(`${base}/library/${row.canonical_id}`)).text();
  assert.ok(html.includes(row.source_url), "Merged occurrence source remains visible");
}
const last = await fetch(`${base}/library?section=video&q=brad2557wtn&page=${Math.ceil(videos.length / 24)}`);
assert.equal(last.status, 200); assert.ok((await last.text()).replaceAll(/<!--.*?-->/g, "").includes(`صفحة ${Math.ceil(videos.length / 24)}`));
console.log(`TikTok collection passed: ${videos.length} videos, ${audio.length} audio, original source captions, search, pagination, duplicate redirects and R2 byte-range playback.`);
