import "server-only";
import { unstable_cache } from "next/cache";
import snapshot from "@/content/corpus-progress.json";
import { queryNeon, usesNeon } from "./neon";
import { normalize, collections } from "./research";
import type { LocalHadith } from "./corpus";
import type { CorpusProgress } from "./corpus-progress";

type Counts = typeof snapshot.counts;
type Book = { slug: string; title: string; counts: Counts };
const countKeys = Object.keys(snapshot.counts) as (keyof Counts)[];
const liveInventory = unstable_cache(async () => {
  const rows = await queryNeon<Counts & {slug: string; title: string}>("SELECT * FROM research.website_corpus_counts");
  const books: Book[] = rows.map(row => ({slug: row.slug, title: row.title,
    counts: Object.fromEntries(countKeys.map(key => [key, Number(row[key])])) as Counts}));
  books.sort((a,b) => Object.keys(collections).indexOf(a.slug) - Object.keys(collections).indexOf(b.slug));
  const counts = Object.fromEntries(countKeys.map(key => [key, books.reduce((n,b) => n+b.counts[key],0)])) as Counts;
  return {counts, collections: books, missing_collections: snapshot.missing_collections};
}, ["neon-corpus-inventory-v1"], { revalidate: 60 });

export async function readInventory() {
  return usesNeon() ? liveInventory() : snapshot;
}

type Row = {slug: string; source_number: string; original_data: LocalHadith; text: string;
 status: CorpusProgress["status"]; filtered: boolean; in_book: boolean; review: CorpusProgress["review"]};
export type CorpusResult = LocalHadith & {collection: string; progress: CorpusProgress};

export async function searchNeon({q,id,collection,status,page}: {q:string;id:string;collection:string;status:string;page:number}) {
  const values: unknown[] = [];
  const where = ["length(trim(text))>0"];
  const parameter = (value: unknown) => {values.push(value);return `$${values.length}`;};
  if (collection) where.push(`slug=${parameter(collection)}`);
  if (id) where.push(`source_number=${parameter(id)}`);
  for (const term of normalize(q).split(/\s+/).filter(Boolean)) where.push(`position(${parameter(term)} in normalized_text)>0`);
  if (status === "filtered") where.push("filtered");
  else if (status === "book") where.push("in_book");
  else if (status) where.push(`status=${parameter(status)}`);
  const condition = where.join(" AND ");
  const [count] = await queryNeon<{total:number}>(`SELECT count(*)::int AS total FROM research.website_hadiths WHERE ${condition}`, values);
  const total = Number(count.total), pages = Math.max(1,Math.ceil(total/15)), current = Math.min(pages,Math.max(1,page));
  const offset = parameter((current-1)*15);
  const rows = await queryNeon<Row>(`SELECT slug,source_number,original_data,text,status,filtered,in_book,review FROM research.website_hadiths WHERE ${condition} ORDER BY CASE slug ${Object.keys(collections).map((key,i)=>`WHEN '${key}' THEN ${i}`).join(" ")} ELSE 99 END,source_ordinal LIMIT 15 OFFSET ${offset}`, values);
  const results: CorpusResult[] = rows.map(row=>({...row.original_data,hadithnumber:Number(row.source_number),text:row.text,collection:row.slug,
    progress:{status:row.status,filtered:row.filtered,in_book:row.in_book,...(row.review?{review:row.review}:{})}}));
  return {results,total,pages,current};
}
