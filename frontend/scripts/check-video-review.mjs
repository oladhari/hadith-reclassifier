import assert from "node:assert/strict";
const base = process.env.RESEARCH_TEST_URL || "http://127.0.0.1:3110";
const code = process.env.VIDEO_REVIEW_TEST_CODE;
assert.ok(code, "Set VIDEO_REVIEW_TEST_CODE without printing the access code");
const page = await fetch(base + "/review/videos");
const publicHtml = await page.text();
assert.ok(publicHtml.includes('name="code"'));
assert.ok(!publicHtml.includes('data-review-video='));
assert.equal((await fetch(base + "/api/video-review/export")).status, 401);
const headers = { Origin: base, "Content-Type": "application/json" };
assert.equal((await fetch(base + "/api/video-review/decision", { method: "POST", headers, body: "{}" })).status, 401);
assert.equal((await fetch(base + "/api/video-review/session", { method: "POST", headers: { Origin: "https://example.invalid" }, body: new URLSearchParams({ code }) })).status, 403);
const wrong = await fetch(base + "/api/video-review/session", { method: "POST", redirect: "manual", headers: { Origin: base }, body: new URLSearchParams({ code: "invalid" }) });
assert.equal(wrong.status, 303);
assert.ok(!wrong.headers.get("set-cookie"));
const login = await fetch(base + "/api/video-review/session", { method: "POST", redirect: "manual", headers: { Origin: base }, body: new URLSearchParams({ code }) });
assert.equal(login.status, 303);
const setCookie = login.headers.get("set-cookie");
assert.match(setCookie, /HttpOnly/i); assert.match(setCookie, /SameSite=strict/i);
const cookie = setCookie.split(";")[0];
const privateHeaders = { ...headers, Cookie: cookie };
const privatePage = await fetch(base + "/review/videos", { headers: { Cookie: cookie } });
const html = await privatePage.text();
assert.ok(html.includes("data-review-video=") && html.includes("إخفاء من الموقع"));
assert.match(privatePage.headers.get("cache-control") || "", /private|no-store/);
assert.equal((await fetch(base + "/api/video-review/decision", { method: "POST", headers: { ...privateHeaders, Origin: "https://example.invalid" }, body: "{}" })).status, 403);
assert.equal((await fetch(base + "/api/video-review/decision", { method: "POST", headers: privateHeaders, body: JSON.stringify({ id: 3, decision: "hide", platform: "unknown", note: "", revision: 0 }) })).status, 400);
const snapshot = await (await fetch(base + "/api/video-review/export", { headers: { Cookie: cookie } })).json();
assert.equal(new Set(snapshot.items.map(row => row.id)).size, snapshot.items.length);
assert.ok(snapshot.items.length > 0);
if (process.env.REVIEW_TEST_MUTATIONS === "1") {
  const item = snapshot.items.find(row => row.decision === "pending" && row.revision === 0 && row.visible);
  assert.ok(item, "Only test an untouched, currently public review item");
  let hidden;
  try {
    assert.equal((await fetch(`${base}/library/${item.id}`)).status, 200);
    const save = await fetch(base + "/api/video-review/decision", { method: "POST", headers: privateHeaders,
      body: JSON.stringify({ id: item.id, decision: "hide", platform: item.platform, note: item.note, revision: item.revision }) });
    assert.equal(save.status, 200); hidden = await save.json();
    assert.equal((await fetch(`${base}/library/${item.id}`)).status, 404);
    assert.equal((await fetch(`${base}/api/media/${item.id}`, { redirect: "manual" })).status, 404);
    assert.equal((await fetch(`${base}/api/media/${item.id}`, { redirect: "manual", headers: { Cookie: cookie } })).status, 307);
    const source = await (await fetch(`${base}/sources/${item.id}`)).text();
    assert.ok(!source.includes(`src="/api/media/${item.id}"`));
    const stale = await fetch(base + "/api/video-review/decision", { method: "POST", headers: privateHeaders,
      body: JSON.stringify({ id: item.id, decision: "keep", platform: item.platform, note: item.note, revision: item.revision }) });
    assert.equal(stale.status, 409);
    const saved = await (await fetch(base + "/api/video-review/export", { headers: { Cookie: cookie } })).json();
    assert.equal(saved.items.find(row => row.id === item.id).decision, "hide");
    assert.ok(saved.history.some(row => row.id === item.id));
  } finally {
    if (hidden) {
      const restore = await fetch(base + "/api/video-review/decision", { method: "POST", headers: privateHeaders,
        body: JSON.stringify({ id: item.id, decision: item.decision, platform: item.platform, note: item.note, revision: hidden.revision }) });
      assert.equal(restore.status, 200, "Restore the temporary visibility test");
      assert.equal((await fetch(`${base}/library/${item.id}`)).status, 200);
    }
  }
}
const logout = await fetch(base + "/api/video-review/session", { method: "POST", redirect: "manual", headers: { Origin: base, Cookie: cookie }, body: new URLSearchParams({ logout: "1" }) });
assert.match(logout.headers.get("set-cookie"), /Max-Age=0/i);
console.log(`Private review checks passed: ${snapshot.items.length} videos, login, permissions, origin checks, history${process.env.REVIEW_TEST_MUTATIONS === "1" ? ", persistent hide/restore, stale-write protection" : ""}.`);
