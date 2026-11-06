import Link from "next/link";
import { readDraftSummaries } from "@/lib/ai-hadith-drafts";
import { hadithHref } from "@/lib/hadith-query";
import { collections } from "@/lib/research";
import { PageHeading } from "@/components/research-ui";
export const dynamic="force-dynamic";
export const metadata={title:"مسودات فحص الأحاديث بالذكاء الاصطناعي"};
export default async function AnalysisPage(){
 const drafts=await readDraftSummaries();
 return <>
  <PageHeading eyebrow="مكتبة الحديث" title="مسودات فحص الأحاديث بالذكاء الاصطناعي" description="الدفعة الأولى: البخاري 1–200، وفق طبقات المنهج المحفوظة. افتح الحديث لقراءة تحليل الطبقات الـ22 واقتباساته وخطوات استكمال التحقيق." />
  <section className="article-section"><p><strong>هذه مسودات آلية وليست أحكامًا شرعية أو نتائج قبول ورد معتمدة.</strong> نُظّمت ملاحظات النص وفُصلت عنها الأدلة الناقصة. تحتاج دراسة الرجال والطرق والمقابلة بالأصول والقرآن إلى مصادر محققة ومراجعة بشرية.</p><p data-ai-draft-count={drafts.length}>المتاح الآن: {drafts.length} من 200 مسودة. لا تُضاف المسودات تلقائيًا إلى أعداد القبول أو الكتاب.</p><Link href="/corpus">البحث والإحصاءات ←</Link></section>
  {drafts.map(draft=><article className="article-section" key={`${draft.collection}-${draft.source_number}`}><h2><Link href={`${hadithHref(draft.collection,draft.source_number)}#ai-analysis`}>{collections[draft.collection]||draft.collection} — حديث {draft.source_number}</Link></h2><p>{draft.summary}</p><Link className="text-link" href={`${hadithHref(draft.collection,draft.source_number)}#ai-analysis`}>اقرأ النص وتحليل الطبقات الـ22 ←</Link></article>)}
  {!drafts.length&&<p className="empty-state">لم تُنشر مسودات هذه الدفعة بعد.</p>}
 </>;
}
