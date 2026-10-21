import { archive } from "@/lib/archive";
import { publicEvidence } from "@/lib/public-evidence";
import { MediaOriginal } from "./source-viewer";
import type { MatchSet } from "@/lib/topics";
export function ArchiveMatches({ baseURL }: { matches: MatchSet; page?: number; baseURL: string; extraIds?: number[] }) {
 const ids = publicEvidence(baseURL);
 return <section className="archive-index-panel" id="archive-matches"><h2>الأدلة وصفحات الكتب</h2>
 <p>اقرأ النص في صفحته، وميّز كلام المؤلف من تعليقات المحقق ووجه الاستدلال به.</p>
 <div className="source-bundle-list">{ids.map(id => { const item = archive.find(a => a.id === id); return item ? <article className="source-bundle" key={id}><MediaOriginal item={item}/></article> : null; })}</div>
 {!ids.length && <p className="muted">لم تُنشر الأدلة المصوّرة لهذا الملف بعد. يمكنك الآن قراءة السؤال ومواضع الاختلاف في هذا الملف.</p>}
 </section>;
}
