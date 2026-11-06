import "server-only";
import data from "@/content/reference-book-assets.json";
export type ReferenceFile={id:string;part:number;label:string;key:string;sha256:string;bytes:number;pages:number;source_url:string;original_name:string;source_archive:string};
export type ReferenceEdition={format:string;complete_source_set:boolean;scanned_edition:string;volume_count:number;file_count:number;pages:number;files:ReferenceFile[];edition_note:string};
export const referenceEditions=data as Record<string,ReferenceEdition>;
export function referenceEdition(id:string){return Object.hasOwn(referenceEditions,id)?referenceEditions[id]:null;}
export function referenceFile(id:string,file:string){return referenceEdition(id)?.files.find(f=>f.id===file)||null;}
export function referenceFileHref(id:string|number,file:string){return `/api/reference-books/${id}/${file}`;}
