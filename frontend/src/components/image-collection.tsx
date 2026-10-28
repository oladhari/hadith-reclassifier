/* eslint-disable @next/next/no-img-element -- Readable original source scans. */
import type { CollectionImage } from "@/lib/media-catalogue";
import { EvidenceReading } from "./evidence-reading";

export function ImageCollection({ images }: { images: CollectionImage[] }) {
  return <div className="image-collection-pages">{images.map((image, index) =>
    <figure key={image.id} className="image-collection-page">
      <figcaption><span className="eyebrow">الصورة {index + 1}</span><h3>{image.label}</h3><p>{image.description}</p></figcaption>
      <a href={`/api/media/${image.id}`} target="_blank" rel="noreferrer">
        <img src={`/api/media/${image.id}`} alt={image.label} loading={index === 0 ? "eager" : "lazy"} />
      </a>
      <a className="text-link" href={`/api/media/${image.id}`} target="_blank" rel="noreferrer">فتح الصورة الأصلية بالحجم الكامل ←</a>
      <EvidenceReading id={image.id} />
    </figure>
  )}</div>;
}
