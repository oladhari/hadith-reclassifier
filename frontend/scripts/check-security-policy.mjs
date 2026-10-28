import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";
import { requestProblem, queryText } from "../src/lib/request-policy.ts";
let checks = 0;
function check(path, expected) {
  assert.equal(requestProblem(new URL(path, "https://example.test"))?.status || 200, expected, path);
  checks++;
}
for (const path of ["/", "/library?q=عثمان", "/corpus?collection=bukhari&id=1", "/corpus?id=1.25", "/library?section=excerpts&page=2", "/library/13?start=1.5&end=20", "/api/media/195?download=1", "/library?q=" + encodeURIComponent("zzzaudit' OR 1=1--"), "/explore?q=" + encodeURIComponent('<script>alert(1)</script>'), "/library?_rsc=abc123"]) check(path, 200);
for (const path of ["/library?q=a&q=b", "/corpus?collection=bukhari&collection=muslim", "/library?q=" + "a".repeat(161), "/cases?category=" + "a".repeat(81), "/library?page=-1", "/library?page=0", "/library?page=Infinity", "/library?page=10001", "/library?section=admin", "/corpus?collection=unknown", "/corpus?id=" + encodeURIComponent("1' OR 1=1"), "/corpus?status=__proto__", "/library?__proto__[admin]=1", "/library?constructor=admin", "/library?q=%00", "/library?q=%0d%0aheader", "/library/13?start=NaN", "/library/13?end=604801", "/api/media/195?download=2", "/library?q=" + Array(17).fill("a").join("+")]) check(path, 400);
check("/library?" + Array.from({length: 13}, (_,i) => `p${i}=v`).join("&"), 400);
check("/library?q=" + "x".repeat(5000), 414);
assert.equal(queryText(["a", "b"]), ""); assert.equal(queryText(null), ""); assert.equal(queryText("a".repeat(200)).length, 160); checks += 3;
let state = 42;
for (let i = 0; i < 2000; i++) {
  state = (1664525 * state + 1013904223) >>> 0;
  const value = String.fromCharCode(...Array.from({length: state % 190}, (_,n) => (state + n * 131) % 65536));
  const url = new URL("https://example.test/library"); url.searchParams.set(i % 2 ? "q" : "page", value);
  const result = requestProblem(url);
  assert.ok(result === null || [400,414].includes(result.status)); checks++;
}
const report = { checks, deterministic_fuzz_cases: 2000, result: "passed", scope: "Pure request validation; no network, database, or AI calls" };
if (process.env.AUDIT_OUTPUT) await writeFile(process.env.AUDIT_OUTPUT, JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report));
