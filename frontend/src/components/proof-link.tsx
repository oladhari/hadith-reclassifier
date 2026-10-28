import Link from "next/link";
import { ArrowUpLeft, BookOpen } from "lucide-react";
export function ProofLink({ href, title, description, action = "فتح الدليل ومصادره" }: {
  href: string; title: string; description?: string; action?: string;
}) {
  return <Link className="proof-link" href={href}>
    <span className="proof-link-icon" aria-hidden="true"><BookOpen size={22} /></span>
    <span className="proof-link-copy"><strong>{title}</strong>{description && <span>{description}</span>}</span>
    <span className="proof-link-action">{action}<ArrowUpLeft size={18} aria-hidden="true" /></span>
  </Link>;
}
