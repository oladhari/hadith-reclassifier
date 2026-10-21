"""Read-only thematic index of Telegram post text/captions, not hadith authentication.

Matches are nonexclusive lexical leads. Duplicate counts use normalized full text.
Images, PDF contents and video/audio speech are not analyzed by this script.
"""
import argparse, hashlib, json, re, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def normalize(s):
    return re.sub(r'\s+',' ',re.sub('[\u064b-\u065f\u0670\u0640]','',s).translate(str.maketrans({'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ي'}))).strip()
SPECS=[
 ('uthman','حصار عثمان ومقتله',['قتل عثمان','قتلة عثمان','مقتل عثمان','حصار عثمان','حصار بيت','حصر عثمان','قتلوا عثمان','الخروج على عثمان'],[]),
 ('camel','الجمل وموقف عائشة وطلحة والزبير',['الجمل','طلحة','الزبير','عائشة','الحوأب'],[]),
 ('allegiance','بيعة علي وصلته بالمشاركين في قتل عثمان',['بيعة علي','خلافة علي','بايعوا علي','بايع علي','أنصار علي','قتلة عثمان','محمد بن أبي بكر','مالك الأشتر'],['علي']),
 ('siffin','صفين والتحكيم وموقف أهل الشام',['صفين','التحكيم','الحكمين','عمرو بن العاص','أهل الشام'],[]),
 ('virtues','روايات الفضائل والإمامة',['الغدير','غدير خم','من كنت مولاه','الكساء','كتاب الله وعترتي','الثقلين','لا يحبني','لا يحبك','باب خيبر','حديث المنزلة','سيدا شباب أهل الجنة','أقضانا علي'],[]),
 ('narrators','الرواة وقواعد نقد الروايات',['المبتدع','بدعته','التدليس','مدلس','وكيع','الأعمش','عدي بن ثابت','الجوزجاني','رواة الكوفة'],[]),
 ('karbala','كربلاء ومقتل الحسين',['كربلاء','مقتل الحسين','قتل الحسين','الحسين بن علي','يزيد بن معاوية'],[]),
 ('manuscripts','اختلاف الألفاظ والنسخ',['اليونينية','اليونيني','نسخ البخاري','تحريف صحيح','إدراج','تقتله الفئة الباغية','وأقضانا علي'],[]),
]
CASES=[
 ('uthman-siege',['قتل عثمان','قتلة عثمان','مقتل عثمان','حصار عثمان','حصار بيت','حصر عثمان'],[]),
 ('uthman-shirt',['يا عثمان إن الله','يلبسك قميصا','البسك قميصا','فلا تخلعه','لا تخلعه'],['عثمان']),
 ('camel',['الجمل','قتال الناكثين','الناكثين والقاسطين'],[]),
 ('hawab',['حديث الحوأب','كلاب الحوأب','تنبحها كلاب','تنبحه كلاب'],[]),
 ('allegiance',['بيعة علي','خلافة علي','بايعوا علي','بايع علي'],[]),
 ('ali-and-killers',['قتلة عثمان','محمد بن أبي بكر','مالك الأشتر','سودان بن حمران'],['علي']),
 ('siffin',['صفين','التحكيم','الحكمين'],[]),
 ('ammar',['تقتله الفئة الباغية','تقتلك الفئة الباغية','الفئه الباغيه','عمار تقتله'],[]),
 ('ghadir',['الغدير','غدير خم','من كنت مولاه'],[]),
 ('kisa',['الكساء','حديث المرط'],[]),
 ('thaqalayn',['الثقلين','كتاب الله وعترتي'],[]),
 ('love-and-faith',['لا يحبني','لا يحبك','لا يحبه إلا مؤمن'],[]),
 ('innovation',['رواية المبتدع','روايه المبتدع','يقوي بدعته','يقوي به بدعته'],[]),
 ('kufan',['رواة الكوفة','أحاديث الكوفة','أهل الكوفة','المدرسة المدنية','أهل الحجاز','أصل بالحجاز'],[]),
 ('adult-nursing',['رضاع الكبير','رضاعة الكبير','إرضاع الكبير','الإرضاع الكبير'],[]),
 ('manuscripts',['اليونيني','اليونينية','نسخ البخاري','وأقضانا علي','تحريف صحيح البخاري'],[]),
 ('karbala',['كربلاء','مقتل الحسين','قتل الحسين'],[]),
]
def collect(rows,terms,required):
    result=[];hashes=set()
    for mid,text in rows:
        n=normalize(text)
        hit=[t for t in terms if normalize(t) in n]
        if hit and all(normalize(t) in n for t in required):
            key=hashlib.sha256(n.encode()).hexdigest();hashes.add(key)
            result.append({'id':mid,'matchedTerms':hit,'normalizedTextHash':key})
    return {'postCount':len(result),'distinctTextCount':len(hashes),'posts':result}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,default=ROOT.parent/'telegram-archive/kkee9938/archive.sqlite3');args=parser.parse_args()
    c=sqlite3.connect(f'file:{args.archive.resolve()}?mode=ro',uri=True)
    rows=c.execute("SELECT id,text FROM messages WHERE text IS NOT NULL AND trim(text)!='' ORDER BY id").fetchall()
    report={'schemaVersion':1,'scope':'telegram_text_and_captions_only','totalPosts':c.execute('SELECT COUNT(*) FROM messages').fetchone()[0],'textPosts':len(rows),'latestMessageId':c.execute('SELECT MAX(id) FROM messages').fetchone()[0],'method':'Nonexclusive normalized substring matching with normalized exact-text deduplication. Counts are research leads, not scholarly findings. No OCR or speech transcription.','topics':[{ 'slug':slug,'title':title,'terms':terms,'requiredTerms':required,**collect(rows,terms,required)} for slug,title,terms,required in SPECS],'cases':{slug:{'terms':terms,'requiredTerms':required,**collect(rows,terms,required)} for slug,terms,required in CASES}}
    out=ROOT/'frontend/src/content/archive-themes.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'posts':report['totalPosts'],'textPosts':len(rows),'topics':[{k:t[k] for k in ['slug','title','postCount','distinctTextCount']} for t in report['topics']],'cases':{k:{'count':v['postCount'],'firstIds':[p['id'] for p in v['posts'][:8]]} for k,v in report['cases'].items()}},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
