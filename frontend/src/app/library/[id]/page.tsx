/* eslint-disable @next/next/no-img-element -- Original archival images are served without alteration. */
import Link from "next/link";
import { notFound } from "next/navigation";
import { EvidenceReading } from "@/components/evidence-reading";
import { Download } from "lucide-react";
import { archive, assetTitle, kindNames, fileSize } from "@/lib/archive";
import { sources } from "@/lib/research";
import { PageHeading, StatusNote } from "@/components/research-ui";
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const item = archive.find((a) => String(a.id) === id);
  return { title: item ? assetTitle(item) : "المادة غير موجودة" };
}
export default async function AssetPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const item = archive.find((a) => String(a.id) === id);
  if (!item) notFound();
  const src = `/api/media/${item.id}`;
  return (
    <>
      <div className="breadcrumb">
        <Link href="/library">المكتبة</Link>
        <span>/</span>
        <span>{sources[item.id]?.title || assetTitle(item)}</span>
      </div>
      <PageHeading
        eyebrow={`${kindNames[item.kind]} • ${fileSize(item.size)}`}
        title={sources[item.id]?.title || assetTitle(item)}
        description="نسخة محفوظة في مكتبة الموسوعة. تُستكمل بيانات الكتاب والمؤلف والطبعة والصفحة بمقابلة الأصل."
      />
      <div className="asset-viewer">
        {item.kind === "image" ? (
          <a href={src} target="_blank" rel="noreferrer">
            <img
              src={src}
              alt={
                sources[item.id]?.title || `الصورة الأصلية للمرجع ${item.id}`
              }
            />
          </a>
        ) : item.kind === "video" ? (
          <video controls preload="metadata" playsInline src={src}>
            <track kind="captions" />
            متصفحك لا يدعم تشغيل الفيديو. استخدم رابط الملف الأصلي أدناه.
          </video>
        ) : item.kind === "audio" ? (
          <audio controls preload="metadata" src={src} />
        ) : item.kind === "pdf" ? (
          <iframe title={`ملف PDF للمرجع ${id}`} src={src} />
        ) : (
          <p>هذا النوع متاح للتنزيل وفتحه ببرنامجه المناسب.</p>
        )}
      </div>
      <div className="related-actions">
        <a className="button button-dark" href={`${src}?download=1`}>
          <Download size={17} /> تنزيل الملف الأصلي
        </a>
        <Link className="button button-outline" href={`/sources/${item.id}`}>
          بيانات المرجع وصفحاته المرتبطة ←
        </Link>
      </div>
      {sources[item.id] && (
        <p className="source-metadata">{sources[item.id].detail}</p>
      )}
      <EvidenceReading id={item.id} />
      <StatusNote>
        {item.kind === "video" || item.kind === "audio"
          ? "الملف متاح للاستماع والمشاهدة. لم يُنشأ تفريغ نصي أو تقسيم علمي إلى حجج وتوقيتات بعد."
          : "هذه المادة مؤرشفة. بيانات المرجع والتفريغ الكامل والمراجعة العلمية تحتاج إلى استكمال."}
      </StatusNote>
    </>
  );
}
