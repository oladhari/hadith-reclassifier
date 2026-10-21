import Link from "next/link";
import { collections, matches, ar } from "@/lib/research";
import { readCollection } from "@/lib/corpus";
import { corpusProgress, stateNames, recordProgress, matchesState, type CorpusState } from "@/lib/corpus-progress";
import { PageHeading } from "@/components/research-ui";
export const metadata = { title: "مكتبة الحديث وحالة المراجعة" };
export const dynamic = "force-dynamic";
export default async function CorpusPage({ searchParams }: {
  searchParams: Promise<{ q?: string; collection?: string; page?: string; id?: string; status?: string }>;
}) {
  const { q: rawQ = "", collection = "", page = "1", id: rawId = "", status: rawStatus = "" } = await searchParams;
  const q = rawQ.slice(0, 160).trim();
  const id = rawId.slice(0, 80).trim();
  const status = [...Object.keys(stateNames), "filtered", "book"].includes(rawStatus) ? rawStatus : "";
  const requested = Boolean(q || id || status);
  const selectedBook = corpusProgress.collections.find(book => book.slug === collection);
  const counts = selectedBook?.counts || corpusProgress.counts;
  const names = collection ? Object.hasOwn(collections, collection) ? [collection] : [] : Object.keys(collections);
  const hasMatchingRecords = !status || status === "unreviewed" || Object.entries(corpusProgress.records).some(([key, value]) => (!collection || key.startsWith(`${collection}:`)) && matchesState(value, status));
  const batches = requested && hasMatchingRecords ? await Promise.all(names.map(async name => ({ name, rows: await readCollection(name).catch(() => null) }))) : [];
  const unavailable = batches.filter(batch => !batch.rows).map(batch => collections[batch.name]);
  const results = batches.flatMap(batch => (batch.rows || []).filter(h => h.text?.trim()).map(h => ({ ...h, collection: batch.name, progress: recordProgress(batch.name, h.hadithnumber) })))
    .filter(h => (!id || String(h.hadithnumber) === id) && matches(h.text, q) && matchesState(h.progress, status));
  const pages = Math.max(1, Math.ceil(results.length / 15));
  const current = Math.min(pages, Math.max(1, Number.parseInt(page) || 1));
  const url = (p: number) => `/corpus?${new URLSearchParams({ q, collection, status, page: String(p), ...(id ? { id } : {}) })}#corpus-results`;
  const stats = [
    ["total", "السجلات المتوفرة"], ["unreviewed", "لم تُفحص بعد"], ["in_progress", "قيد الفحص"],
    ["filtered", "فُحصت أوليًا بأدلة"], ["needs_review", "بانتظار المراجعة البشرية"],
    ["accepted", "مقبولة بعد المراجعة"], ["rejected", "مستبعدة بعد المراجعة"], ["in_book", "معتمدة للكتاب"],
  ] as const;
  return <>
    <PageHeading eyebrow="المجموعات الحديثية ونتائج فحصها" title="مكتبة الحديث وحالة المراجعة" description="تعرّف على الكتب المتوفرة، وابحث عن رواية بعينها، وتتبّع انتقالها من الفحص إلى المراجعة البشرية والاعتماد للكتاب العثماني." />
    <div className="corpus-scope"><strong>{selectedBook ? selectedBook.title : "المكتبة كاملة"}</strong>{selectedBook && <Link href="/corpus">اعرض جميع المجموعات ←</Link>}</div>
    <section className="corpus-stats" aria-label="إحصاءات فحص الأحاديث">{stats.map(([key, label]) => <div key={key} data-corpus-stat={key}><strong dir="ltr">{ar(counts[key])}</strong><span>{label}</span></div>)}</section>
    <p className="corpus-stat-note">الأعداد سجلات بحسب ترقيم المجموعات وتشمل تكرار الطرق. الفحص الأولي يختلف عن القبول النهائي؛ لا تُحسب تشغيلات بلا أدلة مكتملة نتائجَ تصفية، ولا يعتمد مدخل للكتاب قبل المراجعة البشرية.</p>
    <section className="article-section"><div className="section-heading"><h2>الكتب المتوفرة في المكتبة</h2><Link href="/methodology" className="text-link">طبقات الفحص ←</Link></div>
      <div className="corpus-collection-grid">{corpusProgress.collections.map(book => <article className={`corpus-collection ${book.slug === collection ? "selected" : ""}`} key={book.slug}>
        <h3>{book.title}</h3><strong className="collection-total" dir="ltr">{ar(book.counts.total)}</strong><p>سجل حديثي</p>
        <dl><div><dt>فحص أولي موثق</dt><dd>{ar(book.counts.filtered)}</dd></div><div><dt>بانتظار المراجعة</dt><dd>{ar(book.counts.needs_review)}</dd></div><div><dt>مقبول بعد المراجعة</dt><dd>{ar(book.counts.accepted)}</dd></div><div><dt>مستبعد بعد المراجعة</dt><dd>{ar(book.counts.rejected)}</dd></div></dl>
        <Link className="text-link" href={`/corpus?collection=${book.slug}#corpus-search`}>ابحث في هذه المجموعة ←</Link>
      </article>)}{corpusProgress.missing_collections.map(book => <article className="corpus-collection collection-pending" key={book.title}><span className="eyebrow">غير مكتملة في مكتبة الأحاديث</span><h3>{book.title}</h3><p>{book.note}</p><Link href="/cases/uthman-shirt" className="text-link">اقرأ مثالًا من الصفحات المتوفرة ←</Link></article>)}</div>
    </section>
    <section className="article-section" id="corpus-search"><h2>ابحث عن حديث وحالة مراجعته</h2>
      <form action="/corpus" className="filter-bar corpus-filter">
        <label>كلمات من الحديث أو الإسناد<input name="q" defaultValue={q} maxLength={160} placeholder="اكتب لفظًا من الرواية…" /></label>
        <label>المجموعة<select name="collection" defaultValue={collection}><option value="">جميع المجموعات</option>{Object.entries(collections).map(([key, name]) => <option key={key} value={key}>{name}</option>)}</select></label>
        <label>حالة الفحص<select name="status" defaultValue={status}><option value="">جميع الحالات عند البحث</option><option value="filtered">ذات فحص أولي موثق</option>{Object.entries(stateNames).map(([key, name]) => <option key={key} value={key}>{name}</option>)}<option value="book">معتمد للكتاب</option></select></label>
        <label className="number-field">رقم الحديث<input name="id" defaultValue={id} maxLength={80} inputMode="decimal" placeholder="اختياري" /></label>
        <button className="button button-dark">اعرض النتائج</button>
      </form>
      <div className="corpus-status-links"><Link href={`/corpus?collection=${collection}&status=accepted#corpus-results`}>المقبولة</Link><Link href={`/corpus?collection=${collection}&status=needs_review#corpus-results`}>بانتظار المراجعة</Link><Link href={`/corpus?collection=${collection}&status=rejected#corpus-results`}>المستبعدة</Link><Link href={`/corpus?collection=${collection}&status=book#corpus-results`}>المعتمدة للكتاب</Link></div>
    </section>
    {unavailable.length > 0 && <p className="empty-state">تعذّر تحميل نصوص {unavailable.join("، ")}. حاول مجددًا لاحقًا.</p>}
    <section id="corpus-results">
      {!requested ? <div className="corpus-welcome"><h2>ابدأ بالمجموعة أو بالرواية التي تبحث عنها</h2><p>اختر حالة الفحص أو اكتب كلمات من الحديث أو رقمه لعرض النتائج. وجود الحديث في المكتبة لا يعني أنه فُحص أو اعتُمد وفق منهج الموسوعة.</p></div> : <>
        <p className="result-count">{ar(results.length)} سجلًا مطابقًا{status ? ` • ${status === "filtered" ? "فحص أولي موثق" : status === "book" ? "معتمد للكتاب" : stateNames[status as CorpusState]}` : ""}</p>
        <div className="hadith-list">{results.slice((current - 1) * 15, current * 15).map(h => <article className="hadith-record" key={`${h.collection}-${h.hadithnumber}`}>
          <div className="record-header"><span>{collections[h.collection]} <b>#{h.hadithnumber}</b></span><span className={`inline-status corpus-state-${h.progress.status}`}>{stateNames[h.progress.status]}</span></div>
          <p className="font-hadith">{h.text}</p>
          {h.progress.review && <section className="corpus-decision"><h3>{h.progress.status === "accepted" ? "نتيجة المراجعة: مقبول" : "نتيجة المراجعة: مستبعد"}</h3><p>{h.progress.review.reasoning || "اعتمدت النتيجة بعد المراجعة البشرية."}</p><small>تاريخ المراجعة: {new Intl.DateTimeFormat("ar-u-nu-latn", { dateStyle: "medium" }).format(new Date(h.progress.review.reviewed_at))}</small></section>}
          {h.progress.in_book && <p className="corpus-book-ready">اعتمد هذا المدخل لإصدار من الكتاب العثماني.</p>}
          {h.progress.status === "unreviewed" && <p className="small muted">لا توجد نتيجة فحص معتمدة لهذه الرواية بعد.</p>}
          <details><summary>مرجع الرواية</summary><dl className="metadata-list"><div><dt>المجموعة</dt><dd>{collections[h.collection]}</dd></div><div><dt>رقم الكتاب</dt><dd>{h.reference?.book ?? "غير محدد"}</dd></div><div><dt>الرقم داخل الكتاب</dt><dd>{h.reference?.hadith ?? "غير محدد"}</dd></div></dl><p className="small muted">الأرقام بحسب المجموعة المتوفرة، وقد تختلف عن ترقيم طبعات أخرى.</p>{h.grades?.map((g,i) => <p className="small" key={i}>حكم منقول في المجموعة: {g.name} — {g.grade}؛ ليس نتيجة فحص الموسوعة.</p>)}</details>
        </article>)}</div>
        {!results.length && <p className="empty-state">{status && status !== "unreviewed" ? "لا توجد روايات بهذه الحالة ضمن البحث الحالي. ستظهر النتائج عند استكمال الفحص والمراجعة." : "لم نجد نصًا مطابقًا. جرّب كلمة أقصر أو مجموعة أخرى."}</p>}
        {results.length > 15 && <nav className="pagination" aria-label="صفحات الأحاديث">{current > 1 && <Link href={url(current - 1)}>→ السابق</Link>}<span>صفحة {ar(current)} من {ar(pages)}</span>{current < pages && <Link href={url(current + 1)}>التالي ←</Link>}</nav>}
      </>}
    </section>
    <section className="corpus-book-banner"><h2>من المراجعة إلى الكتاب العثماني</h2><p>تُجمع المداخل المقبولة بعد المراجعة البشرية، مع أدلتها وتعليلها. ثم يُعتمد إدراج كل مدخل في إصدار الكتاب؛ فالقبول وإعداد النسخة النهائية مرحلتان موثقتان.</p><Link href="/sahih-othmani" className="text-link">مسار إعداد الكتاب ←</Link></section>
  </>;
}
