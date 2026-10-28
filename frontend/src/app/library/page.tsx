import Link from "next/link";
import { getArchive, kindNames } from "@/lib/archive";
import { getMediaCatalogue, publicLibrary, searchLibrary, scopeNames } from "@/lib/media-catalogue";
import { ar } from "@/lib/research";
import { topics } from "@/lib/topics";
import { PageHeading } from "@/components/research-ui";
import { LibraryCard } from "@/components/library-card";
export const metadata = { title: "مكتبة المصادر" };
export default async function LibraryPage({ searchParams }: {
  searchParams: Promise<{ kind?: string; page?: string; q?: string; topic?: string; scope?: string }>;
}) {
  const [archive, catalogue, params] = await Promise.all([getArchive(), getMediaCatalogue(), searchParams]);
  const { kind = "", page = "1", q: raw = "", topic = "", scope = "" } = params;
  const q = raw.slice(0, 160);
  const library = publicLibrary(archive, catalogue);
  const searched = q ? await searchLibrary(archive, catalogue, q) : library;
  const filtered = searched.filter(item => {
    const entry = catalogue[String(item.id)];
    return (!kind || item.kind === kind) && (!topic || entry.topics.includes(topic)) &&
      (!scope || entry.scope === scope);
  });
  const pages = Math.max(1, Math.ceil(filtered.length / 24));
  const current = Math.min(pages, Math.max(1, Number.parseInt(page) || 1));
  const items = filtered.slice((current - 1) * 24, current * 24);
  const url = (p: number, type = kind) => `/library?${new URLSearchParams({ kind: type, q, topic, scope, page: String(p) })}`;
  return <>
    <PageHeading eyebrow="المصادر بحسب الموضوع" title="المكتبة المصوّرة والمرئيات"
      description="مصادر مختارة لمحاور الموسوعة: صفحات وكتب وأبحاث ومقاطع مرئية وصوتية، بعناوين عربية وملخصات قابلة للبحث." />
    <div className="type-tabs">
      <Link href={url(1, "")} className={!kind ? "selected" : ""}>الكل <span>{ar(library.length)}</span></Link>
      {Object.entries(kindNames).map(([key, label]) => <Link className={kind === key ? "selected" : ""} key={key} href={url(1, key)}>
        {label}<span>{ar(library.filter(item => item.kind === key).length)}</span>
      </Link>)}
    </div>
    <form action="/library" className="filter-bar library-filters">
      <input type="hidden" name="kind" value={kind} />
      <label className="library-query">ابحث في المكتبة<input name="q" maxLength={160} defaultValue={q} placeholder="موضوع، كتاب، مؤلف، راوٍ، أو عبارة من التفريغ" /></label>
      <label>المحور<select name="topic" defaultValue={topic}><option value="">جميع المحاور</option>{topics.map(item => <option key={item.slug} value={item.slug}>{item.title}</option>)}</select></label>
      <label>نوع المحتوى<select name="scope" defaultValue={scope}><option value="">جميع الأنواع</option>{Object.entries(scopeNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      <button className="button button-dark">ابحث في المكتبة</button>
    </form>
    <p className="muted library-result-count" data-result-count={filtered.length}>{ar(filtered.length)} مادة مطابقة</p>
    <div className="library-grid">{items.map(item => <LibraryCard key={item.id} item={item} metadata={catalogue[String(item.id)]} />)}</div>
    {!items.length && <p className="empty-state">لا توجد مادة مطابقة. جرّب كلمات أخرى أو غيّر المحور ونوع المحتوى.</p>}
    <nav className="pagination" aria-label="صفحات المكتبة">
      {current > 1 && <Link href={url(current - 1)}>→ السابق</Link>}
      <span>صفحة {ar(current)} من {ar(pages)} • {ar(filtered.length)} مادة</span>
      {current < pages && <Link href={url(current + 1)}>التالي ←</Link>}
    </nav>
  </>;
}
