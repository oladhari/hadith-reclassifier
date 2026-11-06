import { referenceEdition,referenceFileHref } from "@/lib/reference-assets";
import Link from "next/link";
import { notFound } from "next/navigation";
import { referenceBooks,narrators } from "@/lib/rijal";
import { PageHeading } from "@/components/research-ui";
export const dynamic="force-dynamic";
type Params={params:Promise<{id:string}>};
export async function generateMetadata({params}:Params){const {id}=await params;return {title:referenceBooks.find(b=>String(b.id)===id)?.title||"الكتاب غير موجود"};}
export default async function ReferencePage({params,searchParams}:Params&{searchParams:Promise<{file?:string}>}){
 const query=await searchParams;
 const {id}=await params;const book=referenceBooks.find(b=>String(b.id)===id);if(!book)notFound();const people=narrators.filter(n=>n.evidence.some(e=>e.book_id===book.id));
 const edition=referenceEdition(id);const selected=edition?.files.find(f=>f.id===(query.file||edition.files[0]?.id));
 if(query.file&&!selected)notFound();
 return <><div className="breadcrumb"><Link href="/library?section=books">الكتب والبحوث</Link><span>/</span><Link href="/library?section=books&theme=rijal">علم الرجال</Link><span>/</span><span>{book.title}</span></div>
 <PageHeading eyebrow="علم الرجال والجرح والتعديل" title={book.title} description={book.purpose}/>
 <section className="article-section"><dl className="metadata-list"><div><dt>المؤلف</dt><dd>{book.author}</dd></div><div><dt>الطبعة الإلكترونية المرجعية</dt><dd>{book.edition}</dd></div><div><dt>المتاح للقراءة</dt><dd>{edition?`${edition.file_count} ملف PDF محفوظ في مكتبتنا · ${edition.pages} صفحة مصورة`:book.scans.length?"نص إلكتروني، وتسعة ملفات مصورة محفوظة مع أصلها":"نص إلكتروني في المكتبة الشاملة"}</dd></div></dl><a className="text-link" href={book.url} target="_blank" rel="noopener noreferrer">النص الإلكتروني المرجعي في الشاملة ↗</a></section>
 {edition&&selected&&<section className="article-section reference-reader" id="read-book" data-hosted-reference={book.id}>
 <h2>اقرأ النسخة المحفوظة في مكتبتنا</h2><p><strong>بيانات النسخة المصورة:</strong> {edition.scanned_edition}</p><p>{edition.edition_note}</p>
 <form action={`/library/references/${id}`} className="filter-bar"><label>المجلد أو الملف<select name="file" defaultValue={selected.id}>{edition.files.map(f=><option key={f.id} value={f.id}>{f.label} — {f.pages} صفحة</option>)}</select></label><button className="button button-dark">افتح الملف</button></form>
 <p><a href={referenceFileHref(id,selected.id)} target="_blank" rel="noopener noreferrer" className="button button-outline">افتح PDF في نافذة مستقلة أو نزّله ↗</a></p>
 <iframe title={`${book.title} — ${selected.label}`} src={`${referenceFileHref(id,selected.id)}#view=FitH`} className="reference-pdf-viewer"/>
 <details><summary>جميع الملفات المتاحة ({edition.file_count})</summary><ol>{edition.files.map(f=><li key={f.id}><Link href={`/library/references/${id}?file=${f.id}#read-book`}>{f.label}</Link> · {f.pages} صفحة · <a href={referenceFileHref(id,f.id)} target="_blank" rel="noopener noreferrer">افتح PDF ↗</a></li>)}</ol></details>
 </section>}
 {book.scans.length>0&&<section className="article-section"><h2>الملفات المصورة</h2><p>{book.scan_note}</p><p>نسخ محفوظة في R2 ومقابلة ببصمات ملفات المصدر. روابط توثيق الأصل التالية تفتح Internet Archive؛ القراءة من نسختنا متاحة في العارض أعلاه.</p><ul>{book.scans.map(scan=><li key={scan.part}><a href={scan.url} target="_blank" rel="noopener noreferrer">الملف المصور {scan.part} — PDF ↗</a></li>)}</ul></section>}
 <section className="article-section"><h2>التراجم المرتبطة بهذا الكتاب في الفهرس</h2>{people.length?<ul>{people.map(person=><li key={person.slug}><Link href={`/narrators/${person.slug}`}>{person.name}</Link></li>)}</ul>:<p>أضيف مرجع الكتاب؛ لم تُنشر له تراجم في الدفعة الحالية بعد.</p>}<Link href={`/narrators?source_book=${book.id}`} className="text-link">افتح جدول النقول من هذا المصدر ←</Link></section>
 </>;
}
