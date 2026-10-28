import "server-only";
import { neon } from "@neondatabase/serverless";
export type VideoReviewItem = {
  id: number; title: string; description: string; duration: number; date: string; size: number;
  decision: "pending" | "keep" | "hide"; platform: "unknown" | "tiktok" | "youtube" | "other";
  note: string; revision: number; updated_at: string | null; visible: boolean;
};
export async function reviewQuery<T>(text: string, values: unknown[] = []): Promise<T[]> {
  const url = process.env.VIDEO_REVIEW_DATABASE_URL;
  if (!url) throw new Error("Video review database is not configured");
  const sql = neon(url, { fetchOptions: { cache: "no-store", signal: AbortSignal.timeout(20000) } });
  return await sql.query(text, values) as T[];
}
export async function reviewItems() {
  const rows = await reviewQuery<VideoReviewItem>("SELECT * FROM research.video_review_items ORDER BY id");
  return rows.map(row => ({ ...row, duration: Number(row.duration), size: Number(row.size) }));
}
