"use client";

/* eslint-disable @next/next/no-img-element -- Preserve the original scan and the rendered PDF page. */
import { useId, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { ArrowUpLeft, ChevronDown } from "lucide-react";
import type { EvidenceHighlight } from "@/lib/case-studies";

export function CaseEvidencePreview({
  title,
  original,
  pdfPageImage,
  highlights = [],
  children,
}: {
  title: string;
  original: string;
  pdfPageImage?: string;
  highlights?: EvidenceHighlight[];
  children: ReactNode;
}) {
  const panelId = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const viewport = useRef<HTMLDivElement>(null);
  const firstHighlight = useRef<HTMLSpanElement>(null);
  const [preview, setPreview] = useState<"image" | "pdf" | null>(null);
  const [inlinePdf, setInlinePdf] = useState(false);
  const hasHighlights = highlights.length > 0;
  const leftEdge = Math.min(100, ...highlights.map(({ left }) => left));
  const rightEdge = Math.max(0, ...highlights.map(({ left, width }) => left + width));
  const pageWidth = Math.max(100, Math.min(150, 9200 / (rightEdge - leftEdge)));

  function togglePreview() {
    if (preview) {
      setPreview(null);
      return;
    }
    const supportsPdf = Boolean(pdfPageImage && navigator.pdfViewerEnabled
      && !window.matchMedia("(pointer: coarse)").matches);
    setInlinePdf(supportsPdf);
    setPreview(supportsPdf && !hasHighlights ? "pdf" : "image");
  }

  function showHighlight() {
    if (!viewport.current || !firstHighlight.current) return;
    // Scroll the preview itself so the reader keeps their place in the case.
    const view = viewport.current;
    view.scrollTop = firstHighlight.current.offsetTop - view.clientHeight / 4;
    view.scrollLeft = view.scrollWidth * (leftEdge + rightEdge) / 200 - view.clientWidth / 2;
  }

  return (
    <>
      <div className="case-preview-actions">
        <button ref={trigger} type="button" className="case-preview-toggle"
          aria-expanded={preview !== null} aria-controls={panelId} onClick={togglePreview}>
          <ChevronDown size={18} aria-hidden="true" />
          {preview ? "إغلاق المعاينة" : "عرض الدليل هنا"}
        </button>
        <a className="text-link" href={original} target="_blank" rel="noopener noreferrer">
          فتح الأصل في تبويب جديد <ArrowUpLeft size={16} aria-hidden="true" />
        </a>
      </div>
      <div id={panelId} className="case-preview-panel" hidden={!preview}>
        {preview && hasHighlights && (
          <div className="case-preview-toolbar">
            <span>{preview === "image" ? "موضع الشاهد مظلّل" : "ملف PDF الأصلي"}</span>
            {inlinePdf && <button type="button" className="text-link" onClick={() => {
              setPreview(preview === "image" ? "pdf" : "image");
            }}>{preview === "image" ? "تصفّح ملف PDF هنا" : "العودة إلى الشاهد المظلّل"}</button>}
          </div>
        )}
        {preview === "pdf" && <iframe src={original} title={title} />}
        {preview === "image" && (
          <div className={hasHighlights ? "case-highlight-viewport" : undefined} ref={viewport}
            tabIndex={hasHighlights ? 0 : undefined} role={hasHighlights ? "region" : undefined}
            aria-label={hasHighlights ? `صفحة الشاهد: ${title}` : undefined}>
            <div className="case-highlight-page" style={{ "--case-page-width": `${pageWidth}%` } as CSSProperties}>
              <img src={pdfPageImage || original} alt={title} onLoad={showHighlight} />
              {highlights.map(({ left, top, width, height }, index) => (
                <span key={index} ref={index === 0 ? firstHighlight : undefined}
                  className="case-highlight" aria-hidden="true"
                  style={{ left: `${left}%`, top: `${top}%`, width: `${width}%`, height: `${height}%` }} />
              ))}
            </div>
          </div>
        )}
        {children}
        <button type="button" className="case-preview-toggle" onClick={() => {
          setPreview(null);
          trigger.current?.focus();
        }}>إغلاق المعاينة</button>
      </div>
    </>
  );
}
