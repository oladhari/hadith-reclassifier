import data from "@/content/corpus-progress.json";
export type CorpusState = "unreviewed" | "in_progress" | "needs_review" | "accepted" | "rejected";
export const stateNames: Record<CorpusState, string> = {
  unreviewed: "لم يُفحص بعد", in_progress: "قيد الفحص", needs_review: "بانتظار المراجعة البشرية",
  accepted: "مقبول بعد المراجعة", rejected: "مستبعد بعد المراجعة",
};
export type CorpusProgress = { status: CorpusState; filtered: boolean; in_book: boolean;
  checks?: Record<string, number>; review?: { verdict: string; reasoning: string; reviewed_at: string };
  book_entries?: { edition: string; number: number | null }[];
};
export const corpusProgress = { ...data, records: data.records as Record<string, CorpusProgress> };
export function recordProgress(collection: string, number: string | number): CorpusProgress {
  return (data.records as Record<string, CorpusProgress>)[`${collection}:${number}`] || { status: "unreviewed", filtered: false, in_book: false };
}
export function matchesState(record: CorpusProgress, status: string) {
  return !status || (status === "filtered" ? record.filtered : status === "book" ? record.in_book : record.status === status);
}
