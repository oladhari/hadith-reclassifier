import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const base=process.env.RESEARCH_TEST_URL||'http://127.0.0.1:3015';const origin='https://othmaniya.com';
const ua='facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)';
async function get(path,headers={}){return fetch(base+path,{headers,signal:AbortSignal.timeout(60000)});}
const decode=s=>s.replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#x27;/g,"'");
let pages=0;
for(const path of ['/','/library','/narrators','/corpus','/topics','/themes']){
 const r=await get(path,{'User-Agent':ua});assert.equal(r.status,200,path);const text=await r.text();const head=text.split('</head>')[0];
 const meta=(name)=>{const tag=[...head.matchAll(/<meta\s+[^>]*>/g)].map(m=>m[0]).find(tag=>tag.includes(`property="${name}"`)||tag.includes(`name="${name}"`));return decode(tag?.match(/content="([^"]*)"/)?.[1]||'');};
 assert.ok(meta('description').length>40);assert.ok(meta('og:title'));assert.equal(meta('og:description'),meta('description'));assert.equal(meta('og:locale'),'ar_AR');assert.equal(new URL(meta('og:url')).href,new URL(origin+path).href);assert.equal(meta('og:image'),origin+'/social/othmaniya-share.png');assert.equal(meta('og:image:width'),'1200');assert.equal(meta('og:image:height'),'630');assert.equal(meta('twitter:card'),'summary_large_image');
 const canonical=head.match(/rel="canonical" href="([^"]+)"/)?.[1];assert.equal(new URL(canonical).href,new URL(origin+path).href);assert.ok(head.includes('<title>'));assert.ok(!meta('robots').includes('noindex'));
 if(path==='/')assert.equal((head.match(/<title>/g)||[]).length,1);
 pages++;
}
const filtered=await(await get('/library?section=books&theme=creed',{'User-Agent':ua})).text();assert.ok(filtered.includes('rel="canonical" href="https://othmaniya.com/library"'));
const image=await get('/social/othmaniya-share.png',{'User-Agent':ua});assert.equal(image.status,200);assert.match(image.headers.get('content-type'),/image\/png/);const bytes=Buffer.from(await image.arrayBuffer());assert.equal(bytes.readUInt32BE(16),1200);assert.equal(bytes.readUInt32BE(20),630);
const robots=await get('/robots.txt');assert.equal(robots.status,200);const rules=await robots.text();assert.ok(rules.includes('Allow: /'));assert.ok(rules.includes('Disallow: /api/'));assert.ok(rules.includes(origin+'/sitemap.xml'));
const sitemap=await get('/sitemap.xml');assert.equal(sitemap.status,200);assert.match(sitemap.headers.get('content-type'),/xml/);const xml=await sitemap.text();const urls=[...xml.matchAll(/<loc>(.*?)<\/loc>/g)].map(m=>decode(m[1]));assert.ok(urls.length>1400);assert.equal(new Set(urls).size,urls.length);for(const url of urls){assert.equal(new URL(url).origin,origin);assert.ok(!url.includes('?'));}
const hidden=JSON.parse(await readFile(new URL('../src/content/video-visibility.json',import.meta.url),'utf8')).hidden;for(const id of hidden)assert.ok(!urls.includes(`${origin}/library/${id}`));
console.log(JSON.stringify({facebook_bot_metadata_pages:pages,share_image:'1200x630 PNG verified',canonical_urls:'passed',robots:'passed',sitemap_urls:urls.length,hidden_videos:'excluded'}));
