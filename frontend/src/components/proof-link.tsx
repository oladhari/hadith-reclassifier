import Link from "next/link";
import { ArrowUpLeft, BookOpen } from "lucide-react";
export function ProofLink({ href, title, description, action = "فتح الدليل ومصادره", newTab }: {
  href: string; title: string; description?: string; action?: string; newTab?: boolean;
}) {
  return <Link className="proof-link" href={href} target={newTab ? "_blank" : undefined} rel={newTab ? "noopener noreferrer" : undefined}>
    <span className="proof-link-icon" aria-hidden="true"><BookOpen size={22} /></span>
    <span className="proof-link-copy"><strong>{title}</strong>{description && <span>{description}</span>}</span>
    <span className="proof-link-action">{action}<ArrowUpLeft size={18} aria-hidden="true" /></span>
  </Link>;
}
