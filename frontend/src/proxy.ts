import { randomBytes } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import { requestProblem } from "./lib/request-policy";

function reject(status: number, message: string) {
  return new NextResponse(message, { status, headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff" } });
}
export function proxy(request: NextRequest) {
  // There is one public API, and it is read-only. Unknown/retired APIs never
  // enter the application or the Server Action request parser.
  if (request.nextUrl.pathname.startsWith("/api/") && !/^\/api\/media\/[1-9]\d{0,8}$/.test(request.nextUrl.pathname))
    return reject(404, "المسار غير موجود.");
  if (!["GET", "HEAD", "OPTIONS"].includes(request.method)) {
    const response = reject(405, "هذا المسار متاح للقراءة فقط.");
    response.headers.set("Allow", "GET, HEAD, OPTIONS");
    return response;
  }
  if (["GET", "HEAD"].includes(request.method) && (Number(request.headers.get("content-length")) > 0 || request.headers.has("transfer-encoding")))
    return reject(400, "طلب القراءة لا يقبل محتوى مرفقًا.");
  const problem = requestProblem(request.nextUrl);
  if (problem) return reject(problem.status, problem.message);
  if (request.nextUrl.pathname.startsWith("/api/") || request.method === "OPTIONS") return NextResponse.next();
  const nonce = randomBytes(24).toString("base64");
  const mediaOrigins = [process.env.MEDIA_PUBLIC_BASE_URL].flatMap(value => {
    try { const url = new URL(value || ""); return url.protocol === "https:" ? [url.origin] : []; } catch { return []; }
  }).join(" ");
  const policy = [
    "default-src 'self'", `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${process.env.NODE_ENV === "development" ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'", `img-src 'self' data: blob: ${mediaOrigins}`, "font-src 'self'",
    `media-src 'self' blob: ${mediaOrigins}`, `frame-src 'self' blob: ${mediaOrigins}`, `connect-src 'self' ${mediaOrigins}`,
    "object-src 'none'", "base-uri 'none'", "form-action 'self'", "frame-ancestors 'self'", "worker-src 'self' blob:",
    ...(request.nextUrl.protocol === "https:" ? ["upgrade-insecure-requests"] : []),
  ].join("; ");
  const headers = new Headers(request.headers);
  headers.set("x-nonce", nonce);
  headers.set("Content-Security-Policy", policy);
  const response = NextResponse.next({ request: { headers } });
  response.headers.set("Content-Security-Policy", policy);
  response.headers.set("Cache-Control", "private, no-store");
  return response;
}
export const config = {
  matcher: ["/((?!_next/|thumbnails/|transcripts/|collections/|documents/|evidence/|design/|favicon.ico).*)"],
};
