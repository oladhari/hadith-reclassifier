import Link from "next/link";
import { ArrowUpLeft, BookOpen } from "lucide-react";
import { cases } from "@/lib/research";
import { type topics } from "@/lib/topics";
export function PageHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="page-heading">
      <span className="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  );
}
export function CaseCard({ item }: { item: (typeof cases)[number] }) {
  return (
    <Link className="case-card" href={`/cases/${item.slug}`}>
      <div className="card-top">
        <span className="case-type">{item.label}</span>

      </div>
      <BookOpen className="case-icon" size={26} />
      <h3>{item.title}</h3>
      <p>{item.subtitle}</p>
      <div className="card-bottom">
        <span className="status-dot">قيد البحث</span>
        <span className="card-action">
          استكشف الملف <ArrowUpLeft size={16} />
        </span>
      </div>
    </Link>
  );
}
export function StatusNote({ children }: { children: React.ReactNode }) {
  return (
    <div className="status-note">
      <span className="status-dot">حالة البحث</span>
      <p>{children}</p>
    </div>
  );
}

export function TopicCard({ topic }: { topic: (typeof topics)[number] }) {
  return (
    <Link className="topic-card" href={`/topics/${topic.slug}`}>
      <div className="topic-overline">
        <span>محور بحثي</span>
        <BookOpen size={18} />
      </div>
      <h3>{topic.title}</h3>
      <p>{topic.description}</p>
      <div className="topic-footer">
        <span>القضايا ومصادرها</span>
        <strong>
          تصفّح المحور <ArrowUpLeft size={16} />
        </strong>
      </div>
    </Link>
  );
}
