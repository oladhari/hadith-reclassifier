import "server-only";
import { createHash } from "node:crypto";
import reviews from "@/content/library-organization.json";
import seed from "@/content/editorial-seed.json";
import type { ArchiveItem } from "./archive";
import type { MediaCatalogue, MediaDescription } from "./media-catalogue";
import { normalize } from "./research";

export const sectionNames: Record<string, string> = {
  books: "الكتب والبحوث الكاملة", excerpts: "المقتطفات والشواهد", video: "فيديو", audio: "صوت", all: "الكل",
};
const formNames: Record<string, string> = {
  book: "كتاب كامل", volume: "مجلد كامل من كتاب", research: "بحث / مقال كامل", excerpt: "مقتطف / شواهد", draft: "مسودة غير مكتملة",
};
type Review = { section: string; form: string; title?: string; description?: string; author?: string; attribution?: string; note?: string };
export function organizeEntry(entry: MediaDescription): MediaDescription {
  const review = (reviews as Record<string, Review>)[String(entry.canonical_id)];
  return review ? { ...entry, scope: review.form === "book" || review.form === "volume" ? "full_book" : review.form === "research" ? "article" : "excerpt", library_section: review.section, content_label: formNames[review.form],
    title: review.title || entry.title, description: review.description || entry.description, author: review.author || entry.author,
    attribution: review.attribution, organization_note: review.note } : entry;
}
export function librarySection(item: ArchiveItem, entry: MediaDescription) {
  if (item.kind === "video" || item.kind === "audio") return item.kind;
  return entry.library_section || "excerpts";
}
export function authorLabel(entry: MediaDescription) {
  return entry.author || entry.attribution || "المؤلف غير مذكور في النسخة";
}
export type ExcerptAlbum = { key: string; work: string; theme: string; items: ArchiveItem[] };
export function excerptAlbums(items: ArchiveItem[], catalogue: MediaCatalogue): ExcerptAlbum[] {
  const groups = new Map<string, ExcerptAlbum>();
  for (const item of items) {
    const entry = catalogue[String(item.id)];
    if (librarySection(item, entry) !== "excerpts") continue;
    const cases = [...entry.cases].sort();
    const topics = [...entry.topics].sort();
    const themeKey = cases.length ? `cases:${cases.join(",")}` : topics.length ? `topics:${topics.join(",")}` : "";
    // Only a known book AND a shared theme can combine independently catalogued items.
    const identity = entry.work_title.trim() && themeKey
      ? `${normalize(entry.work_title)}|${themeKey}` : `single:${item.id}`;
    const key = createHash("sha256").update(identity).digest("hex").slice(0, 16);
    const labels = cases.length ? cases.map(slug => seed.cases.find(c => c.slug === slug)?.title)
      : topics.map(slug => seed.topics.find(t => t.slug === slug)?.title);
    const group = groups.get(key) || { key, work: entry.work_title, theme: labels.filter(Boolean).join(" · "), items: [] };
    group.items.push(item);
    groups.set(key, group);
  }
  return [...groups.values()];
}
