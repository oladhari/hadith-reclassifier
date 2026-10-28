import Link from "next/link";
import { ArrowUpLeft } from "lucide-react";
import AssetThumbnail from "./asset-thumbnail";
import thumbnails from "@/content/thumbnails.json";
import { kindNames, fileSize, type ArchiveItem } from "@/lib/archive";
import { scopeNames, type MediaDescription, type MediaChapter, timeLabel } from "@/lib/media-catalogue";
import { topics } from "@/lib/topics";

export function LibraryCard({ item, metadata, chapter }: { item: ArchiveItem; metadata: MediaDescription; chapter?: MediaChapter }) {
  const href = chapter ? `/library/${item.id}?start=${chapter.start}&end=${chapter.end}#media-player` : `/library/${item.id}`;
  return <Link className="asset-card" href={href}>
    <AssetThumbnail src={(thumbnails as Record<string, string>)[item.id]} kind={item.kind} label={kindNames[item.kind]} />
    <div className="asset-info">
      <span className="eyebrow">{chapter ? "مقطع موضوعي" : scopeNames[metadata.scope] || kindNames[item.kind]} • {chapter ? timeLabel(chapter.end - chapter.start) : fileSize(item.size)}
        {!chapter && metadata.page_count ? ` • ${metadata.page_count} صفحة` : ""}
        {!chapter && metadata.duration ? ` • ${timeLabel(metadata.duration)}` : ""}
      </span>
      <h3>{chapter?.title || metadata.title}</h3>
      <p className="asset-description">{chapter?.summary || metadata.description}</p>
      {chapter && <p className="asset-parent-title">من: {metadata.title}</p>}
      {metadata.topics.length > 0 && <p className="asset-topic-labels">{metadata.topics.map(slug => topics.find(t => t.slug === slug)?.title).filter(Boolean).join(" · ")}</p>}
      <div><span>{new Date(item.date).toLocaleDateString("ar-u-nu-latn", { timeZone: "Asia/Tokyo" })}</span><ArrowUpLeft size={16} /></div>
    </div>
  </Link>;
}
