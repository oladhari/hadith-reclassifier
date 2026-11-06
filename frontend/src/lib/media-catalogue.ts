import "server-only";
import { cache } from "react";
import { organizeEntry } from "./library-organization";
import documentPdfs from "@/content/document-pdfs.json";
import videoVisibility from "@/content/video-visibility.json";
import snapshot from "@/content/media-catalogue.json";
import documentSnapshot from "@/content/document-texts.json";
import transcriptSnapshot from "@/content/transcript-content.json";
import { matches, normalize } from "./research";
import type { ArchiveItem } from "./archive";

export type MediaChapter = { title: string; start: number; end: number; topic: string; summary: string };
export type CollectionImage = { id: number; label: string; description: string };
export type MediaDescription = {
  id: number; canonical_id: number; title: string; description: string;
  work_title: string; author: string; page_label: string; scope: string;
  topics: string[]; cases: string[]; tags: string[]; visible: boolean;
  page_count?: number; duration?: number; has_transcript?: boolean;
  asset_url?: string; asset_size?: number; converted_document?: boolean; manual_video_hidden?: boolean;
  source_platform?: string;
  source_posts?: { url: string; caption: string }[];
  source_url?: string; source_caption?: string; source_account?: string;
  author_role?: string; author_source?: { page: number; quote: string };
  library_section?: string; content_label?: string; attribution?: string; organization_note?: string;
  image_count?: number; collection_images?: CollectionImage[];
  collection_sources?: { id: number; page_count: number }[];
  collection_page_map?: { page: number; source_id: number; source_page: number }[];
  preferred_media_id?: number; has_document_text?: boolean; bundles?: string[];
  explanations?: { text: string; attribution: string; kind: string }[];
  chapters: MediaChapter[]; occurrences: number[];
};
export type MediaCatalogue = Record<string, MediaDescription>;
export const getMediaCatalogue = cache(async (): Promise<MediaCatalogue> =>
  Object.fromEntries(Object.entries(snapshot as MediaCatalogue).map(([id, entry]) => {
    if (videoVisibility.hidden.includes(entry.canonical_id)) entry = { ...entry, visible: false, manual_video_hidden: true };
    const pdf = (documentPdfs as Record<string, { asset_url: string; asset_size: number; page_count: number }>)[String(entry.canonical_id)];
    return [id, organizeEntry(pdf ? { ...entry, ...pdf, converted_document: true } : entry)];
  })),
);
export const scopeNames: Record<string, string> = {
  page: "صفحة مصوّرة", excerpt: "مقتطف / صفحات مجمّعة", full_book: "كتاب / مجلد كامل",
  article: "بحث / مقال كامل", lecture: "محاضرة", clip: "مقطع مرئي", audio: "تسجيل صوتي",
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
      metadata.page_label, ...metadata.tags, ...(metadata.explanations || []).map(row => row.text),
      ...(metadata.collection_images || []).flatMap(image => [image.label, image.description])].join(" "), query);
}
// Normalize published search text lazily once per server instance, without network reads.
let textIndexes:{speech:{id:number;text:string}[];documents:{id:number;text:string}[]}|undefined;
function publicTextIndexes(){
 return textIndexes ||= {
  speech:Object.entries(transcriptSnapshot).map(([id,text])=>({id:Number(id),text:normalize(text)})),
  documents:Object.entries(documentSnapshot).map(([id,row])=>({id:Number(id),text:normalize(row.text)})),
 };
}
export async function searchLibrary(archive: ArchiveItem[], catalogue: MediaCatalogue, query: string) {
  const library = publicLibrary(archive, catalogue);
  if (!query.trim()) return library;
  // A known catalogue number resolves its canonical work before matching dates
  // and other incidental numbers in captions from a much larger collection.
  const numbered = /^\d+$/.test(query.trim()) ? catalogue[query.trim()] : undefined;
  if (numbered?.visible && library.some(item => item.id === numbered.canonical_id))
    return library.filter(item => item.id === numbered.canonical_id);
  const words = normalize(query).split(/\s+/).filter(Boolean);
  const indexes=publicTextIndexes();
  const transcriptIds=new Set(indexes.speech.filter(row=>words.every(word=>row.text.includes(word))).map(row=>row.id));
  const documentIds=new Set(indexes.documents.filter(row=>words.every(word=>row.text.includes(word))).map(row=>row.id));
  return library.filter(item => mediaMatches(item, catalogue[String(item.id)], query) || transcriptIds.has(item.id) || documentIds.has(item.id));
}
export const getTranscript = cache(async (id: number): Promise<string> => (transcriptSnapshot as Record<string,string>)[String(id)] || "");
export function timeLabel(seconds: number) {
  const whole = Math.max(0, Math.floor(seconds));
  return whole >= 3600
    ? `${Math.floor(whole / 3600)}:${String(Math.floor(whole / 60) % 60).padStart(2, "0")}:${String(whole % 60).padStart(2, "0")}`
    : `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

export const getDocumentText = cache(async (id: number): Promise<string> => (documentSnapshot as Record<string,{text:string}>)[String(id)]?.text || "");
