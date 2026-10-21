/* eslint-disable @next/next/no-img-element -- Original archival images are served without alteration. */
import Link from "next/link";
import {
  Image as ImageIcon,
  Play,
  FileText,
  ArrowUpLeft,
  Headphones,
} from "lucide-react";
import { archive, assetTitle, kindNames, fileSize } from "@/lib/archive";
import { ar, sources, matches } from "@/lib/research";
import { PageHeading } from "@/components/research-ui";
export const metadata = { title: "مكتبة المصادر" };
export default async function LibraryPage({
  searchParams,
}: {
  searchParams: Promise<{ kind?: string; page?: string; q?: string }>;
}) {
  const { kind = "", page = "1", q = "" } = await searchParams;
  const filtered = archive.filter(
    (a) =>
      (!kind || a.kind === kind) &&
      (!q ||
        String(a.id) === q.trim() ||
        matches(`${assetTitle(a)} ${sources[a.id]?.title || ""}`, q)),
  );
  const pages = Math.max(1, Math.ceil(filtered.length / 24));
  const current = Math.min(pages, Math.max(1, Number.parseInt(page) || 1));
  const items = filtered.slice((current - 1) * 24, current * 24);
  const url = (p: number) =>
    `/library?${new URLSearchParams({ kind, q, page: String(p) })}`;
  return (
    <>
      <PageHeading
        eyebrow="الأصول المحفوظة"
        title="المكتبة المصوّرة والمرئيات"
        description="صور صفحات الكتب والوثائق والمرئيات؛ افتح المادة واقرأ الدليل بنفسك داخل الموسوعة."
      />
      <div className="type-tabs">
        <Link href="/library" className={!kind ? "selected" : ""}>
          الكل <span>{ar(archive.length)}</span>
        </Link>
        {Object.entries(kindNames).map(([k, v]) => (
          <Link
            className={kind === k ? "selected" : ""}
            key={k}
            href={`/library?kind=${k}`}
          >
            {v}
            <span>{ar(archive.filter((a) => a.kind === k).length)}</span>
          </Link>
        ))}
      </div>
      <form action="/library" className="filter-bar">
        <input type="hidden" name="kind" value={kind} />
        <label>
          ابحث في المكتبة
          <input
            name="q"
            maxLength={160}
            defaultValue={q}
            placeholder="اسم كتاب أو مادة تبحث عنها"
          />
        </label>
        <button className="button button-dark">ابحث في المكتبة</button>
      </form>
      <div className="library-grid">
        {items.map((item) => (
          <Link
            className="asset-card"
            key={item.id}
            href={`/library/${item.id}`}
          >
            <div className={`asset-cover ${item.kind}`}>
              {sources[item.id] ? (
                <>
                  <img
                    src={`/evidence/${item.id}.jpg`}
                    alt={sources[item.id].title}
                    loading="lazy"
                  />
                </>
              ) : (
                <>
                  {item.kind === "video" ? (
                    <Play size={34} />
                  ) : item.kind === "image" ? (
                    <ImageIcon size={34} />
                  ) : item.kind === "audio" ? (
                    <Headphones size={34} />
                  ) : (
                    <FileText size={34} />
                  )}
                  <span>{kindNames[item.kind]}</span>
                </>
              )}
            </div>
            <div className="asset-info">
              <span className="eyebrow">
                {kindNames[item.kind]} • {fileSize(item.size)}
              </span>
              <h3>{sources[item.id]?.title || assetTitle(item)}</h3>
              <div>
                <span>
                  {new Date(item.date).toLocaleDateString("ar-u-nu-latn", {
                    timeZone: "Asia/Tokyo",
                  })}
                </span>
                <ArrowUpLeft size={16} />
              </div>
            </div>
          </Link>
        ))}
      </div>
      {!items.length && (
        <p className="empty-state">
          لا يوجد مرفق مطابق. تحقق من معرّف المادة أو غيّر نوع الملف.
        </p>
      )}
      <nav className="pagination" aria-label="صفحات المكتبة">
        {current > 1 && <Link href={url(current - 1)}>→ السابق</Link>}
        <span>
          صفحة {ar(current)} من {ar(pages)} • {ar(filtered.length)} مرفقات
        </span>
        {current < pages && <Link href={url(current + 1)}>التالي ←</Link>}
      </nav>
    </>
  );
}
