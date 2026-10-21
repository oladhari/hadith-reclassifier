import { NextRequest } from "next/server";
import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { Readable } from "node:stream";
import path from "node:path";
import { archive } from "@/lib/archive";
import objectKeys from "@/content/media-objects.json";
export const runtime = "nodejs";
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const item = archive.find((a) => String(a.id) === id);
  if (!item) return new Response("Not found", { status: 404 });
  const remoteBase = process.env.MEDIA_PUBLIC_BASE_URL?.replace(/\/$/, "");
  if (remoteBase) {
    const key = (objectKeys as Record<string, string>)[item.id];
    if (!key || !/^originals\/sha256\/[a-f0-9]{2}\/[a-f0-9]{64}$/.test(key))
      return new Response("Not found", { status: 404 });
    const remoteURL = `${remoteBase}/${key}`;
    if (request.nextUrl.searchParams.get("download") === "1" && item.size <= 4 * 1024 * 1024) {
      const response = await fetch(remoteURL, { signal: request.signal });
      if (!response.ok) return new Response("المادة غير متاحة مؤقتًا", { status: 502 });
      return new Response(response.body, { headers: {
        "Content-Type": item.mime,
        "Content-Length": String(item.size),
        "Content-Disposition": `attachment; filename="source-${item.id}${path.extname(item.path).replace(/[^a-zA-Z0-9.]/g, "")}"`,
        "X-Content-Type-Options": "nosniff",
      } });
    }
    return Response.redirect(remoteURL, 307);
  }

  const root = path.resolve(
    /* turbopackIgnore: true */ process.env.TELEGRAM_ARCHIVE_DIR ||
      path.resolve(
        /* turbopackIgnore: true */ process.cwd(),
        "../../telegram-archive/kkee9938",
      ),
  );
  const file = path.resolve(/* turbopackIgnore: true */ root, item.path);
  if (!file.startsWith(root + path.sep))
    return new Response("Not found", { status: 404 });
  let size: number;
  try {
    size = (await stat(/* turbopackIgnore: true */ file)).size;
  } catch {
    return new Response(
      "المادة غير متاحة مؤقتًا. حاول مجددًا لاحقًا.",
      { status: 503 },
    );
  }
  const headers: Record<string, string> = {
    "Content-Type": item.mime,
    "Accept-Ranges": "bytes",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "private, max-age=3600",
  };
  if (request.nextUrl.searchParams.get("download") === "1")
    headers["Content-Disposition"] =
      `attachment; filename="archive-${item.id}${path.extname(item.path).replace(/[^a-zA-Z0-9.]/g, "")}"`;
  const range = request.headers.get("range");
  let start = 0,
    end = size - 1;
  if (range) {
    const match = /^bytes=(\d*)-(\d*)$/.exec(range);
    if (!match || (!match[1] && !match[2]))
      return new Response(null, {
        status: 416,
        headers: { "Content-Range": `bytes */${size}` },
      });
    if (!match[1]) {
      start = Math.max(0, size - Number(match[2]));
    } else {
      start = Number(match[1]);
      if (match[2]) end = Math.min(end, Number(match[2]));
    }
    if (
      !Number.isSafeInteger(start) ||
      !Number.isSafeInteger(end) ||
      start > end ||
      start >= size
    )
      return new Response(null, {
        status: 416,
        headers: { "Content-Range": `bytes */${size}` },
      });
    headers["Content-Range"] = `bytes ${start}-${end}/${size}`;
  }
  headers["Content-Length"] = String(end - start + 1);
  const stream = createReadStream(/* turbopackIgnore: true */ file, {
    start,
    end,
  });
  request.signal.addEventListener("abort", () => stream.destroy(), {
    once: true,
  });
  return new Response(Readable.toWeb(stream) as ReadableStream, {
    status: range ? 206 : 200,
    headers,
  });
}
