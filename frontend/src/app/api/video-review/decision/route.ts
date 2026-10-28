import { revalidateTag } from "next/cache";
import { isVideoReviewer, sameOrigin } from "@/lib/video-review-auth";
import { reviewQuery } from "@/lib/video-review";
export async function POST(request: Request) {
  if (!sameOrigin(request)) return new Response("Forbidden", { status: 403 });
  if (!await isVideoReviewer()) return new Response("Unauthorized", { status: 401 });
  if (Number(request.headers.get("content-length")) > 8192) return new Response("Too large", { status: 413 });
  let input;
  try { input = await request.json(); } catch { return new Response("Invalid JSON", { status: 400 }); }
  const { id, decision, platform, note, revision } = input || {};
  if (!Number.isSafeInteger(id) || !Number.isSafeInteger(revision) || revision < 0 ||
    !["pending", "keep", "hide"].includes(decision) || !["unknown", "tiktok", "youtube", "other"].includes(platform) || typeof note !== "string" || note.length > 1000)
    return new Response("Invalid review", { status: 400 });
  try {
    const rows = await reviewQuery<{ result: { id: number; decision: string; platform: string; note: string; revision: number; updated_at: string } }>(
      "SELECT research.set_video_review($1::integer,$2::text,$3::text,$4::text,$5::integer) AS result", [id, decision, platform, note, revision]);
    revalidateTag("media-catalogue", { expire: 0 });
    const [item] = await reviewQuery("SELECT * FROM research.video_review_items WHERE id=$1::integer", [id]);
    return Response.json({ ...rows[0].result, ...(item as object) }, { headers: { "Cache-Control": "private, no-store" } });
  } catch (error) {
    const code = (error as { code?: string }).code;
    if (code === "22023") return new Response("Invalid review", { status: 400 });
    const conflict = code === "40001";
    return Response.json({ error: conflict ? "تغيّر القرار في جلسة أخرى. أعد تحميل الصفحة." : "تعذّر حفظ القرار. حاول مجددًا." }, { status: conflict ? 409 : 503 });
  }
}
