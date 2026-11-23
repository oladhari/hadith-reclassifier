import Link from "next/link";
import type { Study } from "@/lib/case-studies";
import { getArchive } from "@/lib/archive";
import { proofHref } from "@/lib/evidence-links";
import { hadithHref } from "@/lib/hadith-query";
import { ProofLink } from "./proof-link";
import { CaseEvidencePreview } from "./case-evidence-preview";

export function CasePassages({ study }: { study: Study }) {
  return study.passages?.map((passage) => (
    <article className="case-passage" key={passage.source}>
      <h3>{passage.source}</h3>
      <p className="case-passage-status">{passage.status}</p>
      <dl>
        <div><dt>الإسناد</dt><dd>{passage.chain}</dd></div>
        <div><dt>المتن أو موضع الشاهد</dt><dd>{passage.text}</dd></div>
      </dl>
      {passage.corpus && <Link className="text-link" href={hadithHref(passage.corpus.collection, passage.corpus.number)}>النص الكامل في قاعدة الأحاديث ←</Link>}
      {passage.citation && <a className="text-link" href={passage.citation.url}
        target={passage.citation.url.startsWith("#") ? undefined : "_blank"}
        rel={passage.citation.url.startsWith("#") ? undefined : "noopener noreferrer"}>
        {passage.citation.label} ←
      </a>}
    </article>
  ));
}

export async function CaseStudyEvidence({ study }: { study: Study }) {
  const ids = [...new Set(study.sections.flatMap(section => section.evidence?.map(item => item.id) ?? []))];
  const [archive, proofLinks] = await Promise.all([
    getArchive(),
    Promise.all(ids.map(async id => [id, await proofHref(id)] as const)),
  ]);
  const links = new Map(proofLinks);
  const media = new Map(archive.map(item => [item.id, item]));
  return (
    <section id="archive-matches" className="article-section case-arguments">
      <h2>شرح الحجة وأدلتها</h2>
      {study.sections.map(section => (
        <section className="case-argument" key={section.title}>
          <h3>{section.title}</h3>
          {section.paragraphs.map(paragraph => <p key={paragraph}>{paragraph}</p>)}
          {section.evidence?.map(evidence => {
            const href = links.get(evidence.id);
            const target = href?.startsWith("/sources/") ? `${href}#media-source-${evidence.id}` : href;
            const kind = media.get(evidence.id)?.kind;
            const page = evidence.page ?? 1;
            const original = `/api/media/${evidence.id}${kind === "pdf" ? `#page=${page}` : ""}`;
            return (
              <div key={evidence.id} id={`evidence-${evidence.id}`} className="case-evidence">
                <h4>{evidence.title}</h4>
                <p>{evidence.explanation}</p>
                {target && (kind === "pdf" || kind === "image") ? (
                  <CaseEvidencePreview title={evidence.title} original={original}
                    pdfPageImage={kind === "pdf" ? `/evidence/cases/${evidence.id}-${page}.webp` : undefined}>
                    <ProofLink href={target} title="بيانات المرجع وصفحاته" action="عرض المرجع" newTab />
                  </CaseEvidencePreview>
                ) : target && <ProofLink href={target} title="بيانات المرجع وصفحاته" action="عرض المرجع" newTab />}
              </div>
            );
          })}
          {section.citations?.length && <ul className="case-citations">{section.citations.map(citation => (
            <li key={citation.url}><a className="text-link" href={citation.url}>{citation.label} ←</a></li>
          ))}</ul>}
        </section>
      ))}
    </section>
  );
}
