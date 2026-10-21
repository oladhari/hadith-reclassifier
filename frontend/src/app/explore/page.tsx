import Link from "next/link";
import { cases, matches } from "@/lib/research";
import { topics } from "@/lib/topics";
import { PageHeading, CaseCard, TopicCard } from "@/components/research-ui";
export const metadata = { title: "البحث في الموسوعة" };
export default async function Explore({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q: raw = "" } = await searchParams;
  const q = raw.slice(0, 160);
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
            placeholder="حديث، راوٍ، كتاب، أو قضية…"
            required
            maxLength={160}
          />
        </label>
        <button className="button button-dark">ابحث</button>
      </form>
      {q && (
        <>
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
            <Link href="/library">
              <strong>تصفّح الأصول المحفوظة ←</strong>
              <p>صور صفحات الكتب والوثائق والمرئيات متاحة للقراءة والمشاهدة.</p>
            </Link>
          </div>
        </>
      )}
    </>
  );
}
