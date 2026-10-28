import "server-only";
import selected from "@/content/public-evidence.json";
import studies from "@/content/filter-case-studies.json";
import seed from "@/content/editorial-seed.json";
import { getMediaCatalogue } from "./media-catalogue";
import { sourceRecord } from "./local-sources";
import { getArchive } from "./archive";

// Explicit editorial references remain usable even when an image is not a
// standalone library listing. This never republishes excluded videos.
export const referencedProofIds = new Set([
  ...Object.values(selected.cases).flat(), ...studies.flatMap(study => study.source_media),
  ...seed.cases.flatMap(item => item.evidence),
]);
export async function proofHref(id: number): Promise<string | null> {
  const catalogue = await getMediaCatalogue();
  const entry = catalogue[String(id)];
  if (entry?.manual_video_hidden) return null;
  if (entry?.visible) return `/library/${entry.canonical_id}`;
  const item = (await getArchive()).find(item => item.id === id);
  if (!item || item.kind === "video" || item.kind === "audio") return null;
  return await sourceRecord(id) ? `/sources/${id}` : null;
}
