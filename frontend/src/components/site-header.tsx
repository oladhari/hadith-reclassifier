"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Menu, X } from "lucide-react";
import { useState } from "react";
const links = [
  ["/topics", "القضايا والأدلة"],
  ["/library", "المكتبة"],
  ["/methodology", "المنهج"],
  ["/corpus", "المجموعة الحديثية"],
];
export default function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className="site-header">
      <div className="shell header-inner">
        <Link href="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark">
            <BookOpen size={25} />
          </span>
          <span>
            <strong>موسوعة الرد على العباسيين</strong>
            <small>المصدر أولًا · الحُجّة بميزانها</small>
          </span>
        </Link>
        <button
          className="menu-toggle"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-controls="main-navigation"
          aria-label={open ? "إغلاق القائمة" : "فتح القائمة"}
        >
          {open ? <X /> : <Menu />}
        </button>
        <nav
          id="main-navigation"
          className={open ? "main-nav open" : "main-nav"}
          aria-label="التنقل الرئيسي"
        >
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              aria-current={
                pathname.startsWith(href) ||
                (href === "/topics" && pathname.startsWith("/cases"))
                  ? "page"
                  : undefined
              }
              onClick={() => setOpen(false)}
            >
              {label}
            </Link>
          ))}
          <Link
            className="nav-start"
            href="/start"
            onClick={() => setOpen(false)}
          >
            ابدأ من هنا <span>↙</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
