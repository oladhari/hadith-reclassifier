import type { Metadata } from "next";
export const siteName="موسوعة الرد على العباسيين";
export const siteDescription="مكتبة بحثية وفق المنهج العثماني: ابحث في الأحاديث، واقرأ المصادر المصوّرة، وتتبّع أقوال النقّاد وشواهد الروايات في سياقها.";
export const shareImage={url:"/social/othmaniya-share.png",width:1200,height:630,alt:"موسوعة الرد على العباسيين — المصدر أولًا والحُجّة في سياقها"};
export function pageMetadata(title:string,description:string,path:string):Metadata{
 return {title,description,alternates:{canonical:path},openGraph:{title,description,url:path,siteName,locale:"ar_AR",type:"website",images:[shareImage]},twitter:{card:"summary_large_image",title,description,images:[shareImage.url]}};
}
