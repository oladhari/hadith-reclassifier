#!/usr/bin/env python3
"""Render the website's Arabic Open Graph card using its existing type palette."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
im=Image.new('RGB',(1200,630),'#f7f5f0');d=ImageDraw.Draw(im)
navy='#172a46';gold='#b58b60';muted='#616b79'
d.rounded_rectangle((35,35,1165,595),radius=22,fill='#fffdf9',outline='#e0dfda',width=2)
d.rectangle((35,35,1165,44),fill=gold)
# The same open-book symbol used in the website header.
d.rounded_rectangle((80,85,185,190),radius=22,fill=navy)
d.line([(133,117),(133,165)],fill='#f7f5f0',width=4)
d.line([(133,122),(108,115),(100,118),(100,160),(108,158),(133,165),(158,158),(166,160),(166,118),(158,115),(133,122)],fill='#f7f5f0',width=4)
def font(size,bold=False):return ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoKufiArabic-'+('Bold' if bold else 'Regular')+'.ttf',size)
def rtl(text,y,size,color=navy,bold=False):
 f=font(size,bold);d.text((1105,y),text,font=f,fill=color,anchor='ra',direction='rtl',language='ar')
rtl('موسوعة الرد على العباسيين',100,47,bold=True)
rtl('المصدر أولًا، والحُجّة في سياقها',210,30,color=gold)
d.line((95,310,1105,310),fill='#e0dfda',width=2)
rtl('ابحث في الأحاديث واقرأ المصادر المصوّرة',350,29)
rtl('تتبّع أقوال النقّاد وشواهد الروايات',420,29)
d.text((95,540),'othmaniya.com',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',27),fill=muted)
im.save(ROOT/'frontend/public/social/othmaniya-share.png',optimize=True)
