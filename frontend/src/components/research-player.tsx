"use client";
import { useRef } from "react";

export function ResearchPlayer({ id, kind, poster, start = 0, end }: {
  id: number; kind: "video" | "audio"; poster?: string; start?: number; end?: number;
}) {
  const player = useRef<HTMLVideoElement & HTMLAudioElement>(null);
  const jumpToStart = () => { if (player.current && start > 0) player.current.currentTime = start; };
  const stopAtEnd = () => {
    if (player.current && end !== undefined && player.current.currentTime >= end) player.current.pause();
  };
  const captions = <track kind="captions" src={`/transcripts/${id}.vtt`} srcLang="ar" label="العربية — تفريغ آلي" />;
  const src = `/api/media/${id}${start > 0 ? `#t=${start}${end !== undefined ? `,${end}` : ""}` : ""}`;
  return kind === "video" ?
    <video key={`${id}-${start}-${end}`} ref={player} controls playsInline preload="none" src={src} poster={poster}
      onLoadedMetadata={jumpToStart} onTimeUpdate={stopAtEnd}>{captions}</video> :
    <audio key={`${id}-${start}-${end}`} ref={player} controls preload="none" src={src}
      onLoadedMetadata={jumpToStart} onTimeUpdate={stopAtEnd}>{captions}</audio>;
}
