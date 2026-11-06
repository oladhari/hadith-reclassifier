import { referenceEdition } from "@/lib/reference-assets";
import Link from "next/link";
import type { referenceBooks } from "@/lib/rijal";
export function ReferenceBookCard({book}:{book:typeof referenceBooks[number]}){
 const edition=referenceEdition(String(book.id));
 return <article className="reference-book-card" data-reference-book-id={book.id}><span className="eyebrow">علم الرجال · {edition?`نسخة PDF محفوظة · ${edition.file_count} ملف`:"مرجع إلكتروني"}</span><h3><Link href={`/library/references/${book.id}`}>{book.title}</Link></h3><p><strong>{book.author}</strong></p><p>{book.purpose}</p><small>{book.edition}</small><p><Link href={`/library/references/${book.id}`} className="text-link">افتح الكتاب واقرأ النسخة المحفوظة ←</Link></p></article>;
}
