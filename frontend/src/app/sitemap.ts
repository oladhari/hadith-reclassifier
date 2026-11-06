import bundles from "@/content/research-bundles.json";
import type { MetadataRoute } from "next";
import { cases } from "@/lib/research";
import { topics } from "@/lib/topics";
import { narrators,referenceBooks } from "@/lib/rijal";
import catalogue from "@/content/media-catalogue.json";
import videoVisibility from "@/content/video-visibility.json";
export default function sitemap():MetadataRoute.Sitemap{
 const hidden=new Set<number>(videoVisibility.hidden);
 const publicIds=new Set(Object.values(catalogue).filter(e=>e.visible&&e.id===e.canonical_id&&!hidden.has(e.id)).map(e=>e.id));
 const paths=["/","/about","/start","/topics","/library","/themes","/narrators","/corpus","/corpus/analysis","/methodology",...bundles.bundles.filter(b=>b.items.some(id=>publicIds.has(id))).map(b=>`/themes/${b.slug}`),...cases.map(c=>`/cases/${c.slug}`),...topics.map(t=>`/topics/${t.slug}`),...narrators.map(n=>`/narrators/${n.slug}`),...referenceBooks.map(b=>`/library/references/${b.id}`),...Object.values(catalogue).filter(e=>e.visible&&e.id===e.canonical_id&&!hidden.has(e.id)).map(e=>`/library/${e.id}`)];
 return [...new Set(paths)].map(path=>({url:`https://othmaniya.com${path}`}));
}
