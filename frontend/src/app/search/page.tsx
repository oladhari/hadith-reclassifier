import { redirect } from "next/navigation";
export default async function LegacySearch({searchParams}:{searchParams:Promise<Record<string,string|string[]|undefined>>}) {
 const input=await searchParams;const params=new URLSearchParams();
 for(const key of ["q","collection","id","status","page"])if(typeof input[key]==="string")params.set(key,input[key]);
 if(!params.has("q")&&typeof input.search==="string")params.set("q",input.search);
 redirect(`/corpus${params.size?`?${params}`:""}`);
}
