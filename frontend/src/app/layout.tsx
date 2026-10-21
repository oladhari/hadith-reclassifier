import type { Metadata } from "next";
import { Noto_Naskh_Arabic, IBM_Plex_Sans_Arabic } from "next/font/google";
import Link from "next/link";
import SiteHeader from "@/components/site-header";
import "./globals.css";
const serif = Noto_Naskh_Arabic({
  subsets: ["arabic", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic-serif",
});
const sans = IBM_Plex_Sans_Arabic({
  subsets: ["arabic", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic-sans",
  display: "swap",
});
export const metadata: Metadata = {
  title: {
    default: "موسوعة الرد على العباسيين | المصدر أولًا",
    template: "%s | موسوعة الرد على العباسيين",
  },
  description:
    "مكتبة بحثية وفق المنهج العثماني: مصادر مصوّرة، روايات وأسانيد، وملفات تقود من السؤال إلى الدليل. نسخة أولية قيد الإعداد.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl">
      <body className={`${sans.variable} ${serif.variable}`}>
        <a className="skip-link" href="#main">
          انتقل إلى المحتوى
        </a>
        <SiteHeader />
        <main id="main" className="shell main-content">
          {children}
        </main>
        <footer className="site-footer">
          <div className="shell footer-inner">
            <div>
              <strong>موسوعة الرد على العباسيين</strong>
              <p>اقرأ الحُجّة. افتح المصدر. تتبّع الرواية.</p>
            </div>
            <div className="footer-links">
              <Link href="/about">عن المشروع والتصحيحات</Link>
              <Link href="/methodology">سياسة المراجعة</Link>
            </div>
            <small>النصّ في مصدره، والحجّة في سياقها.</small>
          </div>
        </footer>
      </body>
    </html>
  );
}
