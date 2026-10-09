"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle, XCircle, Loader2, BookOpen, AlertTriangle, User, Link2, Brain, Star, ArrowRight } from "lucide-react";
import { api, type HadithWithClassification } from "@/lib/api";

const COLLECTION_LABELS: Record<string, string> = {
  bukhari: "صحيح البخاري",
  muslim: "صحيح مسلم",
  malik: "موطأ مالك",
  abudawud: "سنن أبي داود",
  tirmidhi: "سنن الترمذي",
  nasai: "سنن النسائي",
  ibnmajah: "سنن ابن ماجه",
};

const REASON_LABELS: Record<string, string> = {
  quran_contradiction: "يعارض القرآن الكريم",
  historical_contradiction: "تناقض تاريخي",
  logical_contradiction: "تناقض منطقي",
  broken_chain: "انقطاع في السند",
  weak_narrator: "راوٍ ضعيف",
  fabricator_narrator: "راوٍ متهم بالكذب أو الوضع",
  sectarian_bias: "تحيّز طائفي",
  legendary_content: "محتوى أسطوري أو خرافي",
  internal_contradiction: "تناقض داخلي",
  parallel_narration_conflict: "يعارض رواية أقوى",
  other: "سبب آخر",
};

function ScoreBadge({ label, score }: { label: string; score: number | null }) {
  if (score === null) return null;
  const color = score >= 70
    ? "text-emerald-700 bg-emerald-50 border-emerald-200"
    : score >= 40
    ? "text-amber-700 bg-amber-50 border-amber-200"
    : "text-red-700 bg-red-50 border-red-200";
  return (
    <div className={`flex flex-col items-center px-4 py-2 rounded-lg border ${color}`}>
      <span className="text-2xl font-bold">{score}</span>
      <span className="text-xs">{label}</span>
    </div>
  );
}

export default function HadithDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [data, setData] = useState<HadithWithClassification | null>(null);
  const [loading, setLoading] = useState(true);
  const [classifying, setClassifying] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getHadith(id).then(setData).catch(() => setError("الحديث غير موجود")).finally(() => setLoading(false));
  }, [id]);

  const classify = async () => {
    setClassifying(true);
    try {
      const cls = await api.classify(id);
      setData((prev) => prev ? { ...prev, classification: cls } : prev);
    } catch {
      setError("فشل التصنيف. تحقق من إعدادات مفتاح API.");
    } finally {
      setClassifying(false);
    }
  };

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-emerald-600" /></div>;
  if (error || !data) return <div className="text-center py-20 text-red-500">{error || "غير موجود"}</div>;

  const { hadith, classification } = data;
  const accepted = classification?.verdict === "accepted";

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          {hadith.traditional_grade && (
            <span className="text-sm text-stone-500 italic">التصنيف التقليدي: {hadith.traditional_grade}</span>
          )}
          {hadith.hadith_number && (
            <span className="text-sm text-stone-400">حديث رقم {hadith.hadith_number}</span>
          )}
          <span className="text-sm bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium">
            {COLLECTION_LABELS[hadith.collection] ?? hadith.collection}
          </span>
        </div>
        <button onClick={() => router.back()} className="text-stone-400 hover:text-stone-700 transition-colors">
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>

      {/* Verdict banner */}
      {classification && (
        <div className={`flex items-start gap-4 p-5 rounded-xl border ${accepted ? "bg-emerald-50 border-emerald-200" : "bg-red-50 border-red-200"}`}>
          {accepted
            ? <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
            : <XCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />}
          <div className="flex-1">
            <div className="font-bold text-lg mb-1">
              {accepted ? `مقبول — الصحيح العثماني رقم ${classification.sahih_othmani_number}` : "مردود"}
            </div>
            {classification.rejection_reasons && classification.rejection_reasons.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {classification.rejection_reasons.map((r) => (
                  <span key={r} className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                    {REASON_LABELS[r] ?? r}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="flex gap-3 flex-shrink-0">
            <ScoreBadge label="السند" score={classification.chain_score ?? null} />
            <ScoreBadge label="المتن" score={classification.content_score ?? null} />
            <ScoreBadge label="الإجمالي" score={classification.overall_score ?? null} />
          </div>
        </div>
      )}

      {/* Arabic hadith text */}
      <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-stone-500 text-sm font-medium">
          <BookOpen className="w-4 h-4" /> نص الحديث
        </div>
        {hadith.text_arabic && (
          <p className="font-hadith text-stone-900 border-b border-stone-100 pb-5" dir="rtl">
            {hadith.text_arabic}
          </p>
        )}
        {hadith.text_english && (
          <p className="text-stone-500 text-sm leading-7 italic" dir="ltr">{hadith.text_english}</p>
        )}
      </div>

      {/* Chain */}
      {hadith.narrator_chain_raw && (
        <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-2 text-stone-500 text-sm font-medium mb-3">
            <Link2 className="w-4 h-4" /> سلسلة الإسناد
          </div>
          <p className="font-hadith text-stone-700 text-base" dir="rtl">{hadith.narrator_chain_raw}</p>
        </div>
      )}

      {/* AI Analysis */}
      {classification && (
        <div className="space-y-4">
          {classification.chain_analysis && (
            <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2 text-stone-500 text-sm font-medium mb-3">
                <Link2 className="w-4 h-4" /> تحليل الإسناد
              </div>
              <p className="text-sm text-stone-700 leading-7">{classification.chain_analysis}</p>
            </div>
          )}

          {classification.narrator_issues && classification.narrator_issues.length > 0 && (
            <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2 text-stone-500 text-sm font-medium mb-3">
                <User className="w-4 h-4" /> مشكلات الرواة
              </div>
              <div className="space-y-2">
                {classification.narrator_issues.map((ni, i) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-stone-800">{ni.narrator}</span>
                      <span className="text-stone-600">: {ni.issue}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {classification.quran_references && classification.quran_references.length > 0 && (
            <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2 text-stone-500 text-sm font-medium mb-3">
                <Star className="w-4 h-4 text-emerald-600" /> الآيات القرآنية المرجعية
              </div>
              <div className="space-y-3">
                {classification.quran_references.map((ref, i) => (
                  <div key={i} className="text-sm">
                    <span className="font-semibold text-emerald-700">سورة {ref.surah} — آية {ref.ayah}</span>
                    <p className="font-hadith text-stone-700 mt-1" dir="rtl">{ref.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {classification.ai_reasoning && (
            <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2 text-stone-500 text-sm font-medium mb-3">
                <Brain className="w-4 h-4" /> التحليل العلمي بالذكاء الاصطناعي
              </div>
              <p className="text-sm text-stone-700 leading-7 whitespace-pre-line">{classification.ai_reasoning}</p>
            </div>
          )}
        </div>
      )}

      {/* Classify button */}
      {!classification && (
        <button
          onClick={classify}
          disabled={classifying}
          className="flex items-center gap-2 bg-emerald-800 text-white px-6 py-3 rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors"
        >
          {classifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
          {classifying ? "جارٍ التصنيف بالذكاء الاصطناعي..." : "تصنيف هذا الحديث"}
        </button>
      )}
    </div>
  );
}
