import { getBibliography } from "@/lib/local-sources";
/* eslint-disable @next/next/no-img-element -- Preserve original scans and pre-sized document previews. */
import Link from "next/link";
import { notFound, permanentRedirect } from "next/navigation";
import { EvidenceReading } from "@/components/evidence-reading";
import { ResearchPlayer } from "@/components/research-player";
import { ImageCollection } from "@/components/image-collection";
import { Download } from "lucide-react";
import thumbnails from "@/content/thumbnails.json";
import { getArchive, kindNames, fileSize } from "@/lib/archive";
import { getMediaCatalogue, getTranscript, scopeNames, timeLabel } from "@/lib/media-catalogue";
import { topics } from "@/lib/topics";
import { cases } from "@/lib/research";
import { PageHeading } from "@/components/research-ui";
export const dynamic = "force-dynamic";
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const catalogue = await getMediaCatalogue();
  return { title: catalogue[id]?.visible ? catalogue[id].title : "المادة غير موجودة" };
}
export default async function AssetPage({ params, searchParams }: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ start?: string; end?: string }>;
}) {
  const [{ id }, query, archive, catalogue, sources] = await Promise.all([
    params, searchParams, getArchive(), getMediaCatalogue(), getBibliography(),
  ]);
  const entry = catalogue[id];
  if (!entry?.visible) notFound();
  if (entry.canonical_id !== Number(id)) permanentRedirect(`/library/${entry.canonical_id}`);
  const item = archive.find(row => row.id === Number(id));
  if (!item) notFound();
  const src = entry.asset_url || `/api/media/${item.id}`;
  const startValue = Number(query.start);
  const endValue = Number(query.end);
  const start = Number.isFinite(startValue) && startValue >= 0 && startValue < (entry.duration || 0) ? startValue : 0;
  const end = Number.isFinite(endValue) && endValue > start && endValue <= (entry.duration || 0) ? endValue : undefined;
  const chapter = entry.chapters.find(row => Math.abs(row.start - start) < .1 && end === row.end);
  const speech = item.kind === "video" || item.kind === "audio";
  const transcript = entry.has_transcript ? await getTranscript(item.id) : "";
  return <>
    <div className="breadcrumb"><Link href="/library">المكتبة</Link><span>/</span><span>{entry.title}</span></div>
    <PageHeading eyebrow={`${entry.collection_images ? "مجموعة صور" : scopeNames[entry.scope] || kindNames[item.kind]} • ${fileSize(entry.asset_size || item.size)}${entry.page_count ? ` • ${entry.page_count} صفحة` : ""}${entry.image_count === 2 ? " • صورتان" : ""}`}
      title={entry.title} description={entry.description} />
    {(entry.work_title || entry.author || entry.page_label) && <dl className="media-bibliography">
      {entry.work_title && <div><dt>المصدر</dt><dd><Link href={`/library?q=${encodeURIComponent(entry.work_title)}`}>{entry.work_title} ←</Link></dd></div>}
      {entry.author && <div><dt>المؤلف</dt><dd>{entry.author}</dd></div>}
      {entry.page_label && <div><dt>الموضع</dt><dd>{entry.page_label}</dd></div>}
    </dl>}
    {chapter && <div className="chapter-heading"><h2>{chapter.title}</h2><p>{chapter.summary}</p><Link href={`/library/${id}#media-player`}>عرض التسجيل الكامل ←</Link></div>}
    <div className={`asset-viewer${item.kind === "document" ? " document-viewer" : ""}${entry.collection_images ? " grouped-image-viewer" : ""}`} id="media-player">
      {entry.collection_images ? <ImageCollection images={entry.collection_images} /> : item.kind === "image" ? <a href={src} target="_blank" rel="noreferrer"><img src={src} alt={entry.title} /></a>
        : speech ? <ResearchPlayer id={item.id} kind={item.kind as "video" | "audio"} poster={(thumbnails as Record<string, string>)[id]} start={start} end={end} />
        : item.kind === "pdf" ? <iframe title={entry.title} src={src} />
        : <><img className="document-first-page" src={(thumbnails as Record<string, string>)[id]} alt={`الصفحة الأولى: ${entry.title}`} /><p>يمكن تنزيل الوثيقة الأصلية وفتحها ببرنامجها المناسب.</p></>}
    </div>
    <div className="related-actions">
      {!entry.collection_images && <a className="button button-dark" href={entry.asset_url ? src : `${src}?download=1`} download={entry.asset_url ? `${entry.title.replace(/[\\/:*?"<>|]/g, "-")}.pdf` : undefined}><Download size={17} /> {entry.asset_url ? "تنزيل الملف المجمّع" : "تنزيل الملف الأصلي"}</a>}
      <Link className="button button-outline" href={`/sources/${item.id}`}>بيانات المرجع وصفحاته المرتبطة ←</Link>
      {speech && transcript && <a className="text-link" href={`/transcripts/${id}.vtt`} download>تنزيل الترجمة العربية (VTT)</a>}
    </div>
    {entry.collection_sources && <details className="transcript-panel collection-provenance"><summary>{entry.collection_images ? "الأصول ومعلومات الصور" : "الأصول وترتيب الصفحات"}</summary>
      <p>{entry.collection_images ? "جُمعت الصور للقراءة في موضوع واحد دون قصّها أو تغيير محتواها. تظهر بيانات كل صورة وموضعها منفصلة، وتظل النصوص منسوبة إلى أصحابها." : "جُمعت الصفحات كما وردت في أصولها، وحُذفت الأغلفة المتكررة فقط. هذه مجموعة مصادر وليست كتابًا محقّقًا جديدًا."}</p>
      <ol>{entry.collection_sources.map((source, index) => <li key={source.id}><a href={`/api/media/${source.id}`} target="_blank" rel="noreferrer">{entry.collection_images ? `فتح الصورة الأصلية ${index + 1}` : `فتح الملف الأصلي ${index + 1} (${source.page_count} صفحات)`} ←</a></li>)}</ol>
      {!entry.collection_images && <table><thead><tr><th>صفحة المجموعة</th><th>الملف الأصلي</th><th>صفحته</th></tr></thead><tbody>{entry.collection_page_map?.map(row => <tr key={row.page}><td>{row.page}</td><td>{entry.collection_sources!.findIndex(source => source.id === row.source_id) + 1}</td><td>{row.source_page}</td></tr>)}</tbody></table>}
    </details>}
    {entry.chapters.length > 0 && <section className="article-section"><h2>الموضوعات داخل التسجيل</h2><div className="media-chapters">
      {entry.chapters.map((row, index) => <Link key={index} href={`/library/${id}?start=${row.start}&end=${row.end}#media-player`}>
        <span dir="ltr">{timeLabel(row.start)} – {timeLabel(row.end)}</span><strong>{row.title}</strong><p>{row.summary}</p>
      </Link>)}
    </div></section>}
    {transcript && <details className="transcript-panel"><summary>اقرأ التفريغ العربي للتسجيل</summary>
      <p className="muted">تفريغ آلي مع تصحيح أولي لبعض الأسماء؛ يُراجع الصوت عند الاقتباس، وقد تبقى أخطاء في الأسماء والألفاظ.</p>
      <div className="transcript-text">{transcript.split("\n").filter(Boolean).map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div>
    </details>}
    {(entry.topics.length > 0 || entry.cases.length > 0) && <section className="article-section"><h2>محاور وملفات مرتبطة</h2><div className="reference-uses">
      {entry.topics.map(slug => { const topic = topics.find(row => row.slug === slug); return topic ? <Link key={slug} href={`/topics/${slug}`}>{topic.title} ←</Link> : null; })}
      {entry.cases.map(slug => { const item = cases.find(row => row.slug === slug); return item ? <Link key={slug} href={`/cases/${slug}`}>{item.title} ←</Link> : null; })}
    </div></section>}
    {entry.tags.length > 0 && <div className="media-tags">{entry.tags.map(tag => <Link href={`/library?q=${encodeURIComponent(tag)}`} key={tag}>{tag}</Link>)}</div>}
    {sources[item.id] && <p className="source-metadata">{sources[item.id].detail}</p>}
    <EvidenceReading id={item.id} />
  </>;
}
