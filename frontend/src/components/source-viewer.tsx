import { getBibliography } from "@/lib/local-sources";
/* eslint-disable @next/next/no-img-element -- Preserve the original source scan. */
import Link from "next/link";
import { EvidenceReading } from "./evidence-reading";
import { kindNames, fileSize, type ArchiveItem } from "@/lib/archive";
import { sourceFiles, sourceRecord, sourceTitle } from "@/lib/local-sources";
import { evidenceLabels } from "@/lib/public-evidence";
import { getMediaCatalogue } from "@/lib/media-catalogue";
import thumbnails from "@/content/thumbnails.json";
import { ImageCollection } from "./image-collection";
export async function MediaOriginal({ item }: { item: ArchiveItem }) {
  const sources = await getBibliography();
  const metadata = (await getMediaCatalogue())[String(item.id)];
  const src = metadata?.asset_url || `/api/media/${item.id}`;
  return (
    <div className={`source-original ${item.kind}`}>
      <div className="source-file-heading">
        <strong>
          {metadata?.visible ? metadata.title : sources[item.id]?.title || evidenceLabels[item.id] || `${kindNames[item.kind]} الدليل`}
        </strong>
        {metadata?.visible && <p>{metadata.description}</p>}
        {sources[item.id] && <p>{sources[item.id].detail}</p>}
      </div>
      {metadata?.collection_images ? <ImageCollection images={metadata.collection_images} /> : item.kind === "image" ? (
        <a href={src} target="_blank" rel="noreferrer">
          <img
            src={src}
            alt={sources[item.id]?.title || "صورة الدليل؛ افتحها لقراءة الصفحة كاملة"}
            loading="lazy"
          />
        </a>
      ) : item.kind === "video" ? (
        <video controls playsInline preload="none" src={src} poster={(thumbnails as Record<string, string>)[item.id]}>
          <track kind="captions" src={`/transcripts/${metadata?.canonical_id || item.id}.vtt`} srcLang="ar" label="العربية — تفريغ آلي" />
          استخدم رابط تنزيل الأصل لفتح هذا الفيديو.
        </video>
      ) : item.kind === "audio" ? (
        <audio controls preload="none" src={src} />
      ) : item.kind === "pdf" ? (
        <iframe src={src} title={await sourceTitle(item.id)} loading="lazy" />
      ) : (
        <p>الوثيقة متاحة للتنزيل وفتحها ببرنامجها المناسب.</p>
      )}
      <div className="source-file-actions">
        {!metadata?.collection_images && <a href={metadata?.asset_url ? src : `${src}?download=1`} download={metadata?.asset_url ? `${metadata.title.replace(/[\\/:*?"<>|]/g, "-")}.pdf` : undefined}>{metadata?.asset_url ? "تنزيل الملف المجمّع" : "تنزيل الأصل"} • {fileSize(metadata?.asset_size || item.size)}</a>}
        <Link href={`/library/${item.id}`}>
          فتح {metadata?.collection_images ? "مجموعة الصور" : kindNames[item.kind]} في صفحة مستقلة ←
        </Link>
      </div>
      <EvidenceReading id={item.id} />
    </div>
  );
}
export async function SourceBundle({
  id,
  expanded = true,
}: {
  id: number;
  expanded?: boolean;
}) {
  const sources = await getBibliography();
  const record = await sourceRecord(id);
  if (!record) return null;
  const files = await sourceFiles(id);
  return (
    <article className="source-bundle" id={`source-${id}`}>
      <div className="source-bundle-heading">
        <div>
          <span className="eyebrow">
            {files.length
              ? "أصل محفوظ في مكتبة الموسوعة"
              : "نقول تحتاج ربطًا بالأصل"}
          </span>
          <h3>
            <Link href={`/sources/${id}`}>{await sourceTitle(id)}</Link>
          </h3>
        </div>

      </div>
      {sources[id] && <p className="source-bibliography">{sources[id].detail}</p>}
      {files.length > 0 && (
        <div className="source-open" data-expanded={expanded}>
          {files.map((item) => (
            <MediaOriginal item={item} key={item.id} />
          ))}
        </div>
      )}
      {record.quotes.length > 0 && (
        <details className="source-extracts">
          <summary>نقول نصية مرتبطة — تحتاج مطابقة بالأصل</summary>
          <p className="muted">
            مقاطع منقولة من مواد الجمع، وليست تفريغًا مراجعًا للوثيقة أو نسبة
            محققة إلى مؤلف. يُرجع إلى الأصل المصوّر عند توفره.
          </p>
          {record.quotes.map((quote, index) => (
            <blockquote key={index}>{quote}</blockquote>
          ))}
        </details>
      )}
      {!files.length && !record.quotes.length && (
        <p className="muted">
          سُجلت هذه الإشارة ضمن خطة البحث. لم يُجهّز منها اقتباس صالح للنشر أو
          يُربط بها أصل مستقل بعد.
        </p>
      )}
      <Link href={`/sources/${id}`} className="text-link">
        تفاصيل المرجع ومواضع استخدامه ←
      </Link>
    </article>
  );
}
