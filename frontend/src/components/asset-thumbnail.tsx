"use client";

/* eslint-disable @next/next/no-img-element -- Pre-sized static WebP previews. */
import { useState } from "react";
import { Image as ImageIcon, Play, FileText, Headphones } from "lucide-react";

export default function AssetThumbnail({ src, kind, label }: {
  src?: string; kind: string; label: string;
}) {
  const [failed, setFailed] = useState(false);
  const visible = src && !failed;
  return (
    <div className={`asset-cover ${kind}`}>
      {visible ? (
        <img src={src} alt="" loading="lazy" decoding="async" width={640} height={640}
          onError={() => setFailed(true)} />
      ) : (
        <>
          {kind === "video" ? <Play size={34} /> : kind === "image" ? <ImageIcon size={34} />
            : kind === "audio" ? <Headphones size={34} /> : <FileText size={34} />}
          <span>{label}</span>
        </>
      )}
      {visible && kind === "video" && (
        <span className="thumbnail-play" aria-hidden="true"><Play size={25} fill="currentColor" /></span>
      )}
      {visible && (kind === "pdf" || kind === "document") && (
        <span className="thumbnail-page">الصفحة الأولى</span>
      )}
    </div>
  );
}
