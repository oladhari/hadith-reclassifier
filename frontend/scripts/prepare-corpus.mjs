// Prepare only public Arabic corpus files; credentials and research databases are never bundled.
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
if (process.env.RESEARCH_READ_DATABASE_URL) {
  console.log("Using the hosted research database; corpus file preparation is unnecessary.");
  process.exit(0);
}
const books = ["bukhari", "muslim", "malik", "abudawud", "tirmidhi", "nasai", "ibnmajah"];
const output = path.resolve(".corpus");
await mkdir(output, { recursive: true });
for (const book of books) {
  const filename = `ara-${book}.json`;
  let content;
  try { content = await readFile(path.resolve(process.env.HADITH_DATA_DIR || "../data/hadiths", filename), "utf8"); }
  catch {
    if (process.env.CORPUS_DATA_BASE_URL) {
      const response = await fetch(`${process.env.CORPUS_DATA_BASE_URL.replace(/\/$/, "")}/${filename}`);
      if (!response.ok) throw new Error(`Unable to prepare ${book}: HTTP ${response.status}`);
      content = await response.text();
    } else { content = await readFile(path.join(output, filename), "utf8"); }
  }
  const parsed = JSON.parse(content);
  if (!Array.isArray(parsed.hadiths) || !parsed.hadiths.length) throw new Error(`Invalid corpus file: ${book}`);
  await writeFile(path.join(output, filename), content);
}
console.log(`Prepared ${books.length} Arabic hadith collections.`);
