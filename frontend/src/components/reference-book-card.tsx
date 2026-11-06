import { bookThemes } from "@/lib/book-themes";
import { referenceEdition } from "@/lib/reference-assets";
import Link from "next/link";
import AssetThumbnail from "./asset-thumbnail";
import type { referenceBooks } from "@/lib/rijal";
export function ReferenceBookCard({book}:{book:typeof referenceBooks[number]}){
 const edition=referenceEdition(String(book.id));
 const volumes=edition?`${edition.volume_count} ${edition.volume_count===1?"مجلد":"مجلدات"}`:"مرجع إلكتروني";
 return <Link className="asset-card reference-series-card" href={`/library/references/${book.id}`} data-reference-book-id={book.id} data-volume-count={edition?.volume_count}>
 <AssetThumbnail src={edition?`/thumbnails/reference-${book.id}.webp`:undefined} kind="pdf" label={book.title}/>
 <div className="asset-info"><span className="eyebrow">{bookThemes[book.theme]} · {volumes}</span><h3>{book.title}</h3><p><strong>{book.author}</strong></p><p className="asset-description">{book.purpose}</p>{edition&&<p className="series-volume-label">{volumes} في مجموعة واحدة · اختر المجلد للقراءة والتنزيل</p>}<small>{book.edition}</small></div>
 </Link>;
}
