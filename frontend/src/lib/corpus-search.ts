import "server-only";
import { cache } from "react";
import { parseHadithQuery, hadithNumber, hadithWords } from "./hadith-query";
import { searchNeon, readNeonHadith, type CorpusResult } from "./live-corpus";
import { usesNeon } from "./neon";
import { readCollection } from "./corpus";
import { collections } from "./research";
import { corpusProgress, matchesState, recordProgress } from "./corpus-progress";
export async function searchHadiths(input: { q?: string; id?: string; collection?: string; status?: string; page?: number }) {
 const { q,id,collection } = parseHadithQuery(input.q || "",input.id || "",input.collection || "");
 const status=input.status || "";const page=input.page || 1;
 if(q.trim()&&!id&&!hadithWords(q).length)return {results:[] as CorpusResult[],total:0,pages:1,current:1,unavailable:[] as string[]};
 if (usesNeon()) return { ...await searchNeon({q,id,collection,status,page}), unavailable: [] as string[] };
 const names=collection ? Object.hasOwn(collections,collection) ? [collection] : [] : Object.keys(collections);
 const hasRecords=!status || status==="unreviewed" || Object.entries(corpusProgress.records).some(([key,value])=>(!collection||key.startsWith(`${collection}:`))&&matchesState(value,status));
 const batches=hasRecords ? await Promise.all(names.map(async name=>({name,rows:await readCollection(name).catch(()=>null)}))) : [];
 const words=hadithWords(q);
 const rows:CorpusResult[]=batches.flatMap(batch=>(batch.rows||[]).filter(h=>h.text?.trim()).map(h=>({...h,collection:batch.name,progress:recordProgress(batch.name,h.hadithnumber)})))
  .filter(h=>{
   if(id&&hadithNumber(String(h.hadithnumber))!==id&&hadithNumber(String(h.arabicnumber??""))!==id)return false;
   if(!matchesState(h.progress,status))return false;
   if(!words.length)return true;
   const text=hadithWords(h.text).join(" ");return words.every(word=>text.includes(word));
  });
 const total=rows.length,pages=Math.max(1,Math.ceil(total/15)),current=Math.min(pages,Math.max(1,page));
 return {results:rows.slice((current-1)*15,current*15),total,pages,current,unavailable:batches.filter(b=>!b.rows).map(b=>collections[b.name])};
}
export const readHadith=cache(async(collection:string,number:string):Promise<CorpusResult|null>=>{
 if (!Object.hasOwn(collections,collection)||!hadithNumber(number))return null;
 if(usesNeon())return readNeonHadith(collection,hadithNumber(number));
 const row=(await readCollection(collection)).find(h=>String(h.hadithnumber)===hadithNumber(number));
 return row?{...row,collection,progress:recordProgress(collection,row.hadithnumber)}:null;
});
