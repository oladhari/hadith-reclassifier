import { readDraftSummaries } from "@/lib/ai-hadith-drafts";
import { queryText } from "@/lib/request-policy";
import { parseHadithQuery } from "@/lib/hadith-query";
import Link from "next/link";
import { HadithRecord } from "@/components/hadith-record";
import { searchHadiths } from "@/lib/corpus-search";
import { readInventory, type CorpusResult } from "@/lib/live-corpus";
import { collections, ar } from "@/lib/research";
import { stateNames, type CorpusState } from "@/lib/corpus-progress";
import { PageHeading } from "@/components/research-ui";
export const metadata = { title: "البحث في الأحاديث وقراءتها" };
export const dynamic = "force-dynamic";
export default async function CorpusPage({ searchParams }: {
  searchParams: Promise<{ q?: string; collection?: string; page?: string; id?: string; status?: string }>;
}) {
  const { q: rawQ = "", collection = "", page = "1", id: rawId = "", status: rawStatus = "" } = await searchParams;
  const q = queryText(rawQ).trim();
  const id = queryText(rawId, 80).trim();
  const status = [...Object.keys(stateNames), "filtered", "book"].includes(rawStatus) ? rawStatus : "";
  const requested = Boolean(q || id || status || collection);
  const [inventory,drafts] = await Promise.all([readInventory(),readDraftSummaries()]);
  const inferredCollection = parseHadithQuery(q,id,collection).collection;
  const selectedBook = inventory.collections.find(book => book.slug === inferredCollection);
  const counts = selectedBook?.counts || inventory.counts;
  const found = requested ? await searchHadiths({q,id,collection,status,page:Number.parseInt(page)||1}) : {results:[] as CorpusResult[],total:0,pages:1,current:1,unavailable:[] as string[]};
  const {results,total,pages,current,unavailable} = found;
  const url = (p: number) => `/corpus?${new URLSearchParams({ q, collection, status, page: String(p), ...(id ? { id } : {}) })}#corpus-results`;
  const stats = [
    ["total", "السجلات المتوفرة"], ["unreviewed", "لم تُفحص بعد"], ["in_progress", "قيد الفحص"],
    ["filtered", "فُحصت أوليًا بأدلة"], ["needs_review", "بانتظار المراجعة البشرية"],
    ["accepted", "مقبولة بعد المراجعة"], ["rejected", "مستبعدة بعد المراجعة"], ["in_book", "معتمدة للكتاب"],
  ] as const;
  return <>
    <PageHeading eyebrow="مكتبة الحديث" title="ابحث عن حديث واقرأ نصّه" description="اكتب كلمات من الحديث أو رقمه، واختر كتابًا إن أردت. يمكنك كذلك كتابة اسم الكتاب مع الرقم، مثل: البخاري 1. تظهر نصوص الروايات مباشرة مع مراجعها." />
    <section className="article-section" id="corpus-search"><h2>كلمات من الحديث أو رقمه</h2>
      <form action="/corpus" className="filter-bar corpus-filter">
        <label>نص الحديث أو رقمه<input name="q" defaultValue={q} maxLength={160} placeholder="إنما الأعمال بالنيات، أو 1، أو البخاري 1…" /></label>
        <label>المجموعة<select name="collection" defaultValue={inferredCollection}><option value="">جميع المجموعات</option>{Object.entries(collections).map(([key, name]) => <option key={key} value={key}>{name}</option>)}</select></label>
        <label>حالة الفحص<select name="status" defaultValue={status}><option value="">جميع الحالات عند البحث</option><option value="filtered">ذات فحص أولي موثق</option>{Object.entries(stateNames).map(([key, name]) => <option key={key} value={key}>{name}</option>)}<option value="book">معتمد للكتاب</option></select></label>
        <label className="number-field">رقم الحديث<input name="id" defaultValue={id} maxLength={80} inputMode="decimal" placeholder="اختياري" /></label>
        <button className="button button-dark">ابحث عن حديث</button>
      </form>
      <p className="small muted">ابحث دون تشكيل وبأي ترتيب للكلمات. إن كان الرقم مشتركًا بين كتب مختلفة فاختر المجموعة المطلوبة.</p>
      <div className="corpus-examples"><span>جرّب:</span><Link href="/corpus?q=إنما+الأعمال+بالنيات">إنما الأعمال بالنيات</Link><Link href="/corpus?q=البخاري+1">البخاري 1</Link><Link href="/corpus?collection=muslim&id=1">مسلم 1</Link></div>
      <div className="corpus-status-links"><Link href={`/corpus?collection=${collection}&status=accepted#corpus-results`}>المقبولة</Link><Link href={`/corpus?collection=${collection}&status=needs_review#corpus-results`}>بانتظار المراجعة</Link><Link href={`/corpus?collection=${collection}&status=rejected#corpus-results`}>المستبعدة</Link><Link href={`/corpus?collection=${collection}&status=book#corpus-results`}>المعتمدة للكتاب</Link></div>
    </section>
    {unavailable.length > 0 && <p className="empty-state">تعذّر تحميل نصوص {unavailable.join("، ")}. حاول مجددًا لاحقًا.</p>}
    <section id="corpus-results">
      {!requested ? <div className="corpus-welcome"><h2>اكتب كلمات من الحديث أو رقمه في المربع أعلاه</h2><p>يمكنك البحث في جميع الكتب أو اختيار كتاب لتصفّح نصوصه. حالة المراجعة لا تمنع قراءة الأحاديث المتاحة.</p></div> : <>
        <p className="result-count" data-hadith-result-count={total}>{ar(total)} سجلًا مطابقًا{status ? ` • ${status === "filtered" ? "فحص أولي موثق" : status === "book" ? "معتمد للكتاب" : stateNames[status as CorpusState]}` : ""}</p>
        <div className="hadith-list">{results.map(h => <HadithRecord key={`${h.collection}-${h.hadithnumber}`} hadith={h} />)}</div>
        {!results.length && <p className="empty-state">{status && status !== "unreviewed" ? "لا توجد روايات بهذه الحالة ضمن البحث الحالي. ستظهر النتائج عند استكمال الفحص والمراجعة." : "لم نجد نصًا مطابقًا. جرّب كلمة أقصر أو مجموعة أخرى."}</p>}
        {total > 15 && <nav className="pagination" aria-label="صفحات الأحاديث">{current > 1 && <Link href={url(current - 1)}>→ السابق</Link>}<span>صفحة {ar(current)} من {ar(pages)}</span>{current < pages && <Link href={url(current + 1)}>التالي ←</Link>}</nav>}
      </>}
    </section>
    {drafts.length>0&&<section className="article-section"><h2>مسودات الفحص الآلي</h2><p>نُشرت {drafts.length} مسودة من دفعة البخاري 1–200، تغطي الطبقات الـ22 وتوضح الأدلة الناقصة. تحتاج مراجعة بشرية ولا تمثل قبولًا أو ردًا معتمدًا.</p><Link className="text-link" href="/corpus/analysis">عرض النتائج وفتح تحليل كل حديث ←</Link></section>}
    <details className="corpus-inventory" open><summary>الكتب المتاحة وإحصاءات المراجعة</summary>
    <div className="corpus-scope"><strong>{selectedBook ? selectedBook.title : "المكتبة كاملة"}</strong>{selectedBook && <Link href="/corpus">اعرض جميع المجموعات ←</Link>}</div>
    <section className="corpus-stats" aria-label="إحصاءات فحص الأحاديث">{stats.map(([key, label]) => <div key={key} data-corpus-stat={key}><strong dir="ltr">{ar(counts[key])}</strong><span>{label}</span></div>)}</section>
    <p className="corpus-stat-note">الأعداد سجلات بحسب ترقيم المجموعات وتشمل تكرار الطرق. الفحص الأولي يختلف عن القبول النهائي؛ لا تُحسب تشغيلات بلا أدلة مكتملة نتائجَ تصفية، ولا يعتمد مدخل للكتاب قبل المراجعة البشرية.</p>
    <section className="article-section"><div className="section-heading"><h2>الكتب المتوفرة في المكتبة</h2><Link href="/methodology" className="text-link">طبقات الفحص ←</Link></div>
      <div className="corpus-collection-grid">{inventory.collections.map(book => <article className={`corpus-collection ${book.slug === collection ? "selected" : ""}`} key={book.slug}>
        <h3>{book.title}</h3><strong className="collection-total" dir="ltr">{ar(book.counts.total)}</strong><p>سجل حديثي</p>
        <dl><div><dt>فحص أولي موثق</dt><dd>{ar(book.counts.filtered)}</dd></div><div><dt>بانتظار المراجعة</dt><dd>{ar(book.counts.needs_review)}</dd></div><div><dt>مقبول بعد المراجعة</dt><dd>{ar(book.counts.accepted)}</dd></div><div><dt>مستبعد بعد المراجعة</dt><dd>{ar(book.counts.rejected)}</dd></div></dl>
        <Link className="text-link" href={`/corpus?collection=${book.slug}#corpus-search`}>ابحث في هذه المجموعة ←</Link>
      </article>)}{inventory.missing_collections.map(book => <article className="corpus-collection collection-pending" key={book.title}><span className="eyebrow">غير مكتملة في مكتبة الأحاديث</span><h3>{book.title}</h3><p>{book.note}</p><Link href="/cases/uthman-shirt" className="text-link">اقرأ مثالًا من الصفحات المتوفرة ←</Link></article>)}</div>
    </section>
    </details>
    <section className="corpus-book-banner"><h2>من المراجعة إلى الكتاب العثماني</h2><p>تُجمع المداخل المقبولة بعد المراجعة البشرية، مع أدلتها وتعليلها. ثم يُعتمد إدراج كل مدخل في إصدار الكتاب؛ فالقبول وإعداد النسخة النهائية مرحلتان موثقتان.</p><Link href="/sahih-othmani" className="text-link">مسار إعداد الكتاب ←</Link></section>
  </>;
}
