#!/usr/bin/env python3
"""Build a curated directory from cached source pages; never infer grades from keywords."""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'data/research/rijal-sources/public-directory'
BOOKS={b['id']:b for b in json.loads((ROOT/'backend/app/research/rijal-library.json').read_text())['books']}
# Every category below is an editorial index of a specifically quoted statement,
# not an automated verdict. Favorable/countervailing statements are retained.
SPECS=[
('aban-ibn-taghlib','أبان بن تغلب',1692,5,2,[('الذهبي','شيعي جلد، لكنه صدوق، فلنا صدقه وعليه بدعته.','shii_jald','شيعي جلد'),('الذهبي','شيعي جلد، لكنه صدوق، فلنا صدقه وعليه بدعته.','reliability','صدوق'),('ابن عدي، بنقل الذهبي','وقال: كان غاليا في التشيع.','ghulu','غال في التشيع')]),
('ibrahim-ibn-al-hakam','إبراهيم بن الحكم بن ظهير',1692,27,73,[('الذهبي','شيعي جلد.','shii_jald','شيعي جلد'),('أبو حاتم، بنقل الذهبي','قال أبو حاتم: كذاب.','liar','كذاب'),('الدارقطني، بنقل الذهبي','وقال الدارقطني: ضعيف.','weak','ضعيف')]),
('kathir-al-nawwa','كثير بن إسماعيل النواء',1692,1753,6930,[('الذهبي','شيعي جلد.','shii_jald','شيعي جلد'),('أبو حاتم والنسائي، بنقل الذهبي','ضعفه أبو حاتم، والنسائي.','weak','ضعفه أبو حاتم والنسائي'),('ابن عدي، بنقل الذهبي','وقال ابن عدي: مفرط في التشيع.','ghulu','مفرط في التشيع')]),
('zubayd-al-yami','زبيد بن الحارث اليامي',1692,733,2829,[('الذهبي','من ثقات التابعين، فيه تشيع يسير.','mild','فيه تشيع يسير'),('الذهبي','من ثقات التابعين، فيه تشيع يسير.','reliability','من ثقات التابعين'),('القطان، بنقل الذهبي','قال القطان: ثبت.','reliability','ثبت')]),
('jafar-ibn-ziyad','جعفر بن زياد الأحمر',8609,66,940,[('ابن حجر','صدوق يتشيع','tashayyu','يتشيع'),('ابن حجر','صدوق يتشيع','reliability','صدوق')]),
('jafar-ibn-sulayman','جعفر بن سليمان الضبعي',8609,66,942,[('ابن حجر','صدوق زاهد لكنه كان يتشيع','tashayyu','كان يتشيع'),('ابن حجر','صدوق زاهد لكنه كان يتشيع','reliability','صدوق زاهد')]),
('muhammad-al-fitri','محمد بن موسى الفطري',1692,2080,8227,[('أبو حاتم، بنقل الذهبي','قال أبو حاتم: صدوق يتشيع.','tashayyu','يتشيع'),('أبو حاتم، بنقل الذهبي','قال أبو حاتم: صدوق يتشيع.','reliability','صدوق'),('الترمذي، بنقل الذهبي','وقال الترمذي: ثقة.','reliability','ثقة')]),
('ali-ibn-hashim','علي بن هاشم بن البريد',1692,1511,5960,[('أبو داود، بنقل الذهبي','وقال أبو داود: ثبت يتشيع.','tashayyu','يتشيع'),('أبو داود، بنقل الذهبي','وقال أبو داود: ثبت يتشيع.','reliability','ثبت'),('ابن حبان، بنقل الذهبي','وقال ابن حبان: غال في التشيع.','ghulu','غال في التشيع'),('أبو زرعة، بنقل الذهبي','قال أبو زرعة: صدوق.','reliability','صدوق'),('النسائي، بنقل الذهبي','وقال النسائي: ليس به بأس.','reliability','ليس به بأس')]),
('abdallah-ibn-isa','عبد الله بن عيسى بن عبد الرحمن بن أبي ليلى',1692,1137,4495,[('ابن معين، بنقل الذهبي','قال ابن معين: ثقة، يتشيع.','tashayyu','يتشيع'),('ابن معين، بنقل الذهبي','قال ابن معين: ثقة، يتشيع.','reliability','ثقة'),('النسائي، بنقل الذهبي','وقال النسائي: ثقة ثبت.','reliability','ثقة ثبت'),('أبو حاتم، بنقل الذهبي','وقال أبو حاتم: صالح.','reliability','صالح'),('ابن المديني، بنقل الذهبي','وقال ابن المديني: هو عندي منكر.','weak','هو عندي منكر')]),
('muhammad-al-ubaydali','محمد بن محمد بن علي العبيدلي',1692,2060,8142,[('الذهبي','رافضي جلد.','rafidi_jald','رافضي جلد'),('ابن خيرون، بنقل الذهبي','ضعفه ابن خيرون.','weak','ضعفه ابن خيرون')]),
('muhammad-ibn-abi-al-dhikr','محمد بن جعفر بن أبي الذكر المصري',1692,1852,7317,[('الذهبي','رافضي جلد','rafidi_jald','رافضي جلد')]),
('amr-ibn-khalid','عمرو بن خالد القرشي الواسطي',1692,1608,6359,[('الدارقطني، بنقل الذهبي','وقال الدارقطني: كذاب.','liar','كذاب'),('النسائي، بنقل الذهبي','وقال النسائي: روى عن حبيب بن أبي ثابت، كوفي ليس بثقة.','weak','ليس بثقة')]),
('sayf-ibn-muhammad','سيف بن محمد الكوفي',1692,923,3639,[('أحمد بن حنبل، من رواية ابنه بنقل الذهبي','روى عبد الله بن أحمد عن أبيه: كذاب.','liar','كذاب'),('أبو حاتم، بنقل الذهبي','وقال أبو حاتم: لا يكتب حديثه.','abandoned','لا يكتب حديثه')]),
('muhammad-ibn-wadan','محمد بن علي بن ودعان',1692,2008,7983,[('أبو طاهر السلفي، بنقل الذهبي','هالك متهم بالكذب.','accused','متهم بالكذب')]),
('sahl-ibn-ali','سهل بن علي',1692,907,3588,[('أبو مزاحم الخاقاني، بنقل الذهبي','متهم بالكذب، قاله أبو مزاحم الخاقاني.','accused','متهم بالكذب')]),
('ahmad-ibn-salama','أحمد بن سلمة المدائني',1692,101,395,[('الذهبي','متهم بالكذب.','accused','متهم بالكذب')]),
('abd-al-rahman-ibn-yazid','عبد الرحمن بن يزيد بن تميم الدمشقي',1692,1265,5006,[('النسائي، بنقل الذهبي','وقال النسائي: متروك الحديث، شامي.','abandoned','متروك الحديث'),('أبو زرعة، بنقل الذهبي','وقال أبو زرعة: ضعيف.','weak','ضعيف')]),
('abd-al-rahman-ibn-hatim','عبد الرحمن بن حاتم المرادي القفطي',1692,1221,4839,[('ابن الجوزي، بنقل الذهبي','قال ابن الجوزي: متروك الحديث.','abandoned','متروك الحديث'),('الذهبي، معقباً','قلت: هذا من شيوخ الطبراني، ما علمت به بأسا.','counterassessment','ما علمت به بأسا')]),
('jafar-ibn-al-zubayr','جعفر بن الزبير',8609,66,939,[('ابن حجر','متروك الحديث وكان صالحا في نفسه','abandoned','متروك الحديث؛ وكان صالحاً في نفسه')]),
('muhammad-ibn-musa-al-sadi','محمد بن موسى السعدي',1692,2080,8229,[('الذهبي','مجهول.','unknown','مجهول'),('ابن عدي، بنقل الذهبي','وقال ابن عدي: منكر الحديث','weak','منكر الحديث')]),
]


def build():
    sources={}
    P.mkdir(parents=True,exist_ok=True)
    for path in P.glob('*.json'):
        if path.name=='directory-audit.json':continue
        d=json.loads(path.read_text())
        for s in d.get('evidence',{}).get('sources',[]):
            key=(s['book_id'],s['page_id'])
            if len(s.get('text',''))>len(sources.get(key,{}).get('text','')):sources[key]=s
    # Pilot page already retrieved in the earlier research stage.
    previous_path=P.parent/'shamela-scoped-evidence.json'
    if previous_path.exists():
        previous=json.loads(previous_path.read_text())['result']['structuredContent']
        for page in previous['evidence']['sources']:sources.setdefault((page['book_id'],page['page_id']),page)
    P.mkdir(parents=True,exist_ok=True)
    entries=[]
    for slug,name,book_id,page_id,number,statements in SPECS:
        if book_id not in BOOKS:raise ValueError('Unknown reference book')
        if (book_id,page_id) not in sources:
            from research_rijal import call
            page=call('shamela_open',{'book_id':book_id,'page_id':page_id,'max_chars':16000})
            if page.get('book_id')!=book_id or page.get('page_id')!=page_id:raise ValueError('Wrong source page')
            sources[(book_id,page_id)]=page
            (P/f'page-{book_id}-{page_id}.json').write_text(json.dumps({'evidence':{'sources':[page]}},ensure_ascii=False,indent=2))
        page=sources[(book_id,page_id)];text=page['text']
        headings=list(re.finditer(r'(?m)^(?:\[[^\n]*?\]\s*)?([٠-٩0-9]+)\s*[-ـ]',text))
        selected=next((i for i,h in enumerate(headings) if int(h[1])==number),None)
        if selected is None:raise ValueError(f'Biography heading missing: {slug}, {number}')
        start=headings[selected].start();end=headings[selected+1].start() if selected+1<len(headings) else len(text)
        context=text[start:end].strip();findings=[]
        for critic,quote,category,label in statements:
            if quote not in context:raise ValueError(f'Quote outside biography: {slug}: {quote}')
            findings.append({'critic':critic,'quote':quote,'category':category,'label':label})
        citation=page['citation']['markdown'];location=re.search(r'\(([^()]*)\)\]',citation)[1]
        location=location.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩','0123456789'))
        entries.append({'slug':slug,'name':name,'aliases':[],'categories':list(dict.fromkeys(f['category'] for f in findings)),
            'evidence':[{'book_id':book_id,'page_id':page_id,'entry_number':number,'locator':location,
            'url':f'https://shamela.ws/book/{book_id}/{page_id}','source_text_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'context':context,'findings':findings,'verification':'electronic_text_checked','scan_compared':False}],
            'scholarly_verdict':None,'hadith_route_identity_linked':False})
    entries.sort(key=lambda row:row['name'])
    output={'version':1,'scope':'initial_cited_directory_not_exhaustive','entries':entries}
    target=ROOT/'frontend/src/content/narrator-directory.json';target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    audit={'entries':len(entries),'cited_findings':sum(len(e['evidence'][0]['findings']) for e in entries),'source_quotes':'all verbatim inside numbered biography','final_verdicts':0}
    (P/'directory-audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit))


if __name__=='__main__':build()
