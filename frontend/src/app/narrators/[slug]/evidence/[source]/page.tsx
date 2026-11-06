import Link from "next/link";
import { notFound } from "next/navigation";
import { narrators,referenceBooks,narratorEvidenceHref } from "@/lib/rijal";
import { narratorScans } from "@/lib/narrator-scans";
import { referenceEdition,referenceFileHref } from "@/lib/reference-assets";
import { HighlightedScan } from "@/components/highlighted-scan";
import { PageHeading } from "@/components/research-ui";
export const dynamic="force-dynamic";
type Params={params:Promise<{slug:string;source:string}>;searchParams:Promise<{quote?:string}>};
export default async function NarratorEvidencePage({params,searchParams}:Params){
 const [{slug,source},query]=await Promise.all([params,searchParams]);
 const person=narrators.find(p=>p.slug===slug);const evidence=person?.evidence.find(e=>`${e.book_id}-${e.page_id}`===source);
 if(!person||!evidence||query.quote!==undefined&&!/^(0|[1-9]\d?)$/.test(query.quote))notFound();
 const index=Number(query.quote||0);const finding=evidence.findings[index];if(!finding)notFound();
 const book=referenceBooks.find(b=>b.id===evidence.book_id)!;
 const scans=narratorScans(slug,source,index,finding);const edition=referenceEdition(String(book.id));
 const position=evidence.context.indexOf(finding.quote);if(position<0)notFound();
 return <><div className="breadcrumb"><Link href="/narrators">الرواة وأقوال النقاد</Link><span>/</span><Link href={`/narrators/${slug}`}>{person.name}</Link><span>/</span><span>موضع الدليل</span></div>
 <PageHeading eyebrow="تحقق من النص ومصدره" title={`${person.name} — ${finding.label}`} description="النص المنقول في سياقه، مع نسبته إلى قائله وبيانات موضعه. التظليل إرشاد إلى الاقتباس، ولا يضيف حكماً إلى المصدر."/>
 <section className="article-section quote-evidence" data-quote-evidence={`${source}/${index}`}><h2>{finding.critic}</h2><blockquote><p><mark>{finding.quote}</mark></p></blockquote><p><strong>{book.title}</strong> · {evidence.locator} · ترجمة {evidence.entry_number}</p><p className="small muted">الطبعة الإلكترونية المنقول عنها: {book.edition}</p>
 <nav className="quote-finding-nav" aria-label="الأقوال المفهرسة في هذا المصدر">{evidence.findings.map((f,i)=><Link key={i} href={narratorEvidenceHref(person,evidence,i)} aria-current={i===index?"page":undefined}>{f.label} — {f.critic}</Link>)}</nav>
 <details className="quote-context"><summary>اقرأ سياق الاقتباس في النص الإلكتروني</summary><p className="source-context">{evidence.context.slice(0,position)}<mark>{finding.quote}</mark>{evidence.context.slice(position+finding.quote.length)}</p></details>
 <a className="text-link" href={scans[0]?.source_url||evidence.url} target="_blank" rel="noopener noreferrer">افتح موضع النص الإلكتروني في الشاملة ↗</a></section>
 {scans.length>0?<section className="article-section"><h2>موضع الاقتباس في الصورة المطبوعة</h2><p>{edition?.scanned_edition}</p><p className="small muted">تُذكر بيانات الطبعة المصورة مستقلة عن الطبعة الإلكترونية؛ قد يختلف ترقيمهما. التظليل طبقة قابلة للإخفاء فوق الصورة الأصلية.</p>{scans.map(scan=><figure className="evidence-scan-figure" key={`${scan.file_id}-${scan.pdf_page}`} data-scan-page={scan.pdf_page}><figcaption>{scan.printed_locator} · صفحة PDF رقم {scan.pdf_page}</figcaption><HighlightedScan src={scan.image} width={scan.width} height={scan.height} rectangles={scan.rectangles} alt={`${book.title} — ${scan.printed_locator} — موضع قول ${finding.critic}`}/><p><Link className="button button-dark" href={`/library/references/${book.id}?file=${scan.file_id}&page=${scan.pdf_page}#read-book`}>اقرأ السياق في الكتاب عند هذه الصفحة ←</Link> <a className="text-link" href={`${referenceFileHref(book.id,scan.file_id)}#page=${scan.pdf_page}&view=FitH`} target="_blank" rel="noopener noreferrer">افتح PDF عند الصفحة ↗</a></p></figure>)}</section>:<section className="article-section"><h2>الصورة المطبوعة</h2><p>النص الإلكتروني محدد ومظلل أعلاه؛ لم يُثبت موضع هذا الاقتباس في النسخة المصورة بعد.</p><Link href={`/library/references/${book.id}`}>افتح بطاقة الكتاب ونسخه ←</Link></section>}
 <p><Link className="text-link" href={`/narrators/${slug}`}>جميع الأقوال والوثائق المرتبطة بـ{person.name} ←</Link></p></>;
}
