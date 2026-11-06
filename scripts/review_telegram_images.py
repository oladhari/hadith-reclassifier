"""Create numbered private contact sheets for visual duplicate review."""
import json,sqlite3
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/research/imports/muawiya4n/visual-review'
DB=OUT.parent/'filter.sqlite3'

def main():
 OUT.mkdir(exist_ok=True,parents=True)
 c=sqlite3.connect(DB)
 inspections={k:(path,json.loads(payload)) for k,path,payload in c.execute('select id,path,payload from inspections')}
 rows=c.execute('select import_id,other_id,reason,metrics from candidates order by import_id,other_id').fetchall()
 manifest=[]
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
 for i,(a,b,reason,metrics) in enumerate(rows,1):
  manifest.append({'pair':i,'a':a,'b':b,'path_a':inspections[a][0],'path_b':inspections[b][0],'metrics':json.loads(metrics)})
 for start in range(0,len(manifest),16):
  subset=manifest[start:start+16];sheet=Image.new('RGB',(2000,2880),'#ddd');draw=ImageDraw.Draw(sheet)
  for j,row in enumerate(subset):
   x=(j%2)*1000;y=(j//2)*360
   draw.text((x+5,y+3),f"PAIR {row['pair']}   LEFT=A imported   RIGHT=B   d={row['metrics']['hash_distance']}",font=font,fill='black')
   for offset,label in [(0,'a'),(500,'b')]:
    with Image.open(row['path_'+label]) as im:
     im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((492,320))
     sheet.paste(im,(x+offset+(500-im.width)//2,y+32+(320-im.height)//2))
   draw.line((x+500,y+30,x+500,y+359),fill='red',width=2)
  sheet.save(OUT/f'sheet-{start//16+1:02}.jpg',quality=90)
 (OUT/'pairs.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print('pairs',len(manifest),'sheets',(len(manifest)+15)//16)
if __name__=='__main__':main()
