import type { Metadata } from "next";
import { Noto_Naskh_Arabic, Noto_Sans_Arabic } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { BookOpen, Search, BarChart3, BookMarked } from "lucide-react";

const notoNaskhArabic = Noto_Naskh_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic-serif",
});

const notoSansArabic = Noto_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic-sans",
});

export const metadata: Metadata = {
  title: "الصحيح العثماني — إعادة تصنيف الحديث",
  description: "نظام إعادة تصنيف الأحاديث النبوية بالذكاء الاصطناعي",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body className={`${notoSansArabic.className} ${notoNaskhArabic.variable} ${notoSansArabic.variable} bg-stone-50 text-stone-900 min-h-screen`}>
        <header className="bg-emerald-900 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <BookOpen className="w-7 h-7" />
              <div>
                <div className="font-bold text-lg leading-tight">الصحيح العثماني</div>
                <div className="text-emerald-300 text-xs">مشروع إعادة تصنيف الحديث</div>
              </div>
            </Link>
            <nav className="flex items-center gap-6 text-sm">
              <Link href="/search" className="flex items-center gap-1.5 hover:text-emerald-300 transition-colors">
                <Search className="w-4 h-4" /> البحث
              </Link>
              <Link href="/dashboard" className="flex items-center gap-1.5 hover:text-emerald-300 transition-colors">
                <BarChart3 className="w-4 h-4" /> لوحة التحكم
              </Link>
              <Link href="/sahih-othmani" className="flex items-center gap-1.5 hover:text-emerald-300 transition-colors">
                <BookMarked className="w-4 h-4" /> الصحيح العثماني
              </Link>
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
