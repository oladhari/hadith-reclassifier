import data from "@/content/narrator-directory.json";
import references from "@/content/reference-books.json";
export const referenceBooks=references;
export const narrators=data.entries;
export type Narrator=typeof narrators[number];
export type Evidence=Narrator["evidence"][number];
export type Finding=Evidence["findings"][number];
export const findingNames:Record<string,string>={mild:"تشيع يسير / خفيف",tashayyu:"وصف بالتشيع دون درجة محددة",shii_jald:"شيعي جلد",rafidi_jald:"رافضي جلد",ghulu:"غلو أو إفراط في التشيع",liar:"اتهام صريح بالكذب بلفظ كذاب",accused:"متهم بالكذب",abandoned:"متروك أو لا يكتب حديثه",weak:"تضعيف أو نكارة",unknown:"مجهول",reliability:"أقوال توثيق أو صدق",counterassessment:"تعقيب مخالف للجرح"};
export const affiliationCategories=new Set(["mild","tashayyu","shii_jald","rafidi_jald","ghulu"]);
export function findings(person:Narrator){return person.evidence.flatMap(e=>e.findings);}
export function quotedLabels(person:Narrator,affiliation:boolean){return [...new Set(findings(person).filter(f=>affiliationCategories.has(f.category)===affiliation).map(f=>f.label))];}
export function groupedFindings(evidence:Evidence){
 const groups=new Map<string,{critic:string;quote:string;labels:string[]}>();
 for(const finding of evidence.findings){const key=JSON.stringify([finding.critic,finding.quote]);const group=groups.get(key)||{critic:finding.critic,quote:finding.quote,labels:[]};group.labels.push(finding.label);groups.set(key,group);}
 return [...groups.values()];
}
