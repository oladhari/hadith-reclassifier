import Link from "next/link";
import { PageHeading, StatusNote } from "@/components/research-ui";
export const metadata = { title: "مشروع الكتاب العثماني" };
export default function BookProject() {
  return (
    <>
      <PageHeading
        eyebrow="المرحلة الثانية من المشروع"
        title="مشروع الكتاب العثماني"
        description="من المجموعة المحلية إلى دراسة موثقة للأحاديث، ثم إعداد نسخة كتاب من النتائج المعتمدة."
      />
      <StatusNote>
        لم تُعتمد نسخة نهائية للكتاب بعد. الأحكام الآلية الموجودة في النظام
        التجريبي ليست مراجعة علمية ولا تُعرض هنا باعتبارها أحاديث محققة.
      </StatusNote>
      <div className="guide-list">
        {[
          [
            "01",
            "حفظ النصوص وربطها",
            "المجموعة المحلية متاحة للبحث. نطابق الأرقام والألفاظ مع الطبعات ونربط الروايات والطرق دون حذف أصولها.",
          ],
          [
            "02",
            "تطبيق طبقات الفحص",
            "تُدرس كل رواية وفق القواعد الموثقة، وتظهر الأدلة والاعتراضات والمسائل غير المحسومة.",
          ],
          [
            "03",
            "المراجعة واعتماد المداخل",
            "تحتاج النتيجة إلى مراجعة بشرية قبل الترقيم النهائي أو إدراج الحديث في نسخة الكتاب.",
          ],
          [
            "04",
            "إعداد الكتاب وفهارسه",
            "تُجمع المداخل المعتمدة مع التخريج والتعليل والفهارس، وتحمل كل نسخة تاريخًا وسجلًا للتعديلات.",
          ],
        ].map(([n, t, d]) => (
          <article key={n}>
            <span>{n}</span>
            <div>
              <h2>{t}</h2>
              <p>{d}</p>
            </div>
          </article>
        ))}
      </div>
      <div className="related-actions">
        <Link className="button button-dark" href="/corpus">
          تصفّح المجموعة المحلية ←
        </Link>
        <Link className="text-link" href="/methodology">
          طبقات المنهج
        </Link>
      </div>
    </>
  );
}
