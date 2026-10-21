import seed from "@/content/editorial-seed.json";
export type ResearchCase = {
  slug: string;
  title: string;
  subtitle: string;
  category: string;
  label: string;
  number: string;
  intro: string;
  question: string;
  steps: string[];
  posts: number[];
  terms: string[];
  evidence: number[];
  note: string;
};
export const cases: ResearchCase[] = seed.cases;
export const layers = seed.layers;
export const sources: Record<
  number,
  { title: string; detail: string; quote: string }
> = seed.sources;
export const collections: Record<string, string> = seed.collections;
export const normalize = (s: string) =>
  s
    .normalize("NFKC")
    .replace(/[\u064B-\u065F\u0670\u0640]/g, "")
    .replace(/[أإآٱ]/g, "ا")
    .replace(/ى/g, "ي")
    .toLowerCase()
    .trim();
export const matches = (text: string, q: string) =>
  normalize(q)
    .split(/\s+/)
    .filter(Boolean)
    .every((word) => normalize(text).includes(word));
export function ar(n: number) {
  return new Intl.NumberFormat("ar-u-nu-latn").format(n);
}
