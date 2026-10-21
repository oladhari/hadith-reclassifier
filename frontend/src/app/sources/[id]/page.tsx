import Link from "next/link";
import { notFound } from "next/navigation";
import { sourceRecord, sourceTitle } from "@/lib/local-sources";
import { SourceBundle } from "@/components/source-viewer";
import { PageHeading } from "@/components/research-ui";
import { caseEvidence } from "@/lib/public-evidence";
import { cases } from "@/lib/research";
import { topics } from "@/lib/topics";
export const dynamic = "force-dynamic";
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return {
    title: await sourceRecord(Number(id))
      ? await sourceTitle(Number(id))
      : "المرجع غير موجود",
  };
}
export default async function SourcePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const numeric = Number(id);
  if (!/^\d+$/.test(id) || !(await sourceRecord(numeric))) notFound();
  const relatedCases = cases.filter(item => caseEvidence(item.slug).includes(numeric));
  const relatedTopics = topics.filter(topic => topic.cases.some(slug => caseEvidence(slug).includes(numeric)));
  return (
    <>
      <div className="breadcrumb">
        <Link href="/library">مكتبة المصادر</Link>
        <span>/</span>
        <span>{await sourceTitle(numeric)}</span>
      </div>
      <PageHeading
        eyebrow="مرجع داخل الموسوعة"
        title={await sourceTitle(numeric)}
        description="الأصل ومعلوماته والنقول المرتبطة به في مكان واحد. تُستكمل بيانات المرجع بمقابلة الكتاب والطبعة، وتُفصل الوثيقة عن تفسيرها."
      />
      <SourceBundle id={numeric} expanded />
      <section className="article-section">
        <h2>ملفات تستخدم هذا المرجع</h2>
        <div className="reference-uses">
          {relatedCases.map((item) => (
            <Link key={item.slug} href={`/cases/${item.slug}`}>
              {item.title} ←
            </Link>
          ))}
          {relatedTopics.map((topic) => (
            <Link key={topic.slug} href={`/topics/${topic.slug}`}>
              المحور: {topic.title} ←
            </Link>
          ))}
        </div>
        {!relatedCases.length && !relatedTopics.length && (
          <p className="muted">لم يُربط المرجع بملف موضوعي محدد بعد.</p>
        )}
      </section>
    </>
  );
}
