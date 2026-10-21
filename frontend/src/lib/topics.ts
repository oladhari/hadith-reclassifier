import seed from "@/content/editorial-seed.json";
import report from "@/content/archive-themes.json";
export const archiveAnalysis = report;
export type MatchSet = {
  postCount: number;
  distinctTextCount: number;
  posts: { id: number; matchedTerms: string[]; normalizedTextHash: string }[];
};
export function caseMatches(slug: string): MatchSet {
  return (
    (report.cases as Record<string, MatchSet>)[slug] || {
      postCount: 0,
      distinctTextCount: 0,
      posts: [],
    }
  );
}
const definitions = seed.topics;
export const topics = definitions.map((def) => {
  const found = report.topics.find((topic) => topic.slug === def.slug);
  if (!found) throw new Error(`Missing archive topic: ${def.slug}`);
  return { ...found, ...def };
});
