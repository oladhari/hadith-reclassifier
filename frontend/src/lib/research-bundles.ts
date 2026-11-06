import "server-only";
import data from "@/content/research-bundles.json";
import { getMediaCatalogue } from "./media-catalogue";
export type ResearchBundle = { slug: string; title: string; topic: string; cases: string[]; explanation: string; items: number[] };
export async function getResearchBundles(): Promise<ResearchBundle[]> {
  const catalogue = await getMediaCatalogue();
  return data.bundles.map(bundle => ({ ...bundle, items: bundle.items.filter(id => catalogue[String(id)]?.visible && catalogue[String(id)].canonical_id === id) })).filter(bundle => bundle.items.length > 0);
}
