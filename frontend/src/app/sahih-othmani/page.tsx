"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { BookMarked, CheckCircle, Loader2, ChevronRight, ChevronLeft } from "lucide-react";
import { api, type Classification } from "@/lib/api";

export default function SahihOthmaniPage() {
  const [items, setItems] = useState<Classification[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const PAGE_SIZE = 20;

  useEffect(() => {
    setLoading(true);
    api.getSahihOthmani(page, PAGE_SIZE)
      .then((data) => {
        setItems(data);
        setHasMore(data.length === PAGE_SIZE);
      })
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-stone-900 mb-1 flex items-center gap-2">
          <BookMarked className="w-6 h-6 text-emerald-700" /> الصحيح العثماني
        </h1>
        <p className="text-stone-500 text-sm">
          مجموعة الأحاديث المقبولة — الروايات التي اجتازت جميع معايير التحقق.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20 text-stone-400">
          لا توجد أحاديث مقبولة بعد.{" "}
          <Link href="/dashboard" className="text-emerald-700 underline">
            شغّل التصنيف من لوحة التحكم
          </Link>
          .
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((cls) => (
            <Link
              key={cls.id}
              href={`/hadith/${cls.hadith_id}`}
              className="block bg-white border border-emerald-100 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 justify-end">
                    {cls.overall_score !== null && (
                      <span className="text-xs text-stone-400">الدرجة: {cls.overall_score}/100</span>
                    )}
                    <span className="text-sm font-medium text-emerald-700">مقبول</span>
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                  </div>
                  {cls.ai_reasoning && (
                    <p className="text-sm text-stone-600 line-clamp-2 text-right">{cls.ai_reasoning}</p>
                  )}
                </div>
                <div className="flex-shrink-0 w-12 h-12 bg-emerald-700 text-white rounded-lg flex items-center justify-center font-bold text-lg">
                  {cls.sahih_othmani_number}
                </div>
              </div>
            </Link>
          ))}

          <div className="flex items-center justify-center gap-4 pt-4">
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore || loading}
              className="flex items-center gap-1 px-4 py-2 border border-stone-200 rounded-lg text-sm disabled:opacity-40 hover:bg-stone-50"
            >
              التالي <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-stone-500">صفحة {page}</span>
            <button
              onClick={() => setPage((p) => p - 1)}
              disabled={page === 1 || loading}
              className="flex items-center gap-1 px-4 py-2 border border-stone-200 rounded-lg text-sm disabled:opacity-40 hover:bg-stone-50"
            >
              <ChevronRight className="w-4 h-4" /> السابق
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
