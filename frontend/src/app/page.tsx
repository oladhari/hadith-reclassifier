import Link from "next/link";
import { BookOpen, Search, BarChart3, BookMarked, ArrowLeft, CheckCircle, XCircle, HelpCircle } from "lucide-react";

export default function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="text-center py-16">
        <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-800 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
          <BookOpen className="w-4 h-4" />
          أداة البحث الإسلامي
        </div>
        <h1 className="text-4xl font-bold text-stone-900 mb-4">
          إعادة تصنيف الحديث النبوي بالذكاء الاصطناعي
        </h1>
        <p className="text-xl text-stone-600 max-w-2xl mx-auto mb-8">
          منهجية شفافة وعلمية لإعادة تقييم الأحاديث النبوية باستخدام الذكاء الاصطناعي
          ومعايير الجرح والتعديل وأصول علوم الحديث.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link
            href="/search"
            className="flex items-center gap-2 bg-emerald-800 text-white px-6 py-3 rounded-lg font-medium hover:bg-emerald-700 transition-colors"
          >
            <Search className="w-4 h-4" /> البحث في الأحاديث <ArrowLeft className="w-4 h-4" />
          </Link>
          <Link
            href="/sahih-othmani"
            className="flex items-center gap-2 border border-emerald-800 text-emerald-800 px-6 py-3 rounded-lg font-medium hover:bg-emerald-50 transition-colors"
          >
            <BookMarked className="w-4 h-4" /> الصحيح العثماني
          </Link>
        </div>
      </section>

      {/* Criteria */}
      <section className="grid md:grid-cols-3 gap-6">
        {[
          {
            icon: <CheckCircle className="w-6 h-6 text-emerald-600" />,
            title: "مقبول — الصحيح العثماني",
            items: ["سند متصل موثوق", "رواة ثقات", "لا يعارض القرآن الكريم", "صحيح تاريخياً", "سليم من التناقض العقلي"],
          },
          {
            icon: <XCircle className="w-6 h-6 text-red-500" />,
            title: "مردود — مع بيان العلة",
            items: ["يعارض القرآن الكريم", "انقطاع في السند", "راوٍ متهم بالكذب أو الوضع", "استحالة تاريخية", "محتوى أسطوري أو خرافي"],
          },
          {
            icon: <HelpCircle className="w-6 h-6 text-amber-500" />,
            title: "منهجية التقييم",
            items: ["الذكاء الاصطناعي (OpenAI) محكّماً رئيسياً", "فحص آلي لاتصال السند", "مراجعة تراجم الرواة", "المقارنة مع الروايات الأخرى", "توثيق كامل لكل قرار"],
          },
        ].map((card) => (
          <div key={card.title} className="bg-white rounded-xl border border-stone-200 p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              {card.icon}
              <h3 className="font-semibold text-stone-900">{card.title}</h3>
            </div>
            <ul className="space-y-2">
              {card.items.map((item) => (
                <li key={item} className="flex items-center gap-2 text-sm text-stone-600">
                  <span className="w-1.5 h-1.5 rounded-full bg-stone-400 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {/* Quick links */}
      <section className="grid md:grid-cols-2 gap-6">
        <Link href="/dashboard" className="group bg-white border border-stone-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-5 h-5 text-emerald-700" />
              <span className="font-semibold">لوحة التحكم</span>
            </div>
            <p className="text-sm text-stone-500">الإحصائيات، التصنيف الجماعي، استيراد البيانات</p>
          </div>
          <ArrowLeft className="w-5 h-5 text-stone-400 group-hover:text-emerald-700 transition-colors" />
        </Link>
        <Link href="/sahih-othmani" className="group bg-white border border-stone-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <BookMarked className="w-5 h-5 text-emerald-700" />
              <span className="font-semibold">الصحيح العثماني</span>
            </div>
            <p className="text-sm text-stone-500">استعراض الأحاديث المقبولة مرتبةً بالتسلسل</p>
          </div>
          <ArrowLeft className="w-5 h-5 text-stone-400 group-hover:text-emerald-700 transition-colors" />
        </Link>
      </section>
    </div>
  );
}
