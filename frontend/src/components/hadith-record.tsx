import Link from "next/link";
import { collections } from "@/lib/research";
import { hadithHref } from "@/lib/hadith-query";
import { stateNames } from "@/lib/corpus-progress";
import type { CorpusResult } from "@/lib/live-corpus";
export function HadithRecord({ hadith: h, reader=false }: { hadith:CorpusResult; reader?:boolean }) {
 return <article className="hadith-record" data-hadith-number={h.hadithnumber} data-hadith-collection={h.collection}>
  <div className="record-header"><span>{collections[h.collection]} <b>#{h.hadithnumber}</b></span><span className={`inline-status corpus-state-${h.progress.status}`}>{stateNames[h.progress.status]}</span></div>
  <p className="font-hadith">{h.text}</p>
  {!reader && <Link className="text-link" href={hadithHref(h.collection,h.hadithnumber)}>اقرأ الحديث كاملًا وافتح مرجعه ←</Link>}
  {h.progress.review && <section className="corpus-decision"><h3>{h.progress.status==="accepted"?"نتيجة المراجعة: مقبول":"نتيجة المراجعة: مستبعد"}</h3><p>{h.progress.review.reasoning||"اعتمدت النتيجة بعد المراجعة البشرية."}</p><small>تاريخ المراجعة: {new Intl.DateTimeFormat("ar-u-nu-latn",{dateStyle:"medium"}).format(new Date(h.progress.review.reviewed_at))}</small></section>}
  {h.progress.in_book&&<p className="corpus-book-ready">اعتمد هذا المدخل لإصدار من الكتاب العثماني.</p>}
  {h.progress.status==="unreviewed"&&<p className="small muted">لا توجد نتيجة فحص معتمدة لهذه الرواية بعد.</p>}
  <details open={reader}><summary>مرجع الرواية</summary><dl className="metadata-list"><div><dt>المجموعة</dt><dd>{collections[h.collection]}</dd></div><div><dt>رقم الحديث في المجموعة</dt><dd>{h.hadithnumber}</dd></div>{h.arabicnumber!==undefined&&h.arabicnumber!==h.hadithnumber&&<div><dt>الترقيم العربي المنقول</dt><dd>{h.arabicnumber}</dd></div>}<div><dt>رقم الكتاب</dt><dd>{h.reference?.book??"غير محدد"}</dd></div><div><dt>الرقم داخل الكتاب</dt><dd>{h.reference?.hadith??"غير محدد"}</dd></div></dl><p className="small muted">الأرقام بحسب المجموعة المتوفرة، وقد تختلف عن ترقيم طبعات أخرى.</p>{h.grades?.map((g,i)=><p className="small" key={i}>حكم منقول في المجموعة: {g.name} — {g.grade}؛ ليس نتيجة فحص الموسوعة.</p>)}</details>
 </article>;
}
