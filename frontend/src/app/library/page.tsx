import { referenceEdition } from "@/lib/reference-assets";
import { bookThemes,bookTheme } from "@/lib/book-themes";
import { referenceBooks } from "@/lib/rijal";
import { ReferenceBookCard } from "@/components/reference-book-card";
import { matches } from "@/lib/research";
import { BundleLinks } from "@/components/research-bundles";
import { queryText } from "@/lib/request-policy";
import Link from "next/link";
import { getArchive } from "@/lib/archive";
import { getMediaCatalogue, publicLibrary, searchLibrary, scopeNames } from "@/lib/media-catalogue";
import { authorLabel, excerptAlbums, librarySection, sectionNames } from "@/lib/library-organization";
import { ar } from "@/lib/research";
import { topics } from "@/lib/topics";
import { PageHeading } from "@/components/research-ui";
import { LibraryCard } from "@/components/library-card";
import { ExcerptAlbumCard } from "@/components/excerpt-album-card";
export const metadata = { title: "مكتبة المصادر" };
export default async function LibraryPage({ searchParams }: {
  searchParams: Promise<{ section?: string; kind?: string; page?: string; q?: string; topic?: string; scope?: string; theme?: string }>;
}) {
  const [archive, catalogue, params] = await Promise.all([getArchive(), getMediaCatalogue(), searchParams]);
  const { kind = "", page = "1", q: raw = "", topic = "", scope = "" } = params;
  const q = queryText(raw);
  const theme=Object.hasOwn(bookThemes,params.theme||"")?params.theme!:"";
  const references=referenceBooks.filter(book=>(!q||matches([book.title,book.author,book.purpose,book.edition].join(" "),q))&&(!theme||theme===book.theme)&&(!topic||(topic==="narrators"&&book.theme==="rijal"))&&(!scope||scope==="full_book")&&(!kind||(kind==="pdf"&&Boolean(referenceEdition(String(book.id))))));
  const requested = params.section || (kind || q || topic || scope ? "all" : "books");
  const section = sectionNames[requested] ? requested : "books";
  const library = publicLibrary(archive, catalogue);
  const searched = q ? await searchLibrary(archive, catalogue, q) : library;
  const filtered = searched.filter(item => {
    const entry = catalogue[String(item.id)];
    return (section === "all" || librarySection(item, entry) === section) && (!kind || item.kind === kind) &&
      (!theme || (librarySection(item,entry)==="books" && bookTheme(item.id)===theme)) && (!topic || entry.topics.includes(topic)) && (!scope || entry.scope === scope);
  });
  const groups = section === "excerpts" ? excerptAlbums(filtered, catalogue) : [];
  const rows = section === "excerpts" ? groups.map(album => ({ item: album.items[0], album }))
    : filtered.map(item => ({ item, album: undefined }));
  const pages = Math.max(1, Math.ceil(rows.length / 24));
  const current = Math.min(pages, Math.max(1, Number.parseInt(page) || 1));
  const items = rows.slice((current - 1) * 24, current * 24);
  const url = (p: number) => `/library?${new URLSearchParams({ section, kind, q, topic, scope, theme, page: String(p) })}`;
  const bookIndex = filtered.filter(item => librarySection(item,catalogue[String(item.id)]) === "books")
    .sort((a,b)=>catalogue[String(a.id)].title.localeCompare(catalogue[String(b.id)].title,"ar"));
  return <>
    <PageHeading eyebrow="مكتبة المصادر" title={section === "all" ? "جميع مواد المكتبة" : sectionNames[section]}
      description={section === "books" ? "كتب ومجلدات وبحوث ومراجع إلكترونية مرتبة حسب الموضوع، مع فهرس للعناوين والمؤلفين وروابط القراءة والتنزيل المتاحة." : section === "excerpts" ? "صفحات مختارة وصور ومقتطفات من الكتب والوثائق، مجمّعة بحسب المصدر والموضوع، مع الاحتفاظ بمراجع الصفحات." : "مصادر مختارة لمحاور الموسوعة، بعناوين عربية وملخصات قابلة للبحث."} />
    <p className="related-actions"><Link className="button button-outline" href="/themes">مجموعات الشواهد والشرح الموضوعي ←</Link></p>
    {topic && <BundleLinks topic={topic} />}
    <nav className="type-tabs" aria-label="أقسام المكتبة">
      {Object.entries(sectionNames).map(([key, label]) => <Link className={section === key ? "selected" : ""} aria-current={section === key ? "page" : undefined} key={key} href={`/library?section=${key}`}>
        {label}<span>{ar((key === "all" ? library.length : library.filter(item => librarySection(item, catalogue[String(item.id)]) === key).length) + ((key==="all"||key==="books")?referenceBooks.length:0))}</span>
      </Link>)}
    </nav>
    {(section==="books"||section==="all")&&<nav className="book-theme-nav" aria-label="موضوعات الكتب"><Link className={!theme?"selected":""} href={`/library?section=${section}`}>جميع الموضوعات</Link>{Object.entries(bookThemes).map(([key,label])=><Link key={key} className={theme===key?"selected":""} href={`/library?section=${section}&theme=${key}`}>{label}</Link>)}</nav>}
    {section === "books" && <section className="book-index" aria-labelledby="book-index-title">
      <h2 id="book-index-title">فهرس الكتب والبحوث</h2>
      <p className="muted">{ar(bookIndex.length)} كتابًا ومجلدًا وبحثًا من المواد المحفوظة، و{ar(references.length)} مراجع مصدرية. رُتّبت حسب الموضوع، مع بيان المتاح للقراءة لكل مصدر.</p>
      {Object.entries(bookThemes).map(([key,label])=>{const local=bookIndex.filter(item=>bookTheme(item.id)===key);const refs=references.filter(book=>book.theme===key);return (local.length||refs.length)?<section key={key} className="book-theme-group" data-book-theme={key}><h3>{label} <small>({ar(local.length+refs.length)})</small></h3>{key==="hadith"&&<p><Link href="/corpus">تصفح أيضاً مجموعات الحديث وابحث في نصوصها ←</Link></p>}<ol>{local.map(item=>{const entry=catalogue[String(item.id)];return <li key={item.id} data-book-index-id={item.id}><Link href={`/library/${item.id}`}>{entry.title}</Link><span>{authorLabel(entry)}</span><small>{entry.content_label}</small></li>;})}{refs.map(book=><li key={`ref-${book.id}`} data-reference-index-id={book.id}><Link href={`/library/references/${book.id}`}>{book.title}</Link><span>{book.author}</span><small>{referenceEdition(String(book.id))?"نسخة PDF كاملة محفوظة في المكتبة":"مرجع إلكتروني في الشاملة"}</small></li>)}</ol></section>:null;})}
    </section>}
    <form action="/library" className="filter-bar library-filters">
      <input type="hidden" name="section" value={section} />
      {theme&&<input type="hidden" name="theme" value={theme} />}
      {kind && <input type="hidden" name="kind" value={kind} />}
      <label className="library-query">ابحث في {sectionNames[section]}<input name="q" maxLength={160} defaultValue={q} placeholder="موضوع، كتاب، مؤلف، راوٍ، أو عبارة من التفريغ" /></label>
      <label>المحور<select name="topic" defaultValue={topic}><option value="">جميع المحاور</option>{topics.map(item => <option key={item.slug} value={item.slug}>{item.title}</option>)}</select></label>
      <label>نوع المحتوى<select name="scope" defaultValue={scope}><option value="">جميع الأنواع</option>{Object.entries(scopeNames).filter(([key]) => library.some(item => (section === "all" || librarySection(item, catalogue[String(item.id)]) === section) && catalogue[String(item.id)].scope === key)).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      <button className="button button-dark">ابحث في المكتبة</button>
    </form>
    <p className="muted library-result-count" data-result-count={filtered.length} data-library-total-count={filtered.length+((section==="books"||section==="all")?references.length:0)}>{ar(filtered.length)} مادة مطابقة من المواد المحفوظة{(section==="books"||section==="all")&&references.length>0&&`، و${ar(references.length)} مراجع مصدرية`}{section === "excerpts" && ` ضمن ${ar(rows.length)} ألبومًا ومادة مستقلة`}</p>
    {(section==="books"||section==="all")&&references.length>0&&<section className="article-section" data-reference-book-count={references.length}><h2>الكتب والمراجع المحفوظة</h2><p>بطاقات المصادر ونصوصها الإلكترونية، مع الملفات المصورة المتاحة. روابط المواضع المقتبسة تظهر في <Link href="/narrators">فهرس الرواة وأقوال النقاد</Link>.</p><div className="reference-book-grid">{references.map(book=><ReferenceBookCard key={book.id} book={book}/>)}</div></section>}
    <div className="library-grid">{items.map(({ item, album }) => album && album.items.length > 1
      ? <ExcerptAlbumCard key={album.key} album={album} catalogue={catalogue} />
      : <LibraryCard key={item.id} item={item} metadata={catalogue[String(item.id)]} />)}</div>
    {!items.length && !((section==="books"||section==="all")&&references.length) && <p className="empty-state">لا توجد مادة مطابقة. جرّب كلمات أخرى أو غيّر المحور ونوع المحتوى.</p>}
    <nav className="pagination" aria-label="صفحات المكتبة">
      {current > 1 && <Link href={url(current - 1)}>→ السابق</Link>}
      <span>صفحة {ar(current)} من {ar(pages)} • {ar(filtered.length)} مادة</span>
      {current < pages && <Link href={url(current + 1)}>التالي ←</Link>}
    </nav>
  </>;
}
