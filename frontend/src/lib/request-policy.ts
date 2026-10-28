// Query values remain data. SQL is parameterized separately in live-corpus.ts.
const enums: Record<string, readonly string[]> = {
  collection: ["bukhari", "muslim", "malik", "abudawud", "tirmidhi", "nasai", "ibnmajah"],
  status: ["unreviewed", "in_progress", "needs_review", "accepted", "rejected", "filtered", "book"],
  kind: ["image", "pdf", "document", "video", "audio"],
  section: ["books", "excerpts", "video", "audio", "all"],
  scope: ["page", "excerpt", "full_book", "article", "lecture", "clip", "audio"],
  topic: ["uthman", "camel", "allegiance", "siffin", "virtues", "narrators", "karbala", "manuscripts"],
};
export function requestProblem(url: URL): { status: number; message: string } | null {
  if (url.href.length > 4096) return { status: 414, message: "رابط الطلب أطول من الحد المسموح." };
  const seen = new Set<string>();
  for (const [key, value] of url.searchParams) {
    if (seen.has(key)) return { status: 400, message: "لا يمكن تكرار معامل البحث نفسه." };
    seen.add(key);
    if (seen.size > 12 || key.length > 32 || /^(?:__proto__|constructor|prototype)(?:$|\[|\.)/.test(key))
      return { status: 400, message: "معاملات الطلب غير صالحة." };
    const limit = key === "q" ? 160 : key === "category" ? 80 : key === "_rsc" ? 128 : 256;
    if (value.length > limit || /[\u0000-\u001f\u007f]/.test(value))
      return { status: 400, message: "قيمة البحث أطول من المسموح أو تحتوي على محارف غير صالحة." };
    if (key === "q" && value.trim().split(/\s+/).filter(Boolean).length > 16)
      return { status: 400, message: "استخدم 16 كلمة أو أقل في البحث." };
    if (!value) continue;
    if (Object.hasOwn(enums, key) && !enums[key].includes(value))
      return { status: 400, message: "خيار البحث غير صالح." };
    if (key === "page" && (!/^[1-9]\d{0,4}$/.test(value) || Number(value) > 10000))
      return { status: 400, message: "رقم الصفحة غير صالح." };
    if (key === "id" && url.pathname === "/corpus" && !/^\d{1,8}(?:\.\d{1,6})?$/.test(value))
      return { status: 400, message: "رقم الرواية غير صالح." };
    if (["start", "end"].includes(key) && (!/^\d{1,7}(?:\.\d{1,16})?$/.test(value) || Number(value) > 604800))
      return { status: 400, message: "موضع التشغيل غير صالح." };
    if (key === "download" && !["0", "1"].includes(value))
      return { status: 400, message: "خيار التنزيل غير صالح." };
  }
  return null;
}
export function queryText(value: unknown, max = 160): string {
  return typeof value === "string" ? value.slice(0, max) : "";
}
