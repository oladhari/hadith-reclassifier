import { NarratorFindingLinks } from "@/components/narrator-finding-links";
import libraryEvidence from "@/content/narrator-library-evidence.json";
import { proofHref } from "@/lib/evidence-links";
import { getMediaCatalogue } from "@/lib/media-catalogue";
import { ProofLink } from "@/components/proof-link";
import Link from "next/link";
import { notFound } from "next/navigation";
import { narrators,referenceBooks,groupedFindings,narratorEvidenceHref } from "@/lib/rijal";
import { PageHeading } from "@/components/research-ui";
export const dynamic="force-dynamic";
type Params={params:Promise<{slug:string}>};
export async function generateMetadata({params}:Params){const {slug}=await params;return {title:narrators.find(n=>n.slug===slug)?.name||"الترجمة غير موجودة"};}
export default async function NarratorPage({params}:Params){
 const {slug}=await params;const person=narrators.find(n=>n.slug===slug);if(!person)notFound();
 const attachments=(libraryEvidence as Record<string,{id:number;note:string;visual_checked:boolean}[]>)[slug]||[];
 const catalogue=attachments.length?await getMediaCatalogue():{};
 const documents=await Promise.all(attachments.map(async item=>({...item,href:await proofHref(item.id),title:catalogue[String(item.id)]?.title||"وثيقة من المكتبة"})));
 const linkedDocuments=documents.filter((item,index,all)=>item.href&&all.findIndex(other=>other.href===item.href)===index);
 return <><div className="breadcrumb"><Link href="/narrators">الرواة وأقوال النقاد</Link><span>/</span><span>{person.name}</span></div>
 <PageHeading eyebrow="ترجمة موثقة بالنقول" title={person.name} description="أقوال منسوبة إلى نقادها، مع نصها وموضعها وسياقها. النقول المعروضة لا تمثل استقصاءً لجميع المصادر أو حكماً مستقلاً من الموسوعة." />
 <section className="article-section"><h2>الأوصاف المفهرسة</h2><p><strong>في التشيع:</strong> <NarratorFindingLinks person={person} affiliation={true}/></p><p><strong>في النقد والتوثيق:</strong> <NarratorFindingLinks person={person} affiliation={false}/></p><p className="small muted">يبقى كل لفظ منسوباً إلى قائله؛ لا يجمع الفهرس الأقوال في درجة رقمية. هوية الراوي في أي إسناد تحتاج مقابلة مستقلة قبل تطبيق الحكم على الطريق.</p></section>
 {person.evidence.map(e=>{const book=referenceBooks.find(b=>b.id===e.book_id)!;return <section className="article-section" key={`${e.book_id}-${e.page_id}`} data-narrator-source={`${e.book_id}/${e.page_id}`}>
 <h2>{book.title} — {e.locator}</h2><dl className="metadata-list"><div><dt>المؤلف</dt><dd>{book.author}</dd></div><div><dt>الطبعة المنقول عنها</dt><dd>{book.edition}</dd></div><div><dt>رقم الترجمة</dt><dd>{e.entry_number}</dd></div></dl>
 {groupedFindings(e).map((f,index)=><div className="narrator-finding" key={index}><h3>{f.critic}</h3><blockquote><p><Link href={narratorEvidenceHref(person,e,e.findings.findIndex(item=>item.quote===f.quote&&item.critic===f.critic))}>{f.quote}</Link></p></blockquote><p><Link className="text-link" href={narratorEvidenceHref(person,e,e.findings.findIndex(item=>item.quote===f.quote&&item.critic===f.critic))}>تحقق من الاقتباس المظلل والصورة المطبوعة ←</Link></p><p className="small muted">الألفاظ المفهرسة: {[...new Set(f.labels)].join(" · ")}</p></div>)}
 <p><a className="button button-dark" href={e.url} target="_blank" rel="noopener noreferrer">افتح النص في موضعه بالشاملة ↗</a> <Link className="text-link" href={`/library/references/${book.id}`}>بطاقة الكتاب وطرق القراءة ←</Link></p>
 {e.continuation_pages?.map(page=><p key={page.page_id}><a className="text-link" href={page.url} target="_blank" rel="noopener noreferrer">تابع الترجمة في صفحة المصدر التالية ({page.page_id}) ↗</a></p>)}
 <details><summary>سياق الترجمة في الصفحة</summary><p className="source-context">{e.context}</p></details><p className="small muted">النقول مقابلة بالنص الإلكتروني. افتح «تحقق من الاقتباس» لرؤية موضعه المظلل في الصورة المطبوعة؛ وقد تمتد الترجمة إلى صفحات أخرى.</p>
 </section>;})}
 {linkedDocuments.length>0&&<section className="article-section" data-narrator-library-evidence={linkedDocuments.length}><h2>الوثائق والصور المرتبطة في مكتبتنا</h2><p>جُمعت الوثائق بحسب الراوي، مع إبقاء تعليقات المصدر في صفحاتها. ربط الوثيقة هنا لا يعني اعتماد كل ما ورد فيها أو مقابلة جميع صورها؛ تظهر ملاحظة المقابلة لكل ملف.</p>{linkedDocuments.map(item=><ProofLink key={item.id} href={item.href!} title={item.title} description={item.note} />)}</section>}
 <Link className="text-link" href="/narrators">العودة إلى جدول الرواة ←</Link></>;
}
