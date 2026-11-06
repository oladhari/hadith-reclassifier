import Link from "next/link";
import { getResearchBundles } from "@/lib/research-bundles";
export async function BundleLinks({ topic, caseSlug, ids }: { topic?: string; caseSlug?: string; ids?: string[] }) {
  const bundles = (await getResearchBundles()).filter(b => ids ? ids.includes(b.slug) : caseSlug ? b.cases.includes(caseSlug) : topic ? b.topic === topic : true);
  if (!bundles.length) return null;
  return <section className="section-block theme-bundle-links" data-theme-bundles>
    <div className="section-heading"><h2>شواهد مجمّعة بحسب الموضوع</h2><Link className="text-link" href="/themes">جميع المجموعات ←</Link></div>
    <div className="reference-uses">{bundles.map(b => <Link href={`/themes/${b.slug}`} key={b.slug}>{b.title} <span>({b.items.length.toLocaleString("ar")})</span> ←</Link>)}</div>
  </section>;
}
