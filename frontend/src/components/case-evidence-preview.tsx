"use client";

/* eslint-disable @next/next/no-img-element -- Preserve the original scan and the rendered PDF page. */
import { useId, useRef, useState, type ReactNode } from "react";
import { ArrowUpLeft, ChevronDown } from "lucide-react";

export function CaseEvidencePreview({
  title,
  original,
  pdfPageImage,
  children,
}: {
  title: string;
  original: string;
  pdfPageImage?: string;
  children: ReactNode;
}) {
  const panelId = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const [preview, setPreview] = useState<"image" | "pdf" | null>(null);

  function togglePreview() {
    if (preview) {
      setPreview(null);
      return;
    }
    const inlinePdf = pdfPageImage && navigator.pdfViewerEnabled
      && !window.matchMedia("(pointer: coarse)").matches;
    setPreview(inlinePdf ? "pdf" : "image");
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
        {preview === "pdf" && <iframe src={original} title={title} />}
        {preview === "image" && <img src={pdfPageImage || original} alt={title} />}
        {children}
        <button type="button" className="case-preview-toggle" onClick={() => {
          setPreview(null);
          trigger.current?.focus();
        }}>إغلاق المعاينة</button>
      </div>
    </>
  );
}
