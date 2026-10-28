"use client";
/* eslint-disable @next/next/no-img-element -- Existing CDN thumbnails in a private review list. */
import { useState } from "react";
import type { VideoReviewItem } from "@/lib/video-review";
import thumbnails from "@/content/thumbnails.json";
const decisions = { pending: "لم يُراجع", keep: "إبقاء", hide: "إخفاء" };
const platforms = { unknown: "غير محدد", tiktok: "TikTok", youtube: "YouTube", other: "مصدر آخر" };
function normalized(value: string) { return value.replace(/[ً-ٰٟـ]/g, "").replace(/[أإآٱ]/g, "ا").replace(/ى/g, "ي").toLowerCase(); }
function duration(seconds: number) { return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`; }
function ReviewPlayer({ item, busy, save }: { item: VideoReviewItem; busy: boolean; save: (item: VideoReviewItem, decision: VideoReviewItem["decision"], platform: VideoReviewItem["platform"], note: string) => void }) {
  const [platform, setPlatform] = useState(item.platform);
  const [note, setNote] = useState(item.note);
  const [failed, setFailed] = useState(false);
  return <div className="review-player" data-review-video={item.id}>
    <h2>{item.title}</h2><p className="muted">#{item.id} • {duration(item.duration)} • {new Date(item.date).toLocaleDateString("ar", { timeZone: "Asia/Tokyo" })} • {item.visible ? "ظاهر في الموقع" : "مخفي من الموقع"} • {decisions[item.decision]}</p>
    <video key={item.id} controls playsInline preload="metadata" src={`/api/media/${item.id}`} poster={(thumbnails as Record<string, string>)[item.id]} onError={() => setFailed(true)}>
      <track kind="captions" src={`/transcripts/${item.id}.vtt`} srcLang="ar" label="العربية — تفريغ آلي" />
    </video>
    {failed && <p role="alert">تعذّر التشغيل هنا. جرّب <a href={`/api/media/${item.id}`} target="_blank" rel="noreferrer">فتح الفيديو مباشرة</a>.</p>}
    <p>{item.description}</p>
    <label>مصدر الفيديو<select value={platform} onChange={e => setPlatform(e.target.value as VideoReviewItem["platform"])} disabled={busy}>
      {Object.entries(platforms).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
    </select></label>
    <p className="muted">المصدر غير محدد في بيانات الأرشيف. يمكنك تعيينه من العلامة الظاهرة أو معرفتك بالفيديو.</p>
    <label>ملاحظة خاصة (اختياري)<textarea value={note} maxLength={1000} onChange={e => setNote(e.target.value)} disabled={busy} rows={2} /></label>
    <div className="review-decisions">
      <button className="button button-dark" disabled={busy} onClick={() => save(item, "keep", platform, note)}>إبقاء في الموقع</button>
      <button className="button review-hide" disabled={busy} onClick={() => save(item, "hide", platform, note)}>إخفاء من الموقع</button>
      <button className="button button-outline" disabled={busy} onClick={() => save(item, item.decision, platform, note)}>حفظ المصدر والملاحظة</button>
      {item.decision !== "pending" && <button className="text-link" disabled={busy} onClick={() => save(item, "pending", platform, note)}>إعادة إلى غير المراجَع</button>}
    </div>
  </div>;
}
export function VideoReview({ initialItems }: { initialItems: VideoReviewItem[] }) {
  const [items, setItems] = useState(initialItems);
  const [playerReset, setPlayerReset] = useState(0);
  const [status, setStatus] = useState("pending"), [platform, setPlatform] = useState("all"), [query, setQuery] = useState("");
  const [activeId, setActiveId] = useState<number | null>(null), [advance, setAdvance] = useState(true);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState(""), [error, setError] = useState("");
  const [undo, setUndo] = useState<{ previous: VideoReviewItem; revision: number } | null>(null);
  const filtered = items.filter(item => (status === "all" || item.decision === status) && (platform === "all" || item.platform === platform) &&
    normalized(`${item.id} ${item.title} ${item.description} ${item.note}`).includes(normalized(query)));
  const active = items.find(item => item.id === activeId) || filtered[0];
  async function persist(item: VideoReviewItem, decision: VideoReviewItem["decision"], source: VideoReviewItem["platform"], note: string, isUndo = false) {
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch("/api/video-review/decision", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: item.id, revision: item.revision, decision, platform: source, note }) });
      if (response.status === 401) throw new Error("انتهت جلسة الدخول. أعد تحميل الصفحة وسجّل الدخول لحفظ القرار.");
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "تعذّر حفظ القرار.");
      setItems(rows => rows.map(row => row.id === item.id ? { ...row, ...result, duration: Number(result.duration), size: Number(result.size) } : row));
      setUndo(isUndo ? null : { previous: item, revision: result.revision });
      if (isUndo) setPlayerReset(value => value + 1);
      setMessage(isUndo ? "تم التراجع عن آخر تغيير." : `تم الحفظ: ${decisions[decision]} — ${item.title}`);
      if (!isUndo && advance && decision !== item.decision) {
        const position = filtered.findIndex(row => row.id === item.id);
        setActiveId(filtered[position + 1]?.id || null);
      } else setActiveId(item.id);
    } catch (err) { setError(err instanceof Error ? err.message : "تعذّر الحفظ. حاول مجددًا."); }
    finally { setBusy(false); }
  }
  function filterChange(setter: (value: string) => void, value: string) { setter(value); setActiveId(null); }
  const position = active ? filtered.findIndex(item => item.id === active.id) : -1;
  return <div className="video-review">
    <div className="review-counts"><span>المجموع: {items.length}</span>{Object.entries(decisions).map(([key, label]) => <span key={key}>{label}: {items.filter(item => item.decision === key).length}</span>)}</div>
    <div className="review-filters">
      <label>حالة المراجعة<select value={status} onChange={e => filterChange(setStatus, e.target.value)} disabled={busy}><option value="all">الجميع</option>{Object.entries(decisions).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      <label>المصدر<select value={platform} onChange={e => filterChange(setPlatform, e.target.value)} disabled={busy}><option value="all">جميع المصادر</option>{Object.entries(platforms).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      <label>بحث<input value={query} onChange={e => filterChange(setQuery, e.target.value)} placeholder="العنوان أو الرقم أو الملاحظة" disabled={busy} /></label>
      <label className="review-auto"><input type="checkbox" checked={advance} onChange={e => setAdvance(e.target.checked)} /> الانتقال تلقائيًا بعد القرار</label>
    </div>
    <div className="review-feedback" aria-live="polite"><p>{busy ? "جارٍ الحفظ…" : message}</p>{error && <p role="alert">{error}</p>}
      {undo && <button className="button button-outline" disabled={busy} onClick={() => persist({ ...undo.previous, revision: undo.revision }, undo.previous.decision, undo.previous.platform, undo.previous.note, true)}>تراجع عن آخر تغيير</button>}
    </div>
    <div className="review-workspace"><div>
      <div className="review-navigation"><button className="button button-outline" disabled={busy || position <= 0} onClick={() => setActiveId(filtered[position - 1].id)}>السابق</button>
        <span>{filtered.length} فيديو مطابق</span><button className="button button-outline" disabled={busy || position < 0 || position >= filtered.length - 1} onClick={() => setActiveId(filtered[position + 1].id)}>تجاوز / التالي</button></div>
      {active ? <ReviewPlayer key={`${active.id}-${playerReset}`} item={active} busy={busy} save={persist} /> : <p className="empty-state">لا توجد فيديوهات مطابقة. غيّر الفلتر لعرض القرارات المحفوظة.</p>}
    </div><nav className="review-queue" aria-label="قائمة الفيديوهات">
      {filtered.map(item => <button key={item.id} className={active?.id === item.id ? "selected" : ""} disabled={busy} onClick={() => setActiveId(item.id)} aria-current={active?.id === item.id ? "true" : undefined}>
        <img loading="lazy" src={(thumbnails as Record<string, string>)[item.id]} alt="" /><span><strong>{item.title}</strong><small>#{item.id} • {duration(item.duration)} • {decisions[item.decision]} • {platforms[item.platform]}</small></span>
      </button>)}
    </nav></div>
  </div>;
}
