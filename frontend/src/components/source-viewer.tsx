/* eslint-disable @next/next/no-img-element -- Preserve the original source scan. */
import Link from "next/link";
import { EvidenceReading } from "./evidence-reading";
import { kindNames, fileSize, type ArchiveItem } from "@/lib/archive";
import { sourceFiles, sourceRecord, sourceTitle } from "@/lib/local-sources";
import { evidenceLabels } from "@/lib/public-evidence";
import { sources } from "@/lib/research";
export function MediaOriginal({ item }: { item: ArchiveItem }) {
  const src = `/api/media/${item.id}`;
  return (
    <div className={`source-original ${item.kind}`}>
      <div className="source-file-heading">
        <strong>
          {sources[item.id]?.title || evidenceLabels[item.id] || `${kindNames[item.kind]} الدليل`}
        </strong>
        {sources[item.id] && <p>{sources[item.id].detail}</p>}
      </div>
      {item.kind === "image" ? (
        <a href={src} target="_blank" rel="noreferrer">
          <img
            src={src}
            alt={sources[item.id]?.title || "صورة الدليل؛ افتحها لقراءة الصفحة كاملة"}
            loading="lazy"
          />
        </a>
      ) : item.kind === "video" ? (
        <video controls playsInline preload="none" src={src}>
          <track kind="captions" />
          استخدم رابط تنزيل الأصل لفتح هذا الفيديو.
        </video>
      ) : item.kind === "audio" ? (
        <audio controls preload="none" src={src} />
      ) : item.kind === "pdf" ? (
        <iframe src={src} title={sourceTitle(item.id)} loading="lazy" />
      ) : (
        <p>الوثيقة متاحة للتنزيل وفتحها ببرنامجها المناسب.</p>
      )}
      <div className="source-file-actions">
        <a href={`${src}?download=1`}>تنزيل الأصل • {fileSize(item.size)}</a>
        <Link href={`/library/${item.id}`}>
          فتح {kindNames[item.kind]} في صفحة مستقلة ←
        </Link>
      </div>
      <EvidenceReading id={item.id} />
    </div>
  );
}
export function SourceBundle({
  id,
  expanded = true,
}: {
  id: number;
  expanded?: boolean;
}) {
  const record = sourceRecord(id);
  if (!record) return null;
  const files = sourceFiles(id);
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
            <Link href={`/sources/${id}`}>{sourceTitle(id)}</Link>
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
