// Integration checks against a running local research website; no AI or database writes.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
const base = process.env.RESEARCH_TEST_URL || "http://127.0.0.1:3000";
async function page(url, expected) {
  const r = await fetch(base + url);
  assert.equal(r.status, 200, url);
  const text = (await r.text()).replace(/<!--[\s\S]*?-->/g, "");
  assert.doesNotMatch(
    text,
    /href=["\']https?:\/\/(?:t\.me|(?:www\.)?telegram\.me)\//i,
    `${url}: public references must stay on the website`,
  );
  assert.ok(text.includes(expected), `${url}: missing expected content`);
  return text;
}
const home = await page("/", "لكلّ حُجّةٍ أصل");
assert.doesNotMatch(
  home,
  /[\u0660-\u0669\u06f0-\u06f9]/,
  "Interface digits must use 123",
);
assert.ok(home.includes("سلمت منها أيدينا"));
assert.ok(!home.includes("نطاق الفحص"));
assert.ok(!home.includes("حديث عمار بن ياسر"));
for (const slug of [
  "uthman",
  "camel",
  "allegiance",
  "siffin",
  "virtues",
  "narrators",
])
  assert.ok(home.includes(`/topics/${slug}`), `Missing primary topic: ${slug}`);
const themes = JSON.parse(
  await readFile(
    new URL("../src/content/archive-themes.json", import.meta.url),
    "utf8",
  ),
);
assert.equal(themes.totalPosts, 2477);
assert.equal(themes.textPosts, 1113);
assert.equal(themes.scope, "telegram_text_and_captions_only");
assert.equal(themes.topics.length, 8);
for (const group of [...themes.topics, ...Object.values(themes.cases)]) {
  assert.equal(group.postCount, group.posts.length);
  assert.equal(new Set(group.posts.map((p) => p.id)).size, group.posts.length);
  assert.equal(
    new Set(group.posts.map((p) => p.normalizedTextHash)).size,
    group.distinctTextCount,
  );
}
for (const slug of Object.keys(themes.cases))
  await page(`/cases/${slug}`, "حالة البحث");
const overview = await page("/topics", "المحاور الرئيسية");
assert.ok(!overview.includes("كيف استخرجنا"));
const topicPage = await page("/topics/camel", "الأدلة وصفحات الكتب");
assert.ok(topicPage.includes("/api/media/220"));
assert.ok(topicPage.includes("/api/media/25"));
assert.ok(!topicPage.includes("/api/media/1316"), "Unrelated shirt evidence must not leak into camel topic");
const source = await page("/sources/195", "نزهة النظر");
assert.ok(source.includes("/api/media/195"));
assert.ok(source.includes("/api/media/196"));
assert.ok(source.includes("رفع الحاجب"));
const shirt = await page("/sources/1315", "مرجع داخل الموسوعة");
assert.ok(shirt.includes("/api/media/1315"));
assert.ok(shirt.includes("/api/media/1316"));
const grouped = await page("/sources/219", "مرجع داخل الموسوعة");
for (const id of [219, 220, 221])
  assert.ok(grouped.includes(`/api/media/${id}`));
const studies = JSON.parse(await readFile(new URL("../src/content/case-studies.json", import.meta.url), "utf8"));
const seed = JSON.parse(await readFile(new URL("../src/content/editorial-seed.json", import.meta.url), "utf8"));
const archiveIndex = new Map(JSON.parse(await readFile(new URL("../src/content/archive-index.json", import.meta.url), "utf8")).map(item => [item.id, item]));
const selected = JSON.parse(await readFile(new URL("../src/content/public-evidence.json", import.meta.url), "utf8"));
const catalogue = JSON.parse(await readFile(new URL("../src/content/media-catalogue.json", import.meta.url), "utf8"));
assert.deepEqual(Object.keys(studies).sort(), Object.keys(themes.cases).sort());
assert.deepEqual(Object.keys(studies).sort(), seed.cases.map(item => item.slug).sort());
for (const [slug, study] of Object.entries(studies)) {
  const html = await page(`/cases/${slug}`, "شرح الحجة وأدلتها");
  assert.ok(html.includes(study.finding), slug);
  assert.doesNotMatch(JSON.stringify(study), /القناة/u, `${slug}: speak in the website's editorial voice`);
  const evidence = study.sections.flatMap(section => section.evidence || []);
  const ids = new Set(evidence.map(item => item.id));
  for (const id of selected.cases[slug] || []) assert.ok(ids.has(id), `${slug}: missing existing evidence ${id}`);
  for (const { id, page: pdfPage = 1, highlights } of evidence) {
    const target = catalogue[id]?.visible ? `/library/${catalogue[id].canonical_id}` : `/sources/${id}#media-source-${id}`;
    assert.ok(html.includes(`href="${target}"`), `${slug}: missing evidence link ${target}`);
    const kind = archiveIndex.get(id)?.kind;
    if (kind === "pdf" || kind === "image") {
      assert.ok(highlights?.length, `${slug}: no highlighted passage for evidence ${id}`);
      for (const { left, top, width, height } of highlights) {
        assert.ok([left, top, width, height].every(Number.isFinite));
        assert.ok(left >= 0 && top >= 0 && width > 0 && height > 0 && left + width <= 100 && top + height <= 100,
          `${slug}: highlight extends outside evidence ${id}`);
      }
      const original = `/api/media/${id}${kind === "pdf" ? `#page=${pdfPage}` : ""}`;
      const start = html.indexOf(`id="evidence-${id}"`);
      const card = html.slice(start, html.indexOf('class="case-preview-panel"', start));
      assert.match(card, /aria-expanded="false"/, `${slug}: evidence ${id} should start collapsed`);
      assert.ok(card.includes(`href="${original}" target="_blank"`), `${slug}: missing original in new tab ${id}`);
      if (kind === "pdf") await readFile(new URL(`../public/evidence/cases/${id}-${pdfPage}.webp`, import.meta.url));
    }
  }
  for (const passage of study.passages || []) {
    assert.ok(html.indexOf(passage.chain) < html.indexOf('id="archive-matches"'), slug);
    if (passage.corpus) assert.ok(html.includes(`href="/corpus/${passage.corpus.collection}/${passage.corpus.number}"`));
  }
}
const sharedPage = slug => studies[slug].sections.flatMap(section => section.evidence || []).find(item => item.id === 942);
assert.equal(sharedPage("hawab").page, sharedPage("siffin").page);
assert.notDeepEqual(sharedPage("hawab").highlights, sharedPage("siffin").highlights);
const hawab = await page("/cases/hawab", "إنكار القطان واحتمال الاختلاط");
assert.ok(hawab.includes("طريق ابن عباس"));
assert.ok(hawab.includes('href="/api/media/648#page=247"'));
assert.ok(hawab.includes('href="/api/media/760#page=2"'));
const collectedHawab = await page("/sources/858", "موضع الشاهد في القضية");
assert.ok(collectedHawab.includes('id="media-source-858"'));
assert.ok(collectedHawab.includes('href="/api/media/858#page=6"'));
const qays = await page("/library/1000348", "موضع الشاهد في القضية");
assert.ok(qays.includes("سمّى يحيى القطان حديث الحوأب"));
assert.ok(qays.includes('href="/cases/hawab#evidence-1000348"'));
const ghadir = await page("/cases/ghadir", "ملفات الغدير الثلاثة");
const ghadirLibrary = await page("/library/742", "موضع الشاهد في القضية");
for (const [id, pageNumber] of [[742, 2], [743, 8], [744, 3]]) {
  const href = `href="/api/media/${id}#page=${pageNumber}"`;
  assert.ok(ghadir.includes(href));
  assert.ok(ghadirLibrary.includes(href));
}
assert.equal((await fetch(base + "/sources/999999")).status, 404);
await page("/design/palette.html", "الخيار المطبّق حاليًا");
await page("/cases/hawab", "رواية كلاب الحوأب");
const ammar = await page(
  "/cases/ammar",
  "رواية «تقتله الفئة الباغية» في شأن عمار",
);
assert.ok(!ammar.includes("حديث عمار بن ياسر"));
await page("/design/mockup.html", "تصوّر موسوعة");
await page("/cases/innovation", "نزهة النظر");
await page("/cases/ammar", "لم يكتمل تحقيق");
await page(
  "/cases?" + new URLSearchParams({ q: "المُبْتَدِع" }),
  "رواية المبتدع",
);
await page(
  "/cases?" + new URLSearchParams({ q: "zzznomatch" }),
  "لا توجد قضية مطابقة",
);
await page("/library?kind=video", "فيديو");
const library = await page("/library?q=195", "مادة مطابقة");
assert.ok(library.includes("/library/195"));
const inventory = await page("/corpus", "ابحث عن حديث واقرأ نصّه");
assert.ok(!inventory.includes('class="hadith-record"'));
assert.ok(inventory.includes("مسند الإمام أحمد"));
const acceptedCorpus = await page("/corpus?status=accepted", "لا توجد روايات بهذه الحالة");
assert.ok(!acceptedCorpus.includes('class="hadith-record"'));
await page("/corpus?collection=bukhari&status=unreviewed", "hadith-record");
const first = await page(
  "/corpus?" + new URLSearchParams({ collection: "muslim", q: "الإيمان" }),
  "hadith-record",
);
const second = await page(
  "/corpus?" + new URLSearchParams({ collection: "muslim", q: "الايمان" }),
  "hadith-record",
);
const countPattern = /([0-9٠-٩٬,]+) سجلًا/;
assert.ok(first.match(countPattern), "Arabic result count must be present");
assert.equal(first.match(countPattern)?.[1], second.match(countPattern)?.[1]);
await page("/corpus?collection=bukhari&id=1", "مرجع الرواية");
assert.equal((await fetch(base + "/corpus?collection=not-a-collection&q=zzznomatch")).status, 400);
await page("/corpus?q=" + encodeURIComponent("' OR 1=1 --"), "لم نجد نصًا مطابقًا");
const methodology = await page("/methodology", "صريح القرآن الكريم هو الميزان الأول");
assert.ok(methodology.includes("الاعتقاد وصلة الرواية بالبدعة"));
assert.ok(methodology.includes("شرط الانتقاء في الرواة الموصوفين بالتشيع"));
assert.ok(methodology.includes("رواية عمار: الزيادة واختلاف النقل"));
assert.ok(!methodology.includes("https://t.me/"));
const filterProfile = JSON.parse(await readFile(new URL("../src/content/filter-layers.json", import.meta.url), "utf8"));
assert.equal(filterProfile.layers.length, 22);
assert.equal(filterProfile.layers[1].key, "quran_explicit");
assert.equal(filterProfile.layers[1].blocking, true);
await page("/sahih-othmani", "لم تُعتمد نسخة نهائية");
for (const url of ["/cases/not-found", "/library/999999", "/api/media/999999"])
  assert.equal((await fetch(base + url)).status, 404, url);
const archive = path.resolve(
  process.env.TELEGRAM_ARCHIVE_DIR || "../../telegram-archive/kkee9938",
);
const original = await readFile(path.join(archive, "media/195/attachment.jpg"));
for (const [range, start, end] of [
  ["bytes=0-63", 0, 63],
  ["bytes=64-127", 64, 127],
  ["bytes=-16", original.length - 16, original.length - 1],
]) {
  const r = await fetch(base + "/api/media/195", { headers: { range } });
  assert.equal(r.status, 206);
  assert.equal(
    r.headers.get("content-range"),
    `bytes ${start}-${end}/${original.length}`,
  );
  assert.deepEqual(
    Buffer.from(await r.arrayBuffer()),
    original.subarray(start, end + 1),
  );
}
for (const range of [
  "bytes=99999999999-",
  "bytes=5-2",
  "bytes=-0",
  "invalid",
  "bytes=0-1,4-5",
])
  assert.equal(
    (await fetch(base + "/api/media/195", { headers: { range } })).status,
    416,
    range,
  );
const full = await fetch(base + "/api/media/195?download=1");
assert.equal(full.status, 200);
assert.ok(full.headers.get("content-disposition").startsWith("attachment;"));
assert.deepEqual(Buffer.from(await full.arrayBuffer()), original);
console.log(
  "Research checks passed: routes, Arabic search, filters, empty/404 states, source bytes, range playback, and download integrity.",
);
