import Link from "next/link";
import { draftStatusNames, type HadithDraft } from "@/lib/ai-hadith-drafts";
export function AiHadithReport({draft}:{draft:HadithDraft}) {
 return <section className="article-section" id="ai-analysis" data-ai-hadith-report={draft.source_number}>
  <h2>مسودة الفحص بالذكاء الاصطناعي — 22 طبقة</h2>
  <p><strong>تحليل آلي أولي ينتظر التحقيق والمراجعة البشرية؛ ليس حكمًا بقبول الحديث أو رده.</strong></p>
  <p>يعتمد هذا التحليل على نص المجموعة المستوردة وبياناتها. لم تُجرَ فيه مقابلة بالأصول أو تحقيق خارجي للرجال والطرق أو مقابلة الآيات بمصحف محقق. ما يحتاج ذلك موضح في كل طبقة.</p>
  <p>{draft.report.summary}</p>
  <dl className="metadata-list"><div><dt>نسبة الخبر بحسب النص</dt><dd>{draft.report.report_type}</dd></div><div><dt>الموضوعات</dt><dd>{draft.report.themes.join("، ")}</dd></div><div><dt>المنهج</dt><dd>{draft.profile_key} — الإصدار {draft.profile_version} (مسودة)</dd></div><div><dt>النموذج</dt><dd dir="ltr">{draft.model}</dd></div><div><dt>تاريخ التحليل</dt><dd>{new Intl.DateTimeFormat("ar-u-nu-latn",{dateStyle:"medium",timeZone:"Asia/Tokyo"}).format(new Date(draft.created_at))}</dd></div></dl>
  {draft.report.layers.map(layer=><details key={layer.code} className="article-section" data-ai-layer={layer.code}>
   <summary><strong>{layer.code} — {layer.title}</strong> · {draftStatusNames[layer.status]}</summary>
   <p>{layer.analysis}</p>
   {layer.quotes.map((quote,index)=><blockquote key={index}><p className="font-hadith">{quote}</p><small>اقتباس من نص الحديث المعروض أعلاه؛ ليس شاهدًا مستقلًا.</small></blockquote>)}
   <p><strong>الخطوة التالية:</strong> {layer.next_step}</p>
  </details>)}
  <Link href="/corpus/analysis" className="text-link">جميع مسودات الفحص الآلي ←</Link>
 </section>;
}
