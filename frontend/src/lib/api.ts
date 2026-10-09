const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type Collection = "bukhari" | "muslim" | "malik" | "ahmed" | "abudawud" | "tirmidhi" | "nasai" | "ibnmajah";
export type Verdict = "accepted" | "rejected" | "under_review";

export interface Hadith {
  id: number;
  collection: Collection;
  book_number: number | null;
  hadith_number: number | null;
  urn: string | null;
  text_arabic: string | null;
  text_english: string;
  narrator_chain_raw: string | null;
  traditional_grade: string | null;
  is_processed: boolean;
  created_at: string;
}

export interface NarratorIssue {
  narrator: string;
  issue: string;
}

export interface QuranReference {
  surah: number;
  ayah: number;
  text: string;
}

export interface Classification {
  id: number;
  hadith_id: number;
  verdict: Verdict;
  rejection_reasons: string[] | null;
  quran_references: QuranReference[] | null;
  ai_reasoning: string | null;
  chain_analysis: string | null;
  narrator_issues: NarratorIssue[] | null;
  chain_score: number | null;
  content_score: number | null;
  overall_score: number | null;
  sahih_othmani_number: number | null;
  reviewed_by_human: boolean;
  created_at: string;
}

export interface HadithWithClassification {
  hadith: Hadith;
  classification: Classification | null;
}

export interface HadithListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Hadith[];
}

export interface Stats {
  total_classified: number;
  accepted: number;
  rejected: number;
  sahih_othmani_count: number;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  listHadiths: (params: Record<string, string | number | boolean | undefined>) => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") q.set(k, String(v));
    }
    return apiFetch<HadithListResponse>(`/hadiths?${q}`);
  },

  getHadith: (id: number) => apiFetch<HadithWithClassification>(`/hadiths/${id}`),

  classify: (hadithId: number) =>
    apiFetch<Classification>("/classifications/classify", {
      method: "POST",
      body: JSON.stringify({ hadith_id: hadithId }),
    }),

  bulkClassify: (collection?: string, limit = 10) =>
    apiFetch("/classifications/bulk-classify", {
      method: "POST",
      body: JSON.stringify({ collection, limit }),
    }),

  getStats: () => apiFetch<Stats>("/classifications/stats"),

  getSahihOthmani: (page = 1, pageSize = 20) =>
    apiFetch<Classification[]>(`/classifications/sahih-othmani?page=${page}&page_size=${pageSize}`),

  ingest: (collection: Collection, limit = 50) =>
    apiFetch("/ingest/", {
      method: "POST",
      body: JSON.stringify({ collection, limit }),
    }),
};
