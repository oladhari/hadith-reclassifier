import { isVideoReviewer } from "@/lib/video-review-auth";
import { reviewItems, reviewQuery } from "@/lib/video-review";
export async function GET() {
  if (!await isVideoReviewer()) return new Response("Unauthorized", { status: 401 });
  const [items, history] = await Promise.all([reviewItems(), reviewQuery("SELECT * FROM research.video_review_history ORDER BY event_id")]);
  return Response.json({ exported_at: new Date().toISOString(), items, history }, { headers: {
    "Cache-Control": "private, no-store", "Content-Disposition": 'attachment; filename="video-review.json"', "X-Robots-Tag": "noindex, nofollow",
  } });
}
