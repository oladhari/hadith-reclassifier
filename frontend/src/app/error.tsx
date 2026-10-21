"use client";

export default function ResearchError({ reset }: { reset: () => void }) {
  return <section className="empty-state" role="alert">
    <h1>تعذّر تحميل هذه الصفحة مؤقتًا</h1>
    <p>حاول مجددًا بعد قليل للوصول إلى النصوص والمصادر.</p>
    <button className="button button-dark" onClick={reset}>حاول مجددًا</button>
  </section>;
}
