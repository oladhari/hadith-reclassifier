import Link from "next/link";
import { affiliationCategories,narratorEvidenceHref,type Narrator } from "@/lib/rijal";
export function NarratorFindingLinks({person,affiliation}:{person:Narrator;affiliation:boolean}){
 const links=person.evidence.flatMap(e=>e.findings.map((f,index)=>({e,f,index}))).filter(({f})=>affiliationCategories.has(f.category)===affiliation);
 if(!links.length)return <>{affiliation?"لم يرد في النقول المعروضة":"لا حكم آخر في المقتطف المعروض"}</>;
 return <>{links.map(({e,f,index},i)=><span key={`${e.book_id}-${e.page_id}-${index}`}>{i>0&&" · "}<Link className="narrator-evidence-link" href={narratorEvidenceHref(person,e,index)} title={`تحقق من قول ${f.critic} واقرأ النص والصورة`}>{f.label}</Link></span>)}</>;
}
