import "server-only";
import { unstable_cache } from "next/cache";
import { queryNeon, usesNeon } from "./neon";
export type DraftLayer = {code:string;title:string;status:"text_observation"|"needs_evidence"|"methodology_pending";analysis:string;quotes:string[];next_step:string};
export type HadithDraft = {collection:string;source_number:string;model:string;profile_key:string;profile_version:number;created_at:string;report:{summary:string;report_type:string;themes:string[];layers:DraftLayer[]}};
export type DraftSummary = Omit<HadithDraft,"report"> & {summary:string};
export const draftStatusNames = {text_observation:"ملاحظة من النص؛ ليست اجتيازًا للطبقة",needs_evidence:"تحتاج أدلة ومراجعة",methodology_pending:"تحتاج تحرير القاعدة المنهجية"};
export const readDraftSummaries = unstable_cache(async ():Promise<DraftSummary[]> => {
 if(!usesNeon()) return [];
 return queryNeon<DraftSummary>("SELECT collection,source_number,model,profile_key,profile_version,created_at,report->>'summary' AS summary FROM research.website_ai_hadith_drafts ORDER BY collection,source_number::numeric");
},["ai-hadith-draft-summaries-v1"],{revalidate:60});
export async function readHadithDraft(collection:string,number:string):Promise<HadithDraft|null> {
 if(!usesNeon())return null;
 const rows=await queryNeon<HadithDraft>("SELECT * FROM research.website_ai_hadith_drafts WHERE collection=$1 AND source_number=$2 LIMIT 1",[collection,number]);
 return rows[0]||null;
}
