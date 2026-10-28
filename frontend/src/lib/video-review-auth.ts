import "server-only";
import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";
export const reviewCookie = "othmani-video-review";
const lifetime = 8 * 60 * 60;
function equal(a: string, b: string) {
  const x = Buffer.from(a), y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}
export function validReviewCode(code: string) {
  const secret = process.env.VIDEO_REVIEW_ACCESS_CODE;
  return Boolean(secret && code.length <= 128 && equal(code, secret));
}
export function createReviewSession() {
  const secret = process.env.VIDEO_REVIEW_ACCESS_CODE;
  if (!secret) throw new Error("Video review is not configured");
  const expires = String(Math.floor(Date.now() / 1000) + lifetime);
  return `${expires}.${createHmac("sha256", secret).update(`video-review:${expires}`).digest("hex")}`;
}
export async function isVideoReviewer() {
  const secret = process.env.VIDEO_REVIEW_ACCESS_CODE;
  const value = (await cookies()).get(reviewCookie)?.value || "";
  const match = /^(\d+)\.([a-f0-9]{64})$/.exec(value);
  if (!secret || !match || Number(match[1]) <= Date.now() / 1000 || Number(match[1]) > Date.now() / 1000 + lifetime + 60) return false;
  return equal(match[2], createHmac("sha256", secret).update(`video-review:${match[1]}`).digest("hex"));
}
export function sameOrigin(request: Request) {
  const origin = request.headers.get("origin");
  if (!origin) return false;
  try {
    const parsed = new URL(origin);
    return parsed.host === request.headers.get("host") && ["http:", "https:"].includes(parsed.protocol);
  } catch { return false; }
}
