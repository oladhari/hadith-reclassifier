/* eslint-disable @next/next/no-img-element -- Original archival images are served without alteration. */
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowUpLeft, BookOpen } from "lucide-react";
import { cases, sources } from "@/lib/research";
import { caseMatches, topics } from "@/lib/topics";
import { ArchiveMatches } from "@/components/archive-matches";
import { CaseReading } from "@/components/evidence-reading";
import { StatusNote } from "@/components/research-ui";
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
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { slug } = await params;
  const { page = "1" } = await searchParams;
  const item = cases.find((c) => c.slug === slug);
  if (!item) notFound();
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
          <a href="#question">السؤال وموضع النزاع</a>
          <a href="#path">مواضع النظر</a>
          <a href="#archive-matches">الأدلة وشرحها</a>
          <a href="#review">حالة المراجعة</a>
          <div className="sidebar-note">
            <BookOpen size={24} />
            <p>افصل بين النص الأصلي، وتفسير الناقل، ونتيجة الباحث.</p>
          </div>
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
            <span className="eyebrow">السؤال في دقيقة</span>
            <h2>{item.question}</h2>
            <p>{item.intro}</p>
          </section>
          <CaseReading slug={item.slug} />
          <section id="path" className="article-section">
            <h2>مواضع النظر في الرواية</h2>
            <ol className="research-steps">
              {item.steps.map((s, i) => (
                <li key={s}>
                  <span>0{i + 1}</span>
                  <p>{s}</p>
                </li>
              ))}
            </ol>
          </section>
          {item.evidence.length > 0 && <section id="evidence" className="article-section">
            <div className="section-heading">
              <h2>ارجع إلى الأصل</h2>
              <span className="muted">المواد المحفوظة ذات الصلة</span>
            </div>
            {item.evidence.map((id) => (
              <div className="source-detail" key={id}>
                <div className="source-text">
                  <span className="source-number">نص من المصدر</span>
                  <h3>{sources[id].title}</h3>
                  <blockquote>«{sources[id].quote}»</blockquote>
                  <p>{sources[id].detail}</p>
                  <p className="small">
                    اقتباس جزئي مطابق بصريًا للصورة، وليس تفريغًا كاملًا. لا
                    تُعدّ التعليقات الملوّنة أو تعليقات المحقق قولًا للمؤلف دون
                    تمييز.
                  </p>
                  <Link className="text-link" href={`/library/${id}`}>
                    افتح الصورة كاملة <ArrowUpLeft size={17} />
                  </Link>
                </div>
                <Link className="source-preview" href={`/library/${id}`}>
                  <img
                    src={`/evidence/${id}.jpg`}
                    alt={`صورة المصدر: ${sources[id].title}`}
                    loading="lazy"
                  />
                </Link>
              </div>
            ))}
          </section>}
          <ArchiveMatches
            matches={caseMatches(item.slug)}
            extraIds={[...item.posts, ...item.evidence]}
            page={Number.parseInt(page) || 1}
            baseURL={`/cases/${item.slug}`}
          />
          <section id="review" className="article-section">
            <h2>تنبيه عند قراءة الأدلة</h2>
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
        </article>
      </div>
    </>
  );
}
