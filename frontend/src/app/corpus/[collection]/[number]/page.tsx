import Link from "next/link";
import { notFound, permanentRedirect } from "next/navigation";
import { readHadith } from "@/lib/corpus-search";
import { collections } from "@/lib/research";
import { hadithNumber, hadithHref } from "@/lib/hadith-query";
import { HadithRecord } from "@/components/hadith-record";
import { PageHeading } from "@/components/research-ui";
export const dynamic="force-dynamic";
type Params={params:Promise<{collection:string;number:string}>};
function routeNumber(value:string) { try { return hadithNumber(decodeURIComponent(value)); } catch { return ""; } }
export async function generateMetadata({params}:Params) {
 const {collection,number}=await params;
 return {title:Object.hasOwn(collections,collection)&&routeNumber(number)?`${collections[collection]} — حديث ${routeNumber(number)}`:"الحديث غير موجود"};
}
export default async function HadithReader({params}:Params) {
 const {collection,number}=await params;const normalized=routeNumber(number);
 if(!Object.hasOwn(collections,collection)||!normalized)notFound();
 if(normalized!==number)permanentRedirect(hadithHref(collection,normalized));
 const hadith=await readHadith(collection,normalized);
 if(!hadith)notFound();
 return <><div className="breadcrumb"><Link href="/corpus">البحث في الأحاديث</Link><span>/</span><Link href={`/corpus?collection=${collection}`}>{collections[collection]}</Link><span>/</span><span>حديث {normalized}</span></div>
 <PageHeading eyebrow="نص الحديث ومرجعه" title={`${collections[collection]} — حديث ${normalized}`} description="اقرأ النص كما ورد في المجموعة المستوردة. حالة مراجعة الموسوعة منفصلة عن الأحكام المنقولة في المصدر." />
 <HadithRecord hadith={hadith} reader />
 <div className="related-actions"><Link className="button button-dark" href={`/corpus?collection=${collection}&id=${normalized}#corpus-results`}>الأحاديث بهذا الرقم في المجموعة</Link><Link className="button button-outline" href="/corpus#corpus-search">ابحث عن حديث آخر ←</Link></div></>;
}
