import Link from "next/link";
import AssetThumbnail from "./asset-thumbnail";
import thumbnails from "@/content/thumbnails.json";
import type { ExcerptAlbum } from "@/lib/library-organization";
import type { MediaCatalogue } from "@/lib/media-catalogue";
import { ar } from "@/lib/research";
export function ExcerptAlbumCard({ album, catalogue }: { album: ExcerptAlbum; catalogue: MediaCatalogue }) {
  const previews = album.items.flatMap(item => catalogue[String(item.id)].collection_images || [{ id: item.id, label: catalogue[String(item.id)].title }]).slice(0, 3);
  return <Link className="asset-card" href={`/library/albums/${album.key}`} data-excerpt-album={album.key}>
    <div className="image-collection-cover" style={{ gridTemplateColumns: `repeat(${previews.length}, minmax(0, 1fr))` }}>
      {previews.map(image => <AssetThumbnail key={image.id} src={(thumbnails as Record<string, string>)[image.id]} kind="image" label={image.label} />)}
      <span className="image-count-badge">{ar(album.items.length)} مواد</span>
    </div>
    <div className="asset-info"><span className="eyebrow">ألبوم مقتطفات وشواهد</span><h3>{album.work}</h3><p className="asset-description">{album.theme}</p>
      <p>صور وصفحات وملفات مرتبطة بالكتاب والموضوع، مع مراجع كل مادة.</p><span>تصفّح الألبوم ←</span>
    </div>
  </Link>;
}
