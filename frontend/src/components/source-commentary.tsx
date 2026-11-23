import Link from "next/link";
import { caseStudies } from "@/lib/case-studies";
import { getMediaCatalogue } from "@/lib/media-catalogue";
import { cases } from "@/lib/research";

export async function SourceCommentary({ id }: { id: number }) {
  const entry = (await getMediaCatalogue())[String(id)];
  if (entry?.manual_video_hidden) return null;

  const originals = new Set([id, entry?.canonical_id, ...(entry?.collection_sources?.map(source => source.id) ?? [])]);
  const readings = cases.flatMap(item => caseStudies[item.slug].sections.flatMap(section =>
    (section.evidence ?? []).filter(evidence => originals.has(evidence.id)).map(evidence => ({ item, evidence })),
  ));
  if (readings.length) {
    return (
      <section className="evidence-reading source-commentary" data-source-commentary={id}>
        <h2>موضع الشاهد في القضية</h2>
        {readings.map(({ item, evidence }) => (
          <div key={`${item.slug}-${evidence.id}`}>
            <h3>{evidence.title}</h3>
            <p>{evidence.explanation}</p>
            <div className="related-actions">
              {evidence.page && <a className="text-link" href={`/api/media/${evidence.id}#page=${evidence.page}`}>صفحة {evidence.page} من ملف PDF الأصلي ←</a>}
              <Link className="text-link" href={`/cases/${item.slug}#evidence-${evidence.id}`}>{item.title} ←</Link>
            </div>
          </div>
        ))}
      </section>
    );
  }

  if (!entry?.visible || !entry.explanations?.length) return null;
  return <section className="evidence-reading source-commentary" data-source-commentary={entry.canonical_id}>
    <span className="eyebrow">شرح الوثيقة ووجه الاستدلال</span>
    <h2>قراءة في سياق الشاهد</h2>
    {entry.explanations.map((row, index) => <div key={index}><p>{row.text}</p><p className="commentary-attribution">{row.attribution}</p></div>)}
  </section>;
}
