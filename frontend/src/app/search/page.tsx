"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { Search, Filter, CheckCircle, Clock } from "lucide-react";
import { api, type Hadith, type Collection } from "@/lib/api";

const COLLECTIONS: { value: Collection | ""; label: string }[] = [
  { value: "", label: "جميع الكتب" },
  { value: "bukhari", label: "صحيح البخاري" },
  { value: "muslim", label: "صحيح مسلم" },
  { value: "malik", label: "موطأ مالك" },
  { value: "abudawud", label: "سنن أبي داود" },
  { value: "tirmidhi", label: "سنن الترمذي" },
  { value: "nasai", label: "سنن النسائي" },
  { value: "ibnmajah", label: "سنن ابن ماجه" },
];

const COLLECTION_LABELS: Record<string, string> = {
  bukhari: "صحيح البخاري",
  muslim: "صحيح مسلم",
  malik: "موطأ مالك",
  abudawud: "سنن أبي داود",
  tirmidhi: "سنن الترمذي",
  nasai: "سنن النسائي",
  ibnmajah: "سنن ابن ماجه",
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [collection, setCollection] = useState<Collection | "">("");
  const [results, setResults] = useState<Hadith[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const search = useCallback(async (p = 1) => {
    setLoading(true);
    setSearched(true);
    try {
      const data = await api.listHadiths({
        search: query || undefined,
        collection: collection || undefined,
        page: p,
        page_size: 20,
      });
      setResults(data.items);
      setTotal(data.total);
      setPage(p);
    } finally {
      setLoading(false);
    }
  }, [query, collection]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-stone-900 mb-1">البحث في الأحاديث</h1>
        <p className="text-stone-500 text-sm">ابحث في جميع الكتب المستوردة بالنص أو سلسلة الرواة</p>
      </div>

      {/* Search bar */}
      <div className="bg-white border border-stone-200 rounded-xl p-4 shadow-sm space-y-3">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && search()}
              placeholder="ابحث في نص الحديث أو الرواة..."
              className="w-full pr-10 pl-4 py-2.5 border border-stone-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <select
            value={collection}
            onChange={(e) => setCollection(e.target.value as Collection | "")}
            className="border border-stone-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {COLLECTIONS.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          <button
            onClick={() => search()}
            disabled={loading}
            className="flex items-center gap-2 bg-emerald-800 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            <Filter className="w-4 h-4" />
            {loading ? "جارٍ البحث..." : "بحث"}
          </button>
        </div>
      </div>

      {/* Results */}
      {searched && (
        <div>
          <p className="text-sm text-stone-500 mb-4">{total.toLocaleString("ar-SA")} نتيجة</p>
          <div className="space-y-3">
            {results.map((h) => (
              <Link
                key={h.id}
                href={`/hadith/${h.id}`}
                className="block bg-white border border-stone-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-shrink-0">
                    {h.is_processed ? (
                      <CheckCircle className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <Clock className="w-5 h-5 text-stone-300" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2 flex-wrap justify-end">
                      {h.traditional_grade && (
                        <span className="text-xs text-stone-400">{h.traditional_grade}</span>
                      )}
                      {h.hadith_number && (
                        <span className="text-xs text-stone-400">#{h.hadith_number}</span>
                      )}
                      <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium">
                        {COLLECTION_LABELS[h.collection] ?? h.collection}
                      </span>
                    </div>
                    <p className="text-sm text-stone-700 line-clamp-3 font-hadith text-right leading-8">
                      {h.text_arabic || h.text_english}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
            {results.length === 0 && !loading && (
              <div className="text-center py-12 text-stone-400">
                لا توجد نتائج. جرّب استيراد الأحاديث من لوحة التحكم أولاً.
              </div>
            )}
          </div>

          {/* Pagination */}
          {total > 20 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <button
                onClick={() => search(page + 1)}
                disabled={page * 20 >= total || loading}
                className="px-4 py-2 border border-stone-200 rounded-lg text-sm disabled:opacity-40 hover:bg-stone-50"
              >
                التالي
              </button>
              <span className="text-sm text-stone-500">صفحة {page} من {Math.ceil(total / 20)}</span>
              <button
                onClick={() => search(page - 1)}
                disabled={page === 1 || loading}
                className="px-4 py-2 border border-stone-200 rounded-lg text-sm disabled:opacity-40 hover:bg-stone-50"
              >
                السابق
              </button>
            </div>
          )}
        </div>
      )}

      {!searched && (
        <div className="text-center py-16 text-stone-400">
          أدخل كلمة بحث أو اختر كتاباً لاستعراض الأحاديث.
        </div>
      )}
    </div>
  );
}
