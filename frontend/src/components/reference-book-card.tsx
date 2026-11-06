import Link from "next/link";
import type { referenceBooks } from "@/lib/rijal";
export function ReferenceBookCard({book}:{book:typeof referenceBooks[number]}){
 return <article className="reference-book-card" data-reference-book-id={book.id}><span className="eyebrow">علم الرجال · مرجع إلكتروني{book.scans.length?" ومصور":""}</span><h3><Link href={`/library/references/${book.id}`}>{book.title}</Link></h3><p><strong>{book.author}</strong></p><p>{book.purpose}</p><small>{book.edition}</small><p><Link href={`/library/references/${book.id}`} className="text-link">افتح بطاقة الكتاب وروابط القراءة ←</Link></p></article>;
}
