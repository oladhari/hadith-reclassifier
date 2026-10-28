import Link from "next/link";
import { getArchive } from "@/lib/archive";
import { getMediaCatalogue, publicLibrary } from "@/lib/media-catalogue";
import { LibraryCard } from "./library-card";
import { topics } from "@/lib/topics";

export async function ThemedLibrary({ topic, caseSlug }: { topic?: string; caseSlug?: string }) {
  const [archive, catalogue] = await Promise.all([getArchive(), getMediaCatalogue()]);
  const items = publicLibrary(archive, catalogue).filter(item => {
    const entry = catalogue[String(item.id)];
    return caseSlug ? entry.cases.includes(caseSlug) : Boolean(topic && entry.topics.includes(topic));
  });
  if (!items.length) return null;
  const selected = [];
  for (const kind of ["video", "pdf", "audio", "document", "image"]) {
    const item = items.find(row => row.kind === kind);
    if (item) selected.push(item);
  }
  for (const item of items) {
    if (selected.length >= 6) break;
    if (!selected.some(row => row.id === item.id)) selected.push(item);
  }
  const themeSlugs = topic ? [topic] : topics.filter(row => row.cases.includes(caseSlug || "")).map(row => row.slug);
  return <section className="section-block">
    <div className="section-heading"><h2>من المكتبة: كتب ومقاطع ومصادر مرتبطة</h2>
      <Link className="text-link" href={`/library?${new URLSearchParams(topic ? { topic } : { q: "" })}`}>تصفّح المكتبة ←</Link>
    </div>
    <div className="library-grid">{selected.map(item => {
      const entry = catalogue[String(item.id)];
      const chapter = entry.chapters.find(row => themeSlugs.includes(row.topic));
      return <LibraryCard key={item.id} item={item} metadata={entry} chapter={chapter} />;
    })}</div>
  </section>;
}
