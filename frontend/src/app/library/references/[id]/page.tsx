import Link from "next/link";
import { notFound } from "next/navigation";
import { referenceBooks,narrators } from "@/lib/rijal";
import { PageHeading } from "@/components/research-ui";
export const dynamic="force-dynamic";
type Params={params:Promise<{id:string}>};
export async function generateMetadata({params}:Params){const {id}=await params;return {title:referenceBooks.find(b=>String(b.id)===id)?.title||"الكتاب غير موجود"};}
export default async function ReferencePage({params}:Params){
 const {id}=await params;const book=referenceBooks.find(b=>String(b.id)===id);if(!book)notFound();const people=narrators.filter(n=>n.evidence.some(e=>e.book_id===book.id));
 return <><div className="breadcrumb"><Link href="/library?section=books">الكتب والبحوث</Link><span>/</span><Link href="/library?section=books&theme=rijal">علم الرجال</Link><span>/</span><span>{book.title}</span></div>
 <PageHeading eyebrow="علم الرجال والجرح والتعديل" title={book.title} description={book.purpose}/>
 <section className="article-section"><dl className="metadata-list"><div><dt>المؤلف</dt><dd>{book.author}</dd></div><div><dt>الطبعة الإلكترونية المرجعية</dt><dd>{book.edition}</dd></div><div><dt>المتاح للقراءة</dt><dd>{book.scans.length?"نص إلكتروني، وتسعة ملفات مصورة محفوظة مع أصلها":"نص إلكتروني في المكتبة الشاملة"}</dd></div></dl><a className="button button-dark" href={book.url} target="_blank" rel="noopener noreferrer">اقرأ الكتاب وابحث فيه بالشاملة ↗</a></section>
 {book.scans.length>0&&<section className="article-section"><h2>الملفات المصورة</h2><p>{book.scan_note}</p><p>نسخ محفوظة في R2 ومقابلة ببصمات ملفات المصدر. روابط القراءة والتنزيل التالية تفتح الملفات الأصلية في Internet Archive.</p><ul>{book.scans.map(scan=><li key={scan.part}><a href={scan.url} target="_blank" rel="noopener noreferrer">الملف المصور {scan.part} — PDF ↗</a></li>)}</ul></section>}
 <section className="article-section"><h2>التراجم المرتبطة بهذا الكتاب في الفهرس</h2>{people.length?<ul>{people.map(person=><li key={person.slug}><Link href={`/narrators/${person.slug}`}>{person.name}</Link></li>)}</ul>:<p>أضيف مرجع الكتاب؛ لم تُنشر له تراجم في الدفعة الحالية بعد.</p>}<Link href={`/narrators?source_book=${book.id}`} className="text-link">افتح جدول النقول من هذا المصدر ←</Link></section>
 </>;
}
