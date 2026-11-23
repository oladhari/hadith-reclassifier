import data from "@/content/evidence-analysis.json";

type Reading = {
  title: string;
  reading: string;
  argument: string;
  quotes: { text: string; speaker: string }[];
};

export function EvidenceReading({ id }: { id: number }) {
  const item = (data.media as Record<string, Reading>)[id];
  if (!item) return null;
  return (
    <section className="evidence-reading" id={`reading-${id}`} data-evidence-analysis={id}>
      <span className="eyebrow">قراءة الدليل</span>
      <h3>{item.title}</h3>
      <p>{item.reading}</p>
      <div className="evidence-passages">
        {item.quotes.map((quote) => (
          <figure key={quote.text}>
            <blockquote>«{quote.text}»</blockquote>
            <figcaption>{quote.speaker} • مقتطف من الصورة</figcaption>
          </figure>
        ))}
      </div>
      <h4>وجه الاستدلال</h4>
      <p>{item.argument}</p>
    </section>
  );
}
