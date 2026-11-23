import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowUpLeft } from "lucide-react";
import { cases } from "@/lib/research";
import { topics } from "@/lib/topics";
import { caseStudies } from "@/lib/case-studies";
import { CasePassages, CaseStudyEvidence } from "@/components/case-study";
import { StatusNote } from "@/components/research-ui";
import { ThemedLibrary } from "@/components/themed-library";
export function generateStaticParams() {
  return cases.map((c) => ({ slug: c.slug }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return { title: cases.find((c) => c.slug === slug)?.title || "ملف بحث" };
}
export default async function CasePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const item = cases.find((c) => c.slug === slug);
  if (!item) notFound();
  const study = caseStudies[slug];
  return (
    <>
      <div className="breadcrumb">
        <Link href="/cases">القضايا والأدلة</Link>
        <span>/</span>
        <span>{item.category}</span>
      </div>
      <div className="case-layout">
        <aside className="case-sidebar">
          <span className="eyebrow">في هذا الملف</span>
          <a href="#question">موضع النزاع</a>
          {study.passages?.length ? <a href="#texts">النص والتخريج</a> : null}
          <a href="#archive-matches">الأدلة وشرحها</a>
          <a href="#review">استكمال البحث</a>
        </aside>
        <article className="case-body">
          <div className="topic-breadcrumb">
            المحور:{" "}
            {topics
              .filter((topic) => topic.cases.includes(item.slug))
              .map((topic) => (
                <Link key={topic.slug} href={`/topics/${topic.slug}`}>
                  {topic.title} ←{" "}
                </Link>
              ))}
          </div>
          <div className="page-heading">
            <span className="eyebrow">
              {item.label} <span className="inline-status">قيد البحث</span>
            </span>
            <h1>{item.title}</h1>
            <p>{item.subtitle}</p>
          </div>
          <section className="question-box" id="question">
            <h2>موضع النزاع</h2>
            <p>{study.finding}</p>
          </section>
          {study.passages?.length ? (
            <section id="texts" className="article-section">
              <h2>النص والتخريج</h2>
              <CasePassages study={study} />
            </section>
          ) : null}
          <CaseStudyEvidence study={study} />
          <section id="review" className="article-section">
            <h2>استكمال البحث</h2>
            <StatusNote>{item.note}</StatusNote>
            <div className="related-actions">
              <Link
                className="button button-dark"
                href={`/corpus?q=${encodeURIComponent(item.terms[0])}`}
              >
                ابحث في نصوص الأحاديث <ArrowUpLeft size={17} />
              </Link>
              <Link className="text-link" href="/methodology">
                اقرأ طبقات الفحص
              </Link>
            </div>
          </section>
          <ThemedLibrary caseSlug={slug} />
        </article>
      </div>
    </>
  );
}
