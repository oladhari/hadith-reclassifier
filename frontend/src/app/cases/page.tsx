import { queryText } from "@/lib/request-policy";
import { cases, matches, ar } from "@/lib/research";
import { CaseCard, PageHeading } from "@/components/research-ui";
export const metadata = { title: "القضايا والأدلة" };
export default async function CasesPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; category?: string }>;
}) {
  const params = await searchParams;
  const q = queryText(params.q), category = queryText(params.category, 80);
  const results = cases.filter(
    (c) =>
      (!category || c.category === category) &&
      matches([c.title, c.subtitle, ...c.terms].join(" "), q),
  );
  return (
    <>
      <PageHeading
        eyebrow="من السؤال إلى المصدر"
        title="القضايا والأدلة"
        description="من حصار عثمان إلى الجمل وصفين: اقرأ السؤال، وتعرّف على الروايات المحتج بها، وراجع الأدلة ومواضع الاختلاف داخل كل ملف."
      />
      <form className="filter-bar" action="/cases">
        <label>
          ابحث في القضايا
          <input
            name="q"
            defaultValue={q}
            placeholder="اسم حديث، راوٍ، أو موضوع…"
            maxLength={160}
          />
        </label>
        <label>
          المحور
          <select name="category" defaultValue={category}>
            <option value="">جميع المحاور</option>
            {[...new Set(cases.map((c) => c.category))].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <button className="button button-dark" type="submit">
          تطبيق البحث
        </button>
      </form>
      <p className="result-count">
        {ar(results.length)} ملفات • مخططات بحث أولية
      </p>
      <div className="case-grid">
        {results.map((item) => (
          <CaseCard key={item.slug} item={item} />
        ))}
      </div>
      {!results.length && (
        <div className="empty-state">
          لا توجد قضية مطابقة. جرّب كلمات أقل أو محورًا آخر.
        </div>
      )}
    </>
  );
}
