import { searchHadiths } from "@/lib/corpus-search";
import { HadithRecord } from "@/components/hadith-record";
import { ar } from "@/lib/research";
import { queryText } from "@/lib/request-policy";
import Link from "next/link";
import { cases, matches } from "@/lib/research";
import { topics } from "@/lib/topics";
import { PageHeading, CaseCard, TopicCard } from "@/components/research-ui";
import { getArchive } from "@/lib/archive";
import { getMediaCatalogue, searchLibrary } from "@/lib/media-catalogue";
import { LibraryCard } from "@/components/library-card";
export const metadata = { title: "البحث في الموسوعة" };
export default async function Explore({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q: raw = "" } = await searchParams;
  const q = queryText(raw);
  const [archive, catalogue, hadiths] = await Promise.all([getArchive(), getMediaCatalogue(), q ? searchHadiths({q}) : Promise.resolve(null)]);
  const libraryResults = q ? await searchLibrary(archive, catalogue, q) : [];
  const results = q
    ? cases.filter((c) =>
        matches([c.title, c.subtitle, ...c.terms].join(" "), q),
      )
    : [];
  const matchedTopics = q
    ? topics.filter((t) =>
        matches([t.title, t.description, ...t.terms].join(" "), q),
      )
    : [];
  return (
    <>
      <PageHeading
        eyebrow="ابحث، ثم تتبّع المصدر"
        title="ما السؤال الذي يشغلك؟"
        description="ابحث عن القضية التي تشغلك، واقرأ مواضع الاختلاف، أو تتبّع ألفاظ الرواية في مكتبة الحديث."
      />
      <form action="/explore" className="filter-bar">
        <label>
          البحث
          <input
            name="q"
            defaultValue={q}
            placeholder="كلمات من حديث، أو رقمه، أو البخاري 1، أو قضية…"
            required
            maxLength={160}
          />
        </label>
        <button className="button button-dark">ابحث</button>
      </form>
      {q && (
        <>
          <section className="section-block main-hadith-results" data-main-hadith-search>
            <div className="section-heading"><h2>أحاديث مطابقة لبحثك</h2><Link className="text-link" href={`/corpus?q=${encodeURIComponent(q)}`}>جميع نتائج الأحاديث ({ar(hadiths?.total || 0)}) ←</Link></div>
            {hadiths && hadiths.total > 0 ? <><p className="result-count" data-hadith-result-count={hadiths.total}>{ar(hadiths.total)} سجلًا مطابقًا في مكتبة الحديث</p><div className="hadith-list">{hadiths.results.slice(0,5).map(h=><HadithRecord key={`${h.collection}-${h.hadithnumber}`} hadith={h} />)}</div></> : <p className="empty-state">لم نجد حديثًا بهذه الكلمات أو بهذا الرقم ضمن المجموعات المتاحة. جرّب كلمات أقصر أو اختر الكتاب في <Link href={`/corpus?q=${encodeURIComponent(q)}`}>البحث المتخصص</Link>.</p>}
          </section>
          {matchedTopics.length > 0 && (
            <>
              <h2 className="results-heading">محاور مرتبطة بسؤالك</h2>
              <div className="topic-grid">
                {matchedTopics.map((topic) => (
                  <TopicCard key={topic.slug} topic={topic} />
                ))}
              </div>
            </>
          )}
          <h2 className="results-heading">ملفات مرتبطة بـ «{q}»</h2>
          <div className="case-grid">
            {results.map((item) => (
              <CaseCard key={item.slug} item={item} />
            ))}
          </div>
          {!results.length && (
            <p className="empty-state">
              لا يوجد ملف بحث مرتبط بهذه الكلمات بعد. يمكنك متابعة البحث في
              النصوص الحديثية.
            </p>
          )}
          <div className="search-destinations">
            <Link href={`/corpus?q=${encodeURIComponent(q)}`}>
              <strong>ابحث عن «{q}» في الأحاديث ←</strong>
              <p>ابحث في النصوص العربية، واختر مجموعة الحديث التي تريدها.</p>
            </Link>
            <Link href={`/library?q=${encodeURIComponent(q)}`}>
              <strong>تصفّح الأصول المحفوظة ←</strong>
              <p>صور صفحات الكتب والوثائق والمرئيات متاحة للقراءة والمشاهدة.</p>
            </Link>
          </div>
          {libraryResults.length > 0 && <section className="section-block">
            <div className="section-heading"><h2>نتائج من الكتب والمقاطع والمصادر</h2><Link className="text-link" href={`/library?q=${encodeURIComponent(q)}`}>جميع النتائج ({libraryResults.length}) ←</Link></div>
            <div className="library-grid">{libraryResults.slice(0, 6).map(item => <LibraryCard key={item.id} item={item} metadata={catalogue[String(item.id)]} />)}</div>
          </section>}
        </>
      )}
    </>
  );
}
