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

export function CaseReading({ slug }: { slug: string }) {
  const item = (data.cases as Record<string, { title: string; paragraphs: string[] }>)[slug];
  if (!item) return null;
  return (
    <section className="case-reading article-section" id="case-reading">
      <span className="eyebrow">من النص إلى الحجة</span>
      <h2>{item.title}</h2>
      {item.paragraphs.map((text) => <p key={text}>{text}</p>)}
      <a href="#archive-matches" className="text-link">اقرأ كل دليل ووجه الاستدلال به ↓</a>
    </section>
  );
}
