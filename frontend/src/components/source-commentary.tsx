import { getMediaCatalogue } from "@/lib/media-catalogue";
export async function SourceCommentary({ id }: { id: number }) {
  const entry = (await getMediaCatalogue())[String(id)];
  if (!entry?.visible || !entry.explanations?.length) return null;
  return <section className="evidence-reading source-commentary" data-source-commentary={entry.canonical_id}>
    <span className="eyebrow">شرح الوثيقة ووجه الاستدلال</span>
    <h2>قراءة في سياق الشاهد</h2>
    {entry.explanations.map((row, index) => <div key={index}><p>{row.text}</p><p className="commentary-attribution">{row.attribution}</p></div>)}
  </section>;
}
