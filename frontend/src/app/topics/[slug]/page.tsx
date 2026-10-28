export const dynamic = "force-dynamic";
import Link from "next/link";
import { notFound } from "next/navigation";
import { topics } from "@/lib/topics";
import { cases } from "@/lib/research";
import { CaseCard, PageHeading } from "@/components/research-ui";
import { ArchiveMatches } from "@/components/archive-matches";
import { ThemedLibrary } from "@/components/themed-library";
export function generateStaticParams() {
  return topics.map((topic) => ({ slug: topic.slug }));
}
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  return {
    title: topics.find((t) => t.slug === slug)?.title || "محور الموسوعة",
  };
}
export default async function TopicPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { slug } = await params;
  const { page = "1" } = await searchParams;
  const topic = topics.find((t) => t.slug === slug);
  if (!topic) notFound();
  const related = topic.cases
    .map((slug) => cases.find((c) => c.slug === slug)!)
    .filter(Boolean);
  return (
    <>
      <div className="breadcrumb">
        <Link href="/topics">محاور الموسوعة</Link>
        <span>/</span>
        <span>{topic.title}</span>
      </div>
      <PageHeading
        eyebrow="القضايا والروايات والأدلة"
        title={topic.title}
        description={topic.description}
      />
      <div className="section-heading">
        <h2>الملفات المرتبطة بالمحور</h2>

      </div>
      <div className="case-grid">
        {related.map((item) => (
          <CaseCard key={item.slug} item={item} />
        ))}
      </div>
      <ArchiveMatches
        matches={topic}
        extraIds={related.flatMap((item) => [...item.posts, ...item.evidence])}
        page={Number.parseInt(page) || 1}
        baseURL={`/topics/${slug}`}
      />
      <ThemedLibrary topic={slug} />

    </>
  );
}
