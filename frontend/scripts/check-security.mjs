// Bounded read-only probes against the authorized website. No timing attacks,
// destructive SQL, write attempts, password guessing, or load flooding.
import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
const base = process.env.RESEARCH_TEST_URL || "http://127.0.0.1:3110";
const results = [];
async function probe(path, expected = 200, init = {}) {
  const response = await fetch(base + path, { redirect: "manual", signal: AbortSignal.timeout(45000), ...init });
  const body = await response.text();
  assert.ok((Array.isArray(expected) ? expected : [expected]).includes(response.status), `${path}: ${response.status}`);
  assert.ok(!/NeonDbError|PostgresError|syntax error at or near|postgres(?:ql)?:\/\/[^\s]+@|-----BEGIN .*PRIVATE KEY/.test(body), `Internal error/secret exposed at ${path}`);
  results.push({ path, method: init.method || "GET", status: response.status, passed: true });
  return { response, body };
}
const { response: home, body: markup } = await probe("/");
for (const [name, expected] of [["x-content-type-options","nosniff"],["x-frame-options","SAMEORIGIN"],["referrer-policy","strict-origin-when-cross-origin"]]) assert.equal(home.headers.get(name), expected);
assert.ok(Number(home.headers.get("strict-transport-security")?.match(/max-age=(\d+)/)?.[1]) >= 31536000);
assert.ok(home.headers.get("permissions-policy")?.includes("camera=()"));
assert.equal(home.headers.get("x-powered-by"), null);
const csp = home.headers.get("content-security-policy") || "";
const nonce = csp.match(/'nonce-([^']+)'/)?.[1];
assert.ok(nonce && nonce.length >= 32);
assert.ok(csp.includes("'strict-dynamic'") && csp.includes("object-src 'none'") && csp.includes("form-action 'self'") && csp.includes("frame-ancestors 'self'"));
assert.ok(!csp.match(/script-src[^;]*'unsafe-inline'/) && !csp.includes("'unsafe-eval'"));
const scripts = [...markup.matchAll(/<script\b([^>]*)>/g)]; assert.ok(scripts.length > 0);
for (const script of scripts) assert.ok(script[1].includes(`nonce="${nonce}"`), "Rendered script lacks the response's nonce");
const second = await probe("/", 200, { headers: { "x-nonce": "attacker-chosen-nonce", "content-security-policy": "script-src * 'unsafe-inline'" } });
assert.notEqual(second.response.headers.get("content-security-policy")?.match(/'nonce-([^']+)'/)?.[1], nonce);
assert.ok(!second.response.headers.get("content-security-policy").includes("attacker-chosen-nonce"));
assert.match(home.headers.get("cache-control"), /private/); assert.match(home.headers.get("cache-control"), /no-store/);
for (const path of ["/library?q=a&q=b", "/corpus?q=a&q=b", "/explore?q=a&q=b", "/cases?q=a&q=b", "/library?page=-1", "/library?page=Infinity", "/library?page=10001", "/corpus?collection=unknown", "/corpus?id=" + encodeURIComponent("1' OR 1=1--"), "/library?__proto__[admin]=1", "/library?q=%00", "/library?q=" + "x".repeat(161), "/library/13?start=NaN", "/api/media/195?download=2"]) await probe(path, 400);
await probe("/library?q=a&q=b", 400, { headers: { "x-middleware-subrequest": "src/proxy:src/proxy:src/proxy:src/proxy:src/proxy" } });
await probe("/library?q=" + "x".repeat(5000), [414,431]);
const sqlPayloads = ["zzzaudit' OR 1=1--", "zzzaudit' UNION SELECT 'audit_marker'--", "zzzaudit'; SELECT 1--", "zzzaudit'/**/OR/**/'1'='1"];
for (const payload of sqlPayloads) {
  const { body } = await probe(`/corpus?collection=bukhari&q=${encodeURIComponent(payload)}`);
  assert.ok(!body.includes('class="hadith-record"'), "SQL-like search returned unexpected corpus records");
}
for (const payload of ['<script>window.__audit_xss=1</script>', '<img src=x onerror="window.__audit_xss=1">', '"><svg onload="window.__audit_xss=1">']) {
  const { body } = await probe(`/explore?q=${encodeURIComponent(payload)}`);
  assert.ok(!body.includes(payload), "Raw executable markup appeared in HTML");
}
for (const path of ["/.env", "/.env.local", "/.git/config", "/package.json", "/data/research/research.sqlite3", "/backend/app/core/config.py", "/api/video-review/export", "/api/video-review/decision", "/api/v1/ingest", "/api/v1/classifications/bulk-classify", "/_next/server/app/page.js", "/__nextjs_original-stack-frame"]) await probe(path, [404,403]);
for (const id of ["195%27%20OR%201%3D1", "..%2F.env", "%252e%252e%252f.env", "%00", "-1", "9999999999999999999999"]) await probe(`/api/media/${id}`, [400,404]);
await probe("/_next/image?url=https%3A%2F%2Fexample.invalid%2Faudit.png&w=64&q=75", [400,404]);
const asset = await probe("/api/media/195?url=https%3A%2F%2Fexample.invalid%2Faudit", 307);
assert.notEqual(new URL(asset.response.headers.get("location")).hostname, "example.invalid");
for (const path of ["/corpus", "/library", "/explore", "/api/media/195"]) await probe(path, 405, { method: "POST", headers: { "next-action": "invalid-audit-action", "Content-Type": "text/plain" }, body: "audit-marker" });
const retiredApi = await probe("/api/retired-audit", 404, { method: "POST", headers: { "next-action": "invalid-audit-action", "Content-Type": "application/json" }, body: "{" });
assert.match(retiredApi.response.headers.get("content-type"), /^text\/plain/);
const canonicalApi = await probe("/api/v1/ingest/", 308, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{" });
assert.equal(new URL(canonicalApi.response.headers.get("location"), base).origin, new URL(base).origin);
for (const path of ["/api/v1/ingest", "/api/v1/classifications/classify", "/api/v1/classifications/bulk-classify"])
  await probe(path, 404, { method: "POST", headers: { "Content-Type": "application/json", "next-action": "invalid-audit-action" }, body: "{" });
for (const method of ["PUT","PATCH","DELETE"]) await probe("/library", 405, { method });
const report = { base, checks: results.length, passed: true, scope: "bounded non-destructive request probes plus CSP/nonce/header assertions", results };
if (process.env.AUDIT_OUTPUT) await writeFile(process.env.AUDIT_OUTPUT, JSON.stringify(report, null, 2) + "\n");
console.log(`Security integration checks passed: ${results.length} requests; SQL-like inputs, escaped markup, CSP nonces, parameter pollution, private paths, SSRF surface and read-only methods.`);
