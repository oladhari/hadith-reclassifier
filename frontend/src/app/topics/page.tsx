import { topics } from "@/lib/topics";
import { PageHeading, TopicCard } from "@/components/research-ui";
export const metadata = { title: "محاور الموسوعة" };
export default function TopicsPage() {
 return <><PageHeading eyebrow="القضايا والأدلة" title="المحاور الرئيسية في الموسوعة" description="اختر القضية التي تبحث عنها، واقرأ الروايات ومواضع الاختلاف، ثم ارجع إلى الأدلة وصفحات الكتب داخل كل ملف." /><div className="topic-grid">{topics.map(topic => <TopicCard topic={topic} key={topic.slug} />)}</div></>;
}
