"use client";
/* eslint-disable @next/next/no-img-element -- Original page rendering with proportional annotation overlays. */
import { useEffect,useRef,useState } from "react";
export type ScanRectangle={x:number;y:number;width:number;height:number};
export function HighlightedScan({src,width,height,rectangles,alt}:{src:string;width:number;height:number;rectangles:ScanRectangle[];alt:string}){
 const [highlight,setHighlight]=useState(true);
 const viewport=useRef<HTMLDivElement>(null);const page=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  const frame=viewport.current,image=page.current;if(!frame||!image)return;
  const center=()=>{frame.scrollTop=Math.max(0,image.clientHeight*(rectangles[0]?.y||0)/100-frame.clientHeight*.35);};
  center();const observer=new ResizeObserver(center);observer.observe(image);return()=>observer.disconnect();
 },[rectangles]);
 return <><div className="scan-controls"><button type="button" className="button button-outline" aria-pressed={highlight} onClick={()=>setHighlight(!highlight)}>{highlight?"أخفِ التظليل لفحص الأصل":"أظهر موضع الاقتباس"}</button><a className="text-link" href={src} target="_blank" rel="noopener noreferrer">افتح الصورة بالحجم الكامل ↗</a></div>
 <p className="small muted">يمكنك تمرير الصورة لرؤية بقية الصفحة، أو فتحها بالحجم الكامل.</p><div ref={viewport} className="quoted-scan-viewport" tabIndex={0} role="region" aria-label="صورة الصفحة عند موضع الاقتباس"><div ref={page} className="quoted-scan" style={{aspectRatio:`${width} / ${height}`}}><img src={src} width={width} height={height} alt={alt}/>{highlight&&rectangles.map((r,i)=><span key={i} className="scan-quote-highlight" aria-hidden="true" style={{left:`${r.x}%`,top:`${r.y}%`,width:`${r.width}%`,height:`${r.height}%`}}/>)}</div></div></>;
}
