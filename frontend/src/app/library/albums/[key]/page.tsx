import Link from "next/link";
import { notFound } from "next/navigation";
import { getArchive } from "@/lib/archive";
import { getMediaCatalogue, publicLibrary } from "@/lib/media-catalogue";
import { authorLabel, excerptAlbums } from "@/lib/library-organization";
import { PageHeading } from "@/components/research-ui";
import { MediaOriginal } from "@/components/source-viewer";
import { ar } from "@/lib/research";
export const metadata = { title: "ألبوم مقتطفات وشواهد" };
export default async function AlbumPage({ params }: { params: Promise<{ key: string }> }) {
  const [{ key }, archive, catalogue] = await Promise.all([params, getArchive(), getMediaCatalogue()]);
  const album = excerptAlbums(publicLibrary(archive, catalogue), catalogue).find(row => row.key === key && row.items.length > 1);
  if (!album) notFound();
  return <>
    <div className="breadcrumb"><Link href="/library?section=excerpts">المقتطفات والشواهد</Link><span>/</span><span>ألبوم</span></div>
    <PageHeading eyebrow={`${ar(album.items.length)} مواد من المصدر نفسه`} title={album.work} description={album.theme} />
    <p>تُعرض المواد كما وردت في أصولها. تبقى بيانات الصفحات والمؤلف والتعليقات الخاصة بكل مادة ظاهرة معها.</p>
    <nav className="album-index" aria-label="محتويات الألبوم"><ol>{album.items.map(item => {
      const entry = catalogue[String(item.id)]; return <li key={item.id}><a href={`#source-${item.id}`}>{entry.title}</a>{entry.page_label && <span> — {entry.page_label}</span>}</li>;
    })}</ol></nav>
    {album.items.map(item => { const entry = catalogue[String(item.id)]; return <section className="album-material" key={item.id} id={`source-${item.id}`} data-album-member={item.id}>
      <h2>{entry.title}</h2><p className="muted">{authorLabel(entry)}{entry.page_label ? ` • ${entry.page_label}` : ""}</p>
      {entry.organization_note && <p className="organization-note">{entry.organization_note}</p>}
      <Link className="text-link" href={`/library/${item.id}`}>بيانات المادة ومراجعها ←</Link>
      <MediaOriginal item={item} />
    </section>; })}
  </>;
}
