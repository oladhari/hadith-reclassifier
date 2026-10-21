/* eslint-disable @next/next/no-img-element -- Original archival images are served without alteration. */
import Link from "next/link";
import {
  ArrowUpLeft,
  Search,
  Play,
  BookOpen,
  ArrowLeft,
  ScanText,
  Scale,
  Network,
} from "lucide-react";
import { cases } from "@/lib/research";
import { CaseCard, TopicCard } from "@/components/research-ui";
import { topics } from "@/lib/topics";
export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <div className="hero-kicker">
            <span /> مكتبة بحثية وفق المنهج العثماني
          </div>
          <h1>
            لكلّ حُجّةٍ أصل.
            <br />
            <span>ولكلّ روايةٍ ميزان.</span>
          </h1>
          <p>
            «سلمت منها أيدينا فلتسلم منها أفواهنا»؛ مبدأ نحترم به الصحابة. لكن هل التزم به من نسب البغي إلى عائشة وطلحة والزبير ومعاوية؟ هنا نفحص هذه الدعاوى، ونقرأ الروايات في مصادرها، ونتتبّع الأدلة لنتبيّن ما وقع ونصل إلى الحقيقة.
          </p>
          <form action="/explore" className="hero-search" role="search">
            <Search size={21} />
            <input
              name="q"
              aria-label="البحث في الموسوعة"
              placeholder="حديث، راوٍ، كتاب، أو سؤال يشغلك…"
              required
              maxLength={160}
            />
            <button type="submit">
              ابحث <ArrowLeft size={17} />
            </button>
          </form>
          <div className="popular-search">
            <span>تصفّح المحاور:</span>
            <Link href="/topics/uthman">حصار عثمان</Link>
            <Link href="/topics/camel">أهل الجمل</Link>
            <Link href="/topics/siffin">صفين والتحكيم</Link>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="art-ring ring-one" />
          <div className="art-ring ring-two" />
          <div className="art-star">✧</div>
          <div className="manuscript">
            <span>مِنَ السُّؤَالِ إِلَى الدَّلِيلِ</span>
            <div className="manuscript-word">الميزان</div>
            <div className="manuscript-rule" />
            <p>
              نصٌّ محفوظ
              <br />
              ومصدرٌ معلوم
              <br />
              وحُجّةٌ تُفحَص
            </p>
            <span className="manuscript-seal">۞</span>
          </div>
          <span className="art-caption">وضوحٌ في العرض · عنايةٌ بالأصل</span>
        </div>
      </section>
      <section className="section-block" id="archive-topics">
        <div className="section-heading">
          <div>
            <span className="eyebrow">محاور الموسوعة وملفاتها</span>
            <h2>القضايا التي يدور حولها النقاش</h2>
          </div>
          <Link className="text-link" href="/topics">
            جميع المحاور <ArrowUpLeft size={18} />
          </Link>
        </div>
        <p className="section-intro">
          تتبّع الحجج والمصادر في الوقائع والروايات محل النزاع. لكل محور ملفات
          تفصيلية وأدلة مصوّرة تقرؤها في مكانها.
        </p>
        <div className="topic-grid">
          {topics.slice(0, 6).map((topic) => (
            <TopicCard key={topic.slug} topic={topic} />
          ))}
        </div>

      </section>
      <section className="section-block">
        <div className="section-heading">
          <div>
            <span className="eyebrow">داخل هذه المحاور</span>
            <h2>تتبّع الرواية أو الحجة المحددة</h2>
          </div>
          <Link className="text-link" href="/cases">
            جميع الملفات <ArrowUpLeft size={18} />
          </Link>
        </div>
        <div className="case-grid">
          {[
            "uthman-shirt",
            "hawab",
            "ammar",
            "ghadir",
            "innovation",
            "adult-nursing",
          ]
            .map((slug) => cases.find((c) => c.slug === slug)!)
            .map((item) => (
              <CaseCard item={item} key={item.slug} />
            ))}
        </div>
      </section>
      <section className="evidence-feature">
        <div className="evidence-image">
          <div className="scan-label">
            <ScanText size={16} /> من صفحات الكتب
          </div>
          <img
            src="/evidence/195.jpg"
            alt="صفحة مصورة من نزهة النظر تتناول رواية المبتدع"
            loading="lazy"
          />
          <span className="scan-caption">
            صورة المصدر كما وردت • التمييز اللوني من الأصل
          </span>
        </div>
        <div className="evidence-copy">
          <span className="eyebrow">المصدر على بُعد نقرة</span>
          <h2>
            لا تكتفِ بالنقل.
            <br />
            <em>اقرأ الصفحة بنفسك.</em>
          </h2>
          <p>
            نربط كل حُجّة بأصلها: صورة الكتاب، وموضع النص، وبيانات المرجع، أو
            توقيت الكلام في المقطع.
          </p>
          <ul className="feature-list">
            <li>
              <ScanText size={18} /> الأصل المصوّر بجوار الاقتباس المحدد
            </li>
            <li>
              <Network size={18} /> روابط تجمع القضية بالرواية والمصدر
            </li>
            <li>
              <Scale size={18} /> فصل واضح بين النص والتفسير والحكم
            </li>
          </ul>
          <Link href="/cases/innovation" className="button button-dark">
            اقرأ النص في مصدره <ArrowUpLeft size={18} />
          </Link>
        </div>
      </section>
      <section className="section-block">
        <div className="section-heading">
          <div>
            <span className="eyebrow">ثلاث خطوات لقراءة واعية</span>
            <h2>كيف تستخدم الموسوعة؟</h2>
          </div>
          <Link href="/start" className="text-link">
            دليل البداية <ArrowUpLeft size={18} />
          </Link>
        </div>
        <div className="journey-grid">
          {[
            ["01", "ابدأ بالسؤال", "اختر قضية واقرأ موضع النزاع بلغة واضحة."],
            [
              "02",
              "افتح الدليل",
              "شاهد الأصل المصوّر أو افتح الرواية في مجموعتها.",
            ],
            [
              "03",
              "تتبّع وجه الاستدلال",
              "ميّز النص عن تفسيره، وراجع ما اكتمل وما بقي للبحث.",
            ],
          ].map(([n, t, d]) => (
            <div className="journey" key={n}>
              <span>{n}</span>
              <h3>{t}</h3>
              <p>{d}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="collection-banner">
        <div>
          <span className="eyebrow">مكتبة الحديث</span>
          <h2>من المكتبة إلى الكتاب العثماني</h2>
          <p>
            نصوص حديثية تُدرس في ضوء الأدلة وطبقات المنهج. اعتماد
            النتائج وترقيم الكتاب يأتيان بعد المراجعة.
          </p>
        </div>
        <Link href="/corpus" className="button button-light">
          <BookOpen size={18} /> تصفّح نصوص الأحاديث{" "}
          <ArrowUpLeft size={18} />
        </Link>
      </section>
      <div className="bottom-note">
        <Play size={16} />
        <span>
          شاهد المرئيات واقرأ الأدلة المصوّرة في مكتبة الموسوعة.
        </span>
        <Link href="/library?kind=video">افتح المرئيات ←</Link>
      </div>
    </>
  );
}
