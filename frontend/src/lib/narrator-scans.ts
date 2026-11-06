import "server-only";
import { createHash } from "node:crypto";
import type { Finding } from "@/lib/rijal";
import data from "@/content/narrator-scan-locations.json";
import { referenceFile } from "@/lib/reference-assets";
import type { ScanRectangle } from "@/components/highlighted-scan";
export type NarratorScan={book_id:number;file_id:string;pdf_page:number;printed_locator:string;image:string;width:number;height:number;sha256:string;quote_sha256:string;rectangles:ScanRectangle[];source_url:string};
export function narratorScans(slug:string,source:string,index:number,finding:Finding){
 const scans=(data as Record<string,NarratorScan[]>)[`${slug}/${source}/${index}`]||[];
 return scans.filter(scan=>{const file=referenceFile(String(scan.book_id),scan.file_id);return scan.quote_sha256===createHash("sha256").update(`${finding.critic}\n${finding.quote}`).digest("hex")&&file&&file.sha256===scan.sha256&&scan.pdf_page>=1&&scan.pdf_page<=file.pages;});
}
