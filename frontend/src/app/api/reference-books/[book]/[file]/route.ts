import { NextRequest } from "next/server";
import { referenceFile } from "@/lib/reference-assets";
export const runtime="nodejs";
export async function GET(request:NextRequest,{params}:{params:Promise<{book:string;file:string}>}){
 const {book,file}=await params;
 if(!/^[1-9]\d{0,5}$/.test(book)||!/^part-\d{2}$/.test(file))return new Response("Not found",{status:404});
 const asset=referenceFile(book,file);if(!asset)return new Response("Not found",{status:404});
 if(!/^reference-books\/rijal\/(?:[a-z0-9-]+\/)*sha256\/[a-f0-9]{64}\.pdf$/.test(asset.key)||!asset.key.endsWith(`/${asset.sha256}.pdf`))return new Response("Not found",{status:404});
 const range=request.headers.get("range");
 if(range){
  const match=/^bytes=(\d*)-(\d*)$/.exec(range);
  let valid=Boolean(match&&(match[1]||match[2]));
  if(match&&valid){
   const first=match[1]?Number(match[1]):null,last=match[2]?Number(match[2]):null;
   valid=(first===null||Number.isSafeInteger(first))&&(last===null||Number.isSafeInteger(last));
   const start=first??Math.max(0,asset.bytes-(last??0));const end=first!==null&&last!==null?Math.min(last,asset.bytes-1):asset.bytes-1;
   valid=valid&&start<=end&&start<asset.bytes;
  }
  if(!valid)return new Response(null,{status:416,headers:{"Content-Range":`bytes */${asset.bytes}`,"Cache-Control":"private, no-store"}});
 }
 const base=process.env.MEDIA_PUBLIC_BASE_URL?.replace(/\/$/,"");
 if(!base)return new Response("الملف غير متاح مؤقتاً",{status:503});
 let target:URL;try{target=new URL(`${base}/${asset.key}`);if(target.protocol!=="https:")throw new Error("Invalid storage URL");}catch{return new Response("الملف غير متاح مؤقتاً",{status:503});}
 return new Response(null,{status:307,headers:{Location:target.href,"Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"}});
}
