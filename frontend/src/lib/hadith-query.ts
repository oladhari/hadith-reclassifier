// Shared, pure parsing for Arabic/Western number input and public hadith search.
export function latinDigits(value: string) {
  return value.normalize("NFKC").replace(/[٠-٩۰-۹]/g, c => String(c.charCodeAt(0) >= 0x6f0 ? c.charCodeAt(0)-0x6f0 : c.charCodeAt(0)-0x660)).replace(/٫/g,".");
}
export function hadithNumber(value: string) {
  const text = latinDigits(value).trim();
  return /^\d{1,8}(?:\.\d{1,6})?$/.test(text) ? String(Number(text)) : "";
}
export function hadithWords(value: string) {
  return latinDigits(value).normalize("NFKC").replace(/[\u064B-\u065F\u0670\u0640]/g, "").replace(/[أإآٱ]/g,"ا").replace(/ى/g,"ي").toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
}
const names: [string,string][] = [
 ["صحيح البخاري","bukhari"],["البخاري","bukhari"],["بخاري","bukhari"],["bukhari","bukhari"],
 ["صحيح مسلم","muslim"],["مسلم","muslim"],["muslim","muslim"],
 ["موطأ مالك","malik"],["موطا مالك","malik"],["malik","malik"],
 ["سنن أبي داود","abudawud"],["سنن ابي داود","abudawud"],["أبو داود","abudawud"],["ابو داود","abudawud"],["abudawud","abudawud"],
 ["سنن الترمذي","tirmidhi"],["الترمذي","tirmidhi"],["tirmidhi","tirmidhi"],
 ["سنن النسائي","nasai"],["النسائي","nasai"],["nasai","nasai"],
 ["سنن ابن ماجه","ibnmajah"],["ابن ماجه","ibnmajah"],["ibnmajah","ibnmajah"],
];
export function parseHadithQuery(q: string, id = "", collection = "") {
 let text = latinDigits(q).trim();
 for (const [name,slug] of names) {
  if (text.toLowerCase() === name.toLowerCase()) { collection ||= slug; text=""; break; }
  if (text.toLowerCase().startsWith(name.toLowerCase()) && /^[\s:：#]/.test(text.slice(name.length))) {
   collection ||= slug; text=text.slice(name.length).replace(/^[\s:：]+/,""); break;
  }
 }
 const numeric = text.replace(/^(?:(?:حديث|الحديث|رقم|حديث رقم)\s*[:：]?\s*|#\s*)+/u,"").trim();
 const number = hadithNumber(id) || hadithNumber(numeric);
 return { q: number && hadithNumber(numeric) ? "" : text, id: number, collection };
}
export function hadithHref(collection: string, number: number | string) {
 return `/corpus/${encodeURIComponent(collection)}/${encodeURIComponent(String(number))}`;
}
