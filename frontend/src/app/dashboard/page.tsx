"use client";

import { useState, useEffect } from "react";
import { CheckCircle, XCircle, Database, Zap, Loader2, BarChart3 } from "lucide-react";
import { api, type Stats, type Collection } from "@/lib/api";

const COLLECTIONS: { value: Collection; label: string }[] = [
  { value: "bukhari", label: "صحيح البخاري" },
  { value: "muslim", label: "صحيح مسلم" },
  { value: "malik", label: "موطأ مالك" },
  { value: "abudawud", label: "سنن أبي داود" },
  { value: "tirmidhi", label: "سنن الترمذي" },
  { value: "nasai", label: "سنن النسائي" },
  { value: "ibnmajah", label: "سنن ابن ماجه" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [ingestCollection, setIngestCollection] = useState<Collection>("bukhari");
  const [ingestLimit, setIngestLimit] = useState(200);
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<string>("");
  const [classifyCollection, setClassifyCollection] = useState<Collection | "">("");
  const [classifyLimit, setClassifyLimit] = useState(10);
  const [classifyLoading, setClassifyLoading] = useState(false);
  const [classifyResult, setClassifyResult] = useState<string>("");

  const loadStats = () => api.getStats().then(setStats).catch(console.error);

  useEffect(() => { loadStats(); }, []);

  const runIngest = async () => {
    setIngestLoading(true);
    setIngestResult("");
    try {
      const res = await api.ingest(ingestCollection, ingestLimit) as { added: number; skipped: number; total_in_collection: number };
      setIngestResult(`تمت إضافة ${res.added} حديث، تم تجاوز ${res.skipped} مكرر. إجمالي الكتاب: ${res.total_in_collection}`);
      loadStats();
    } catch (e: unknown) {
      setIngestResult(`خطأ: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIngestLoading(false);
    }
  };

  const runClassify = async () => {
    setClassifyLoading(true);
    setClassifyResult("");
    try {
      const res = await api.bulkClassify(classifyCollection || undefined, classifyLimit) as { processed: number; accepted: number; rejected: number };
      setClassifyResult(`تمت معالجة ${res.processed}: مقبول ${res.accepted}، مردود ${res.rejected}`);
      loadStats();
    } catch (e: unknown) {
      setClassifyResult(`خطأ: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setClassifyLoading(false);
    }
  };

  const acceptRate = stats && stats.total_classified > 0
    ? Math.round((stats.accepted / stats.total_classified) * 100)
    : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-stone-900 mb-1 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-emerald-700" /> لوحة التحكم
        </h1>
        <p className="text-stone-500 text-sm">إدارة استيراد البيانات وتشغيل التصنيف الجماعي</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "إجمالي المصنَّفة", value: stats?.total_classified ?? "—", icon: <Database className="w-5 h-5 text-stone-400" /> },
          { label: "مقبول", value: stats?.accepted ?? "—", icon: <CheckCircle className="w-5 h-5 text-emerald-500" /> },
          { label: "مردود", value: stats?.rejected ?? "—", icon: <XCircle className="w-5 h-5 text-red-400" /> },
          { label: "رقم الصحيح العثماني", value: stats?.sahih_othmani_count ?? "—", icon: <Zap className="w-5 h-5 text-amber-500" /> },
        ].map((s) => (
          <div key={s.label} className="bg-white border border-stone-200 rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-stone-400 font-medium">{s.label}</span>
              {s.icon}
            </div>
            <div className="text-3xl font-bold text-stone-900">
              {typeof s.value === "number" ? s.value.toLocaleString("ar-SA") : s.value}
            </div>
          </div>
        ))}
      </div>

      {/* Acceptance rate */}
      {stats && stats.total_classified > 0 && (
        <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-2 text-sm">
            <span className="text-stone-500">نسبة القبول</span>
            <span className="font-semibold text-emerald-700">{acceptRate}%</span>
          </div>
          <div className="w-full bg-stone-100 rounded-full h-3">
            <div className="bg-emerald-500 h-3 rounded-full transition-all" style={{ width: `${acceptRate}%` }} />
          </div>
        </div>
      )}

      {/* Ingest */}
      <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 font-semibold text-stone-800">
          <Database className="w-5 h-5 text-emerald-700" /> استيراد الأحاديث من الملفات المحلية
        </div>
        <p className="text-sm text-stone-500">تحميل الأحاديث من ملفات JSON المحلية وحفظها في قاعدة البيانات.</p>
        <div className="flex gap-3 flex-wrap">
          <select
            value={ingestCollection}
            onChange={(e) => setIngestCollection(e.target.value as Collection)}
            className="border border-stone-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {COLLECTIONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <input
            type="number"
            value={ingestLimit}
            onChange={(e) => setIngestLimit(Number(e.target.value))}
            min={1} max={10000}
            className="w-28 border border-stone-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="الحد"
          />
          <button
            onClick={runIngest}
            disabled={ingestLoading}
            className="flex items-center gap-2 bg-emerald-800 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            {ingestLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
            {ingestLoading ? "جارٍ الاستيراد..." : "استيراد"}
          </button>
        </div>
        {ingestResult && <p className="text-sm text-stone-600 bg-stone-50 rounded-lg px-3 py-2">{ingestResult}</p>}
      </div>

      {/* Bulk classify */}
      <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 font-semibold text-stone-800">
          <Zap className="w-5 h-5 text-amber-500" /> التصنيف الجماعي بالذكاء الاصطناعي
        </div>
        <p className="text-sm text-stone-500">
          تشغيل تصنيف OpenAI على الأحاديث غير المعالجة. كل طلب يستهلك استدعاء من API.
        </p>
        <div className="flex gap-3 flex-wrap">
          <select
            value={classifyCollection}
            onChange={(e) => setClassifyCollection(e.target.value as Collection | "")}
            className="border border-stone-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">جميع الكتب</option>
            {COLLECTIONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
          <input
            type="number"
            value={classifyLimit}
            onChange={(e) => setClassifyLimit(Number(e.target.value))}
            min={1} max={100}
            className="w-28 border border-stone-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            placeholder="الحد"
          />
          <button
            onClick={runClassify}
            disabled={classifyLoading}
            className="flex items-center gap-2 bg-amber-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-amber-500 disabled:opacity-50 transition-colors"
          >
            {classifyLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {classifyLoading ? "جارٍ التصنيف..." : "تشغيل التصنيف"}
          </button>
        </div>
        {classifyResult && <p className="text-sm text-stone-600 bg-stone-50 rounded-lg px-3 py-2">{classifyResult}</p>}
      </div>
    </div>
  );
}
