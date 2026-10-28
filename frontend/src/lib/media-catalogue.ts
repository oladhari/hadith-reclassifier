import "server-only";
import { cache } from "react";
import { unstable_cache } from "next/cache";
import snapshot from "@/content/media-catalogue.json";
import transcriptSnapshot from "@/content/transcript-content.json";
import { queryNeon, usesNeon } from "./neon";
import { matches, normalize } from "./research";
import type { ArchiveItem } from "./archive";

export type MediaChapter = { title: string; start: number; end: number; topic: string; summary: string };
export type CollectionImage = { id: number; label: string; description: string };
export type MediaDescription = {
  id: number; canonical_id: number; title: string; description: string;
  work_title: string; author: string; page_label: string; scope: string;
  topics: string[]; cases: string[]; tags: string[]; visible: boolean;
  page_count?: number; duration?: number; has_transcript?: boolean;
  asset_url?: string; asset_size?: number;
  image_count?: number; collection_images?: CollectionImage[];
  collection_sources?: { id: number; page_count: number }[];
  collection_page_map?: { page: number; source_id: number; source_page: number }[];
  chapters: MediaChapter[]; occurrences: number[];
};
export type MediaCatalogue = Record<string, MediaDescription>;
const liveCatalogue = unstable_cache(async () => {
  const rows = await queryNeon<{ id: string; metadata: MediaDescription }>(
    "SELECT id,metadata FROM research.website_catalogue",
  );
  return Object.fromEntries(rows.map(row => [row.id, row.metadata])) as MediaCatalogue;
}, ["neon-catalogue-v3"], { revalidate: 60 });
export const getMediaCatalogue = cache(async (): Promise<MediaCatalogue> =>
  usesNeon() ? liveCatalogue() : snapshot as MediaCatalogue,
);
export const scopeNames: Record<string, string> = {
  page: "صفحة مصوّرة", excerpt: "مقتطف / صفحات مجمّعة", full_book: "كتاب / مجلد كامل",
  article: "بحث / وثيقة", lecture: "محاضرة", clip: "مقطع مرئي", audio: "تسجيل صوتي",
};
export function publicLibrary(archive: ArchiveItem[], catalogue: MediaCatalogue) {
  return archive.filter(item => {
    const metadata = catalogue[String(item.id)];
    return metadata?.visible && metadata.canonical_id === item.id;
  });
}
export function mediaMatches(item: ArchiveItem, metadata: MediaDescription, query: string) {
  return String(item.id) === query.trim() || metadata.occurrences.some(id => String(id) === query.trim()) ||
    matches([metadata.title, metadata.description, metadata.work_title, metadata.author,
      metadata.page_label, ...metadata.tags,
      ...(metadata.collection_images || []).flatMap(image => [image.label, image.description])].join(" "), query);
}
export async function searchLibrary(archive: ArchiveItem[], catalogue: MediaCatalogue, query: string) {
  const library = publicLibrary(archive, catalogue);
  if (!query.trim()) return library;
  let transcriptIds: Set<number>;
  if (usesNeon()) {
    const words = normalize(query).split(/\s+/).filter(Boolean);
    const rows = await queryNeon<{ id: string }>(`SELECT id FROM research.website_transcripts t
      WHERE NOT EXISTS (SELECT 1 FROM unnest($1::text[]) AS w(word)
      WHERE strpos(research.website_normalize(t.text),w.word)=0)`, [words]);
    transcriptIds = new Set(rows.map(row => Number(row.id)));
  } else {
    transcriptIds = new Set(Object.entries(transcriptSnapshot).filter(([, text]) => matches(text as string, query)).map(([id]) => Number(id)));
  }
  return library.filter(item => mediaMatches(item, catalogue[String(item.id)], query) || transcriptIds.has(item.id));
}
export const getTranscript = cache(async (id: number): Promise<string> => {
  if (!usesNeon()) return (transcriptSnapshot as Record<string, string>)[id] || "";
  const rows = await queryNeon<{ text: string }>("SELECT text FROM research.website_transcripts WHERE id=$1", [String(id)]);
  return rows[0]?.text || "";
});
export function timeLabel(seconds: number) {
  const whole = Math.max(0, Math.floor(seconds));
  return whole >= 3600
    ? `${Math.floor(whole / 3600)}:${String(Math.floor(whole / 60) % 60).padStart(2, "0")}:${String(whole % 60).padStart(2, "0")}`
    : `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}
