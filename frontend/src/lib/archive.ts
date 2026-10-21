import "server-only";
import evidence from "@/content/public-evidence.json";
import data from "@/content/archive-index.json";
export type ArchiveItem = (typeof data)[number];
export const archive = data;
export const kindNames: Record<string, string> = {
  image: "صورة",
  video: "فيديو",
  pdf: "كتاب / PDF",
  audio: "صوت",
  document: "وثيقة",
};
export function assetTitle(item: ArchiveItem) {
  return (
    (evidence.labels as Record<string, string>)[item.id] ||
    item.name?.replace(/\.[^.]+$/, "").replace(/_/g, " ") ||
    `${kindNames[item.kind]} من مكتبة الموسوعة`
  );
}
export function fileSize(bytes: number) {
  return bytes >= 1024 ** 3
    ? `${(bytes / 1024 ** 3).toFixed(2)} GB`
    : `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}
