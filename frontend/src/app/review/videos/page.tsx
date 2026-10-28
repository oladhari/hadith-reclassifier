import { isVideoReviewer } from "@/lib/video-review-auth";
import { reviewItems } from "@/lib/video-review";
import { VideoReview } from "@/components/video-review";
import { PageHeading } from "@/components/research-ui";
export const dynamic = "force-dynamic";
export const metadata = { title: "مراجعة الفيديوهات — خاص", robots: { index: false, follow: false } };
export default async function VideoReviewPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  if (!await isVideoReviewer()) {
    const params = await searchParams;
    return <><PageHeading eyebrow="إدارة خاصة" title="مراجعة الفيديوهات" description="أدخل رمز الوصول لعرض الفيديوهات وحفظ قرارات الظهور والإخفاء." />
      <form className="review-login" action="/api/video-review/session" method="post">
        <label>رمز الوصول<input type="password" name="code" autoComplete="current-password" maxLength={128} required /></label>
        {params.error && <p role="alert">رمز الوصول غير صحيح.</p>}
        <button className="button button-dark">دخول</button>
      </form></>;
  }
  return <><PageHeading eyebrow="إدارة خاصة" title="مراجعة الفيديوهات" description="شاهد الفيديو ثم قرّر ظهوره في الموقع. الإخفاء يحفظ الفيديو وأصله في قاعدة البيانات، ويمكن التراجع عنه." />
    <div className="review-toolbar"><a className="button button-outline" href="/api/video-review/export">تنزيل نسخة من القرارات والسجل</a>
      <form action="/api/video-review/session" method="post"><input type="hidden" name="logout" value="1" /><button className="button button-outline">خروج</button></form></div>
    <VideoReview initialItems={await reviewItems()} /></>;
}
