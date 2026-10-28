// Read-only crawl of thematic pages and their evidence/source links.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
const base = process.env.RESEARCH_TEST_URL || "http://127.0.0.1:3110";
const read = async name => JSON.parse(await readFile(new URL(`../src/content/${name}.json`, import.meta.url), "utf8"));
const seed = await read("editorial-seed"), studies = await read("filter-case-studies"), visibility = await read("video-visibility");
const seen = new Set(), queue = new Map();
const enqueue = (path, from) => { if (!seen.has(path) && !queue.has(path)) queue.set(path, from); };
for (const path of ["/", "/topics", "/cases", "/methodology", "/library/1881", ...seed.topics.map(t => `/topics/${t.slug}`), ...seed.cases.map(c => `/cases/${c.slug}`)]) enqueue(path, "audit entry");
let proofCards = 0;
const errors = [];
while (queue.size) {
  const batch = [...queue.entries()].slice(0, 2);
  for (const [path] of batch) { queue.delete(path); seen.add(path); }
  const results = await Promise.allSettled(batch.map(async ([path, from]) => {
    const response = await fetch(base + path, { signal: AbortSignal.timeout(60000) });
    if (response.status !== 200) throw new Error(`${path}: ${response.status}; linked from ${from}`);
    const html = await response.text();
    if (path === "/methodology") {
      assert.ok(html.includes('class="proof-link"') && html.includes("فتح الدليل ومصادره"));
      assert.ok(html.includes('href="/sources/1881"'));
      assert.ok(!html.includes('href="/library/1881"'));
      proofCards = (html.match(/class="proof-link"/g) || []).length;
    }
    if (path === "/library/1881") {
      assert.ok(response.url.endsWith("/sources/1881"));
      assert.ok(html.includes('src="/api/media/1881"'));
    }
    const destination = new URL(response.url);
    for (const match of html.matchAll(/href="([^"<>]+)"/g)) {
      const value = match[1].replace(/&amp;/g, "&");
      if (value.startsWith("#")) {
        if (value.length > 1) assert.ok(html.includes(`id="${value.slice(1)}"`), `Missing section ${path}${value}`);
        continue;
      }
      if (!value.startsWith("/") || value.startsWith("//")) continue;
      const url = new URL(value, base);
      if (/^\/library\/\d+$/.test(url.pathname)) assert.ok(!visibility.hidden.includes(Number(url.pathname.split("/").pop())), `Rejected video linked from ${path}`);
      // Follow evidence links transitively, but don't recursively crawl search pagination or download originals.
      if (/^\/(?:library\/\d+|library\/albums\/[^/]+|sources\/\d+|topics(?:\/[^/]+)?|cases(?:\/[^/]+)?)$/.test(url.pathname)) enqueue(url.pathname, path);
      if (path === "/methodology" && url.pathname === "/corpus" && url.searchParams.has("id")) enqueue(url.pathname + url.search, path);
    }
    if (destination.pathname.startsWith("/sources/")) assert.ok(!html.includes('href="/library/1881"'));
  }));
  for (const result of results) if (result.status === "rejected") errors.push(result.reason.message);
  assert.ok(seen.size < 1500, "Unexpected crawl expansion");
}
assert.deepEqual(errors, [], errors.join("\n"));
assert.ok(proofCards >= studies.length);
console.log(`Proof link audit passed: ${seen.size} pages across all ${seed.topics.length} themes and ${seed.cases.length} cases; ${proofCards} clear proof cards; legacy 1881 link resolves; rejected videos remain excluded.`);
