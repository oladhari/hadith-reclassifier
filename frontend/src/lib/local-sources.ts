import "server-only";
import data from "@/content/local-sources.json";
import { archive, assetTitle, type ArchiveItem } from "./archive";
import { evidenceLabels } from "./public-evidence";
import { sources } from "./research";
export type LocalSource = {
  id: number;
  date: string;
  files: number[];
  quotes: string[];
};
const records = data as Record<string, LocalSource>;
export function sourceRecord(id: number) {
  return records[String(id)];
}
export function sourceFiles(id: number): ArchiveItem[] {
  return (sourceRecord(id)?.files || [])
    .map((fileId) => archive.find((file) => file.id === fileId))
    .filter((file): file is ArchiveItem => Boolean(file));
}
export function sourceTitle(id: number) {
  const known = sources[id];
  if (known) return known.title;
  if (evidenceLabels[id]) return evidenceLabels[id];
  const files = sourceFiles(id);
  return files[0]
    ? assetTitle(files[0])
    : "نصوص ومناقشات";
}
export function resolveSources(ids: number[]) {
  const seen = new Set<string>();
  return ids.filter((id) => {
    const record = sourceRecord(id);
    if (!record) return false;
    const key = record.files.length
      ? `files:${[...record.files].sort((a, b) => a - b).join(",")}`
      : `text:${id}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
