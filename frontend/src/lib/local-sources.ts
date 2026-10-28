import "server-only";
import { unstable_cache } from "next/cache";
import { cache } from "react";
import { queryNeon, usesNeon } from "./neon";
import data from "@/content/local-sources.json";
import { getArchive, assetTitle, type ArchiveItem } from "./archive";
import { evidenceLabels } from "./public-evidence";
import { sources } from "./research";
import { getMediaCatalogue } from "./media-catalogue";
import objectKeys from "@/content/media-objects.json";
const liveBibliography = unstable_cache(async () => {
  const rows = await queryNeon<{id:number;title:string;detail:string;quote:string}>("SELECT * FROM research.website_bibliography");
  return Object.fromEntries(rows.map(({id,...source})=>[id,source]));
}, ["neon-bibliography-v1"], { revalidate:60 });
export const getBibliography = cache(async (): Promise<typeof sources> => usesNeon() ? liveBibliography() : sources);
export type LocalSource = {
  id: number;
  date: string;
  files: number[];
  quotes: string[];
};
const liveSources = unstable_cache(async () => {
  const rows = await queryNeon<LocalSource>("SELECT * FROM research.website_sources ORDER BY id");
  return Object.fromEntries(rows.map(row=>[String(row.id),row]));
}, ["neon-sources-v1"], { revalidate: 60 });
const getSources = cache(async (): Promise<Record<string, LocalSource>> => usesNeon() ? liveSources() : data as Record<string, LocalSource>);
export async function sourceRecord(id: number) {
  return (await getSources())[String(id)];
}
export async function sourceFiles(id: number): Promise<ArchiveItem[]> {
  const archive = await getArchive();
  const catalogue = await getMediaCatalogue();
  const seen = new Set<string>();
  return ((await sourceRecord(id))?.files || [])
    .map((fileId) => archive.find((file) => file.id === fileId))
    .filter((file): file is ArchiveItem => Boolean(file))
    .filter(file => {
      const metadata = catalogue[String(file.id)];
      if (metadata?.manual_video_hidden) return false;
      const key = metadata?.asset_url || metadata?.collection_images ? `collection:${metadata.canonical_id}` : file.object_key || (objectKeys as Record<string, string>)[file.id] || String(file.id);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}
export async function sourceTitle(id: number) {
  const metadata = (await getMediaCatalogue())[String(id)];
  if (metadata?.visible) return metadata.title;
  const known = (await getBibliography())[id];
  if (known) return known.title;
  if (evidenceLabels[id]) return evidenceLabels[id];
  const files = await sourceFiles(id);
  return files[0]
    ? assetTitle(files[0])
    : "نصوص ومناقشات";
}
export async function resolveSources(ids: number[]) {
  const records = await getSources();
  const catalogue = await getMediaCatalogue();
  const seen = new Set<string>();
  return ids.filter((id) => {
    const record = records[String(id)];
    if (!record) return false;
    const key = record.files.length
      ? `files:${[...new Set(record.files.map(file => catalogue[String(file)]?.asset_url || catalogue[String(file)]?.collection_images ? `collection:${catalogue[String(file)].canonical_id}` : (objectKeys as Record<string, string>)[file] || String(file)))].sort().join(",")}`
      : `text:${id}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
