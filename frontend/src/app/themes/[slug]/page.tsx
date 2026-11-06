import Link from "next/link";
import { notFound } from "next/navigation";
import { getResearchBundles } from "@/lib/research-bundles";
import { getArchive } from "@/lib/archive";
import { getMediaCatalogue } from "@/lib/media-catalogue";
import { topics } from "@/lib/topics";
import { PageHeading } from "@/components/research-ui";
import { LibraryCard } from "@/components/library-card";
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return { title: (await getResearchBundles()).find(b => b.slug === slug)?.title || "المجموعة غير موجودة" };
}
export default async function ThemePage({ params, searchParams }: { params: Promise<{ slug: string }>; searchParams: Promise<{ page?: string }> }) {
  const [{ slug }, query, bundles, archive, catalogue] = await Promise.all([params, searchParams, getResearchBundles(), getArchive(), getMediaCatalogue()]);
  const bundle = bundles.find(b => b.slug === slug);
  if (!bundle) notFound();
  const items = bundle.items.flatMap(id => { const item = archive.find(a => a.id === id); return item ? [item] : []; });
  const pages = Math.max(1, Math.ceil(items.length / 18));
  const page = Math.min(pages, Math.max(1, Number.parseInt(query.page || "1") || 1));
  const topic = topics.find(t => t.slug === bundle.topic);
  return <><div className="breadcrumb"><Link href="/themes">مجموعات الشواهد</Link><span>/</span><span>{bundle.title}</span></div>
    <PageHeading eyebrow={`${items.length.toLocaleString("ar")} وثيقة وشاهد`} title={bundle.title} description="اقرأ تفسير المصدر، ثم قارن الروايات والألفاظ في الوثائق المصوّرة. تُعرض المواد مستقلة عن شرحها، وتبقى النسخ والتعليقات المختلفة محفوظة." />
    <section className="evidence-reading theme-explanation" data-theme-explanation={slug}><span className="eyebrow">شرح موضوعي محرر من تعليقات المصدر</span><h2>سياق الشواهد ووجه الاستدلال</h2><p>{bundle.explanation}</p>
      <p className="commentary-attribution">هذا شرح لموقف صاحب التعليق، وليس نصًا من الكتاب المصوّر أو حكمًا علميًا معتمدًا من الموسوعة.</p>
      {topic && <Link className="text-link" href={`/topics/${topic.slug}`}>المحور العام: {topic.title} ←</Link>}</section>
    <div className="section-heading"><h2>الوثائق والشواهد المرتبطة</h2><Link href={`/library?section=all&topic=${bundle.topic}`} className="text-link">مواد المحور في المكتبة ←</Link></div>
    <div className="library-grid">{items.slice((page-1)*18,page*18).map(item => <LibraryCard key={item.id} item={item} metadata={catalogue[String(item.id)]} />)}</div>
    {pages > 1 && <nav className="pagination" aria-label="صفحات الشواهد">{page > 1 && <Link href={`/themes/${slug}?page=${page-1}`}>السابق</Link>}<span>{page.toLocaleString("ar")} / {pages.toLocaleString("ar")}</span>{page < pages && <Link href={`/themes/${slug}?page=${page+1}`}>التالي</Link>}</nav>}
  </>;
}
