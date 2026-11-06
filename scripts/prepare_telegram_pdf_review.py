"""Render the imported PDFs locally for private page-layout and readability review."""
import concurrent.futures,json,sqlite3,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/research/imports/muawiya4n/visual-review/pdf'

def render(row):
 key,path,payload,n=row;folder=OUT/f'doc-{n:02}';folder.mkdir(parents=True,exist_ok=True)
 pages=json.loads(payload)['pages']
 if len(list(folder.glob('page-*.jpg')))!=pages:
  subprocess.run(['pdftoppm','-jpeg','-scale-to','1100','-jpegopt','quality=90',path,str(folder/'page')],capture_output=True,check=True,timeout=120)
 files=sorted(folder.glob('page-*.jpg'),key=lambda p:int(p.stem.split('-')[-1]))
 assert len(files)==pages
 return {'document':n,'id':key,'original_path':path,'pages':[str(p) for p in files]}

def sheet(rows,path,columns=2,cell=(800,450)):
 width,height=cell;canvas=Image.new('RGB',(columns*width,((len(rows)+columns-1)//columns)*height),'#ddd');d=ImageDraw.Draw(canvas)
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
 for i,(label,file) in enumerate(rows):
  x=(i%columns)*width;y=(i//columns)*height;im=Image.open(file).convert('RGB');im.thumbnail((width-8,height-32));canvas.paste(im,(x+(width-im.width)//2,y+30));d.text((x+5,y+3),label,fill='black',font=font)
 canvas.save(path,quality=92)

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(OUT.parent.parent/'filter.sqlite3')
 rows=[(*r,i) for i,r in enumerate(c.execute("select id,path,payload from inspections where id like 'new:%' and json_extract(payload,'$.mime')='application/pdf' order by id"),1)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:docs=list(pool.map(render,rows))
 (OUT/'manifest.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2))
 pages=[(f"DOC {doc['document']} PAGE {n}",p) for doc in docs for n,p in enumerate(doc['pages'],1)]
 for start in range(0,len(pages),16):sheet(pages[start:start+16],OUT/f'pages-{start//16+1:02}.jpg')
 for start in range(0,len(docs),6):sheet([(f"DOC {doc['document']} FIRST PAGE / {len(doc['pages'])} pages",doc['pages'][0]) for doc in docs[start:start+6]],OUT/f'first-{start//6+1}.jpg',2,(900,1000))
 print('documents',len(docs),'pages',len(pages))
if __name__=='__main__':main()
