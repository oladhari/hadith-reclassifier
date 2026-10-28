import { NextResponse } from "next/server";
import { createReviewSession, reviewCookie, sameOrigin, validReviewCode } from "@/lib/video-review-auth";
export async function POST(request: Request) {
  if (!sameOrigin(request)) return new Response("Forbidden", { status: 403 });
  const form = await request.formData();
  const logout = form.get("logout") === "1";
  const success = logout || validReviewCode(String(form.get("code") || ""));
  const response = NextResponse.redirect(new URL(`/review/videos${success ? "" : "?error=1"}`, request.url), 303);
  response.headers.set("Cache-Control", "private, no-store");
  if (success) response.cookies.set(reviewCookie, logout ? "" : createReviewSession(), {
    httpOnly: true, secure: new URL(request.url).protocol === "https:", sameSite: "strict", path: "/", maxAge: logout ? 0 : 8 * 60 * 60,
  });
  return response;
}
