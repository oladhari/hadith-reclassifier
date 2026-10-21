import Link from "next/link";
import profile from "@/content/filter-layers.json";
import studies from "@/content/filter-case-studies.json";
import evidence from "@/content/public-evidence.json";
import { PageHeading } from "@/components/research-ui";
import { ar, cases } from "@/lib/research";
export const metadata = { title: "المنهج وطبقات فحص الحديث" };
export default function Methodology() {
  const groups = [...new Set(profile.layers.map(layer => layer.group))];
  const titles = evidence.labels as Record<string, string>;
  return <>
    <PageHeading eyebrow="من النص إلى الحكم المعلّل" title="طبقات فحص الحديث" description="يُفحص متن الرواية في ضوء صريح القرآن، ويُدرس كل إسناد ولفظ بأدلته. لكل ملاحظة موضع محدد وسبب ومصدر، ولكل نتيجة نطاقها." />
    <section className="quran-gate" id="quran-gate">
      <span className="eyebrow">الأصل المقدّم في فحص المتن</span>
      <h2>صريح القرآن الكريم هو الميزان الأول</h2>
      <p>لا تجبر سلامة الإسناد تعارضًا قائمًا مع صريح القرآن. تُحدَّد الآية والعبارة المقابلة في الحديث، ويُحرَّر وجه التعارض، ويُفحص دليل أي تفسير أو جمع مقترح. ويبقى موضع الاعتراض ظاهرًا حتى تُراجع حجته.</p>
      <div className="quran-comparison-steps"><span>الآية وموضعها</span><span>لفظ الحديث</span><span>وجه التعارض</span><span>التفسير ودليله</span><span>النتيجة المعلّلة</span></div>
    </section>
    <div className="method-intro"><h2>{ar(profile.layers.length)} طبقة تتكامل في الفحص</h2><p>قد تؤثر الملاحظة في طريق واحد أو زيادة محددة، فتُدرس الطرق والألفاظ الأخرى في مواضعها. وشروط الانتقاء الخاصة بالموسوعة تُذكر باسمها وأدلتها، مع فصلها عن نسبة القول إلى النقاد.</p></div>
    {groups.map(group => <section className="filter-group" key={group}>
      <h2>{group}</h2>
      <div className="method-grid">{profile.layers.filter(layer => layer.group === group).map(layer => <article className={`method-card ${layer.key === "quran_explicit" ? "method-card-quran" : ""}`} key={layer.code} id={`layer-${layer.key}`}>
        <span>{layer.code.slice(1)}</span><h3>{layer.title}</h3><p>{layer.question}</p>
        <details><summary>معايير الفحص</summary><ul>{layer.checks.map(check => <li key={check}>{check}</li>)}</ul></details>
        {layer.related_cases.length > 0 && <div className="filter-case-links">{layer.related_cases.slice(0, 2).map(slug => <Link href={`/cases/${slug}`} key={slug}>{cases.find(item => item.slug === slug)?.title || "ملف مرتبط"} ←</Link>)}</div>}
      </article>)}</div>
    </section>)}
    <section className="article-section" id="filter-case-studies"><h2>أمثلة تطبيقية على مواضع الاعتراض</h2><p>نماذج تربط السؤال بالأدلة وبطبقات الفحص المناسبة. ورود المثال هنا يحدّد ما يُبحث فيه، ولا يختصر التحقيق في حكم مسبق على جميع طرقه.</p>
      <div className="filter-studies">{studies.map(study => <article className="filter-study" key={study.slug}>
        <h3>{study.title}</h3><p>{study.question}</p><ul>{study.checks.map(check => <li key={check}>{check}</li>)}</ul>
        <div className="filter-layer-tags">{study.layer_keys.map(key => <a href={`#layer-${key}`} key={key}>{profile.layers.find(l => l.key === key)?.title}</a>)}</div>
        <Link className="text-link" href={`/cases/${study.case_slug}`}>افتح ملف الأدلة ←</Link>
        {study.source_media.length > 0 && <details><summary>صفحات المصادر المرتبطة</summary><div className="filter-reference-list">{study.source_media.map(id => <Link key={id} href={`/library/${id}`}>{titles[id] || "صفحة من المصدر المصوّر"} ←</Link>)}</div></details>}
        {study.corpus_candidates.length > 0 && <details><summary>مواضع الألفاظ للمقارنة ({ar(study.corpus_candidates.length)})</summary><p className="muted">تُقارن ألفاظ هذه المواضع وأسانيدها قبل نقل الحكم من طريق إلى آخر.</p><div className="filter-reference-list">{study.corpus_candidates.map(item => <Link key={item.hadith_id} href={`/corpus?collection=${item.collection}&id=${encodeURIComponent(item.number)}`}>{item.collection_title} • {item.number} ←</Link>)}</div></details>}
      </article>)}</div>
    </section>
    <section className="method-intro"><h2>من الملاحظة إلى الاعتماد</h2><p>النقص في البيانات يبقى غير محسوم. والتعارض بين الأدلة يُعرض للمراجعة، مع حفظ القول السابق وسبب تغييره. اعتماد الحديث للكتاب مرحلة مستقلة تأتي بعد استكمال ملفه ومراجعته.</p><Link href="/corpus" className="button button-dark">تصفّح نصوص الحديث ←</Link></section>
  </>;
}
