import data from "@/content/public-evidence.json";
import { topics } from "./topics";
export const evidenceLabels = data.labels as Record<string, string>;
export function caseEvidence(slug: string): number[] { return (data.cases as Record<string, number[]>)[slug] || []; }
export function publicEvidence(path: string): number[] {
 const slug = path.split("/").pop() || "";
 return path.startsWith("/topics/") ? [...new Set((topics.find(t => t.slug === slug)?.cases || []).flatMap(caseEvidence))] : caseEvidence(slug);
}
