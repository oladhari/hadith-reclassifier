// Prepare only checksum-verified public Arabic files; no DB/storage credentials enter the bundle.
import { mkdir,readFile,writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { gunzipSync } from "node:zlib";
import path from "node:path";
if (process.env.RESEARCH_DATA_SOURCE==="neon"&&process.env.RESEARCH_READ_DATABASE_URL) {
 console.log("Explicit live corpus mode; local corpus preparation skipped.");process.exit(0);
}
const seed=JSON.parse(await readFile(new URL("../src/content/editorial-seed.json",import.meta.url),"utf8"));
const manifest=JSON.parse(await readFile(new URL("../src/content/corpus-assets.json",import.meta.url),"utf8"));
const output=path.resolve(".corpus");await mkdir(output,{recursive:true});
const sha=bytes=>createHash("sha256").update(bytes).digest("hex");
for(const name of Object.keys(seed.collections)){
 const asset=manifest.collections[name];if(!asset)throw new Error(`No published corpus snapshot: ${name}`);
 const filename=`ara-${name}.json`;let content;
 for(const file of [path.resolve(process.env.HADITH_DATA_DIR||"../data/hadiths",filename),path.join(output,filename)]){
  try{const local=await readFile(file);if(sha(local)===asset.sha256){content=local;break;}}catch{}
 }
 if(!content){
  const base=process.env.MEDIA_PUBLIC_BASE_URL?.replace(/\/$/,"");if(!base||!/^https:\/\//.test(base))throw new Error("Public media base is needed to prepare corpus snapshots");
  if(!/^site-snapshots\/corpus\/sha256\/[a-f0-9]{64}\.json\.gz$/.test(asset.key))throw new Error("Invalid corpus snapshot key");
  const response=await fetch(`${base}/${asset.key}`,{signal:AbortSignal.timeout(120000),redirect:"error"});
  if(!response.ok)throw new Error(`Corpus snapshot ${name}: HTTP ${response.status}`);
  const compressed=Buffer.from(await response.arrayBuffer());if(compressed.length!==asset.gzip_bytes||sha(compressed)!==asset.gzip_sha256)throw new Error(`Compressed corpus checksum mismatch: ${name}`);
  content=gunzipSync(compressed,{maxOutputLength:64*1024*1024});
 }
 if(content.length!==asset.bytes||sha(content)!==asset.sha256)throw new Error(`Corpus checksum mismatch: ${name}`);
 const parsed=JSON.parse(content);if(!Array.isArray(parsed.hadiths)||parsed.hadiths.length!==asset.records)throw new Error(`Corpus record mismatch: ${name}`);
 await writeFile(path.join(output,filename),content);
}
console.log(`Prepared ${Object.keys(seed.collections).length} verified public Arabic corpus snapshots (no Neon reads).`);
