import Link from "next/link";
import { PageHeading } from "@/components/research-ui";
import { getResearchBundles } from "@/lib/research-bundles";
export const dynamic = "force-dynamic";
export const metadata = { title: "مجموعات الشواهد والشرح الموضوعي" };
export default async function ThemesPage() {
  const bundles = await getResearchBundles();
  return <><PageHeading eyebrow="من السؤال إلى الوثيقة" title="مجموعات الشواهد والشرح الموضوعي" description="لكل موضوع مجموعة من الوثائق والصور وملفات PDF، مع شرح محرر من تعليقات المصدر وروابط إلى الأصول. جمع الشواهد في موضوع واحد لا يعني تساويها في الدلالة أو صحة النسبة." />
    <div className="case-grid">{bundles.map(b => <Link className="case-card" href={`/themes/${b.slug}`} key={b.slug}>
      <span className="eyebrow">{b.items.length.toLocaleString("ar-u-nu-latn")} وثيقة وشاهد</span><h2>{b.title}</h2><p>{b.explanation}</p><span className="text-link">اقرأ الشرح وافتح الشواهد ←</span>
    </Link>)}</div></>;
}
