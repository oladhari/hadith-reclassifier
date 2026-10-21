import "server-only";
import { unstable_cache } from "next/cache";
import { cache } from "react";
import { queryNeon, usesNeon } from "./neon";
import evidence from "@/content/public-evidence.json";
import data from "@/content/archive-index.json";
export type ArchiveItem = (typeof data)[number] & { object_key?: string; storage_state?: string };
const liveArchive = unstable_cache(async () => {
  const rows = await queryNeon<ArchiveItem>("SELECT * FROM research.website_media ORDER BY id");
  return rows.map(row=>({...row,size:Number(row.size)}));
}, ["neon-media-v1"], { revalidate: 60 });
export const getArchive = cache(async (): Promise<ArchiveItem[]> => usesNeon() ? liveArchive() : data);
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
