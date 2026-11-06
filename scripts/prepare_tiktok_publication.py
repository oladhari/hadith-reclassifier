"""Publish verified, deduplicated TikTok assets into saved public read models.

No database writes or paid model calls. Original captions remain attributed to the
source account. Manual duplicate decisions live separately in the review folder.
"""
import argparse
from collections import Counter
import concurrent.futures
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / 'frontend/src/content'
IMPORT = Path('/mnt/linuxdata/othmani-tiktok/brad2557wtn')


def clean(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text).replace('#', ' ').replace('_', ' ')).strip()


def norm(text):
    return re.sub('[\u064b-\u065f\u0670ـ]', '', text).translate(str.maketrans('أإآى', 'اااي'))


# Descriptive headings, not endorsements of the claims in the source captions.
SUBJECTS = [
 ('حديث عمار', 'حديث عمار والفئة الباغية', 'siffin'), ('الفئة الباغية', 'حديث عمار والفئة الباغية', 'siffin'),
 ('حديث سفينة', 'حديث سفينة ومدة الخلافة', 'allegiance'), ('سعيد بن جمهان', 'حديث سفينة وسعيد بن جمهان', 'narrators'),
 ('رضاع الكبير', 'روايات رضاع الكبير', 'narrators'), ('ارضاع الكبير', 'روايات رضاع الكبير', 'narrators'),
 ('حديث الكساء', 'حديث الكساء وأهل البيت', 'virtues'), ('اهل البيت', 'أهل البيت في الروايات والتفسير', 'virtues'),
 ('قصة الحرة', 'أخبار وقعة الحرة', 'karbala'), ('واقعة الحرة', 'أخبار وقعة الحرة', 'karbala'),
 ('وقعة الحرة', 'أخبار وقعة الحرة', 'karbala'), ('غدير', 'حديث الغدير ورواياته', 'virtues'),
 ('مقتل عثمان', 'مقتل عثمان بن عفان ورواياته', 'uthman'), 
 ('حكيم بن حبلة', 'حكيم بن جبلة وأخبار الفتنة', 'narrators'), ('محمد بن ابي بكر', 'محمد بن أبي بكر وأحداث الفتنة', 'uthman'),
 ('صفين', 'صفين والتحكيم', 'siffin'), ('الجمل', 'وقعة الجمل ورواياتها', 'camel'),
 ('كربلاء', 'كربلاء ومقتل الحسين', 'karbala'), ('الحسين', 'أخبار الحسين بن علي', 'karbala'),
 ('رواة البخاري', 'رواة صحيح البخاري وأقوال النقاد', 'narrators'),
 ('صحيح البخاري', 'قراءة في روايات صحيح البخاري', 'narrators'),
 ('تدوين السنة', 'تاريخ تدوين السنة', 'manuscripts'), ('تدوين', 'تدوين الروايات وتاريخها', 'manuscripts'),
 ('الرواة', 'الرواة ونقد الأخبار', 'narrators'), ('الجرح', 'الجرح والتعديل ونقد الروايات', 'narrators'),
 ('الاعمش', 'الأعمش وأقوال نقاد الرجال', 'narrators'), ('ابو مخنف', 'أبو مخنف وروايات الأخبار', 'narrators'),
 ('ابن القيم', 'قراءة في أقوال ابن القيم', 'narrators'), ('الامام الذهبي', 'قراءة في أقوال الذهبي', 'narrators'),
 ('ابن تيمية', 'قراءة في أقوال ابن تيمية', 'narrators'),
 ('الحجاج', 'الحجاج بن يوسف الثقفي وأخباره', 'siffin'),
 ('يزيد', 'يزيد بن معاوية وروايات تاريخه', 'karbala'), ('معاوية', 'معاوية بن أبي سفيان وأخبار الشام', 'siffin'),
 ('عثمان بن عفان', 'عثمان بن عفان وأحداث الفتنة', 'uthman'),
 ('بيعة', 'البيعة والخلافة بعد عثمان', 'allegiance'), ('خليفة', 'الخلافة بعد عثمان ورواياتها', 'allegiance'),
 ('الخلافة', 'الخلافة وروايات التاريخ', 'allegiance'), ('عائشة', 'أخبار عائشة أم المؤمنين', 'camel'),
 ('ام المؤمنين', 'روايات أم المؤمنين ومناقشتها', 'camel'), ('فاطمة', 'أخبار فاطمة في المصادر', 'virtues'),
]
PEOPLE = [
 ('شعيب', 'شعيب العثماني'), ('طارق', 'طارق المغربي الأموي'), ('وليد', 'وليد الأموي'),
 ('غصون', 'غصون'), ('غضون', 'غصون'), ('بحري', 'الشيخ بحري'), ('منير الطويل', 'منير الطويل'),
 ('عناد', 'عناد العثماني'), ('الياس المصري', 'إلياس المصري'), ('هيثم', 'هيثم'),
 ('قتادة', 'قتادة العثماني'), ('القائد خطاب', 'القائد خطاب'), ('القاءد خطاب', 'القائد خطاب'),
 ('الدكتور مصطفى', 'الدكتور مصطفى'), ('فواز الشمري', 'فواز الشمري'),
 ('سيف ابو معاوية', 'سيف أبو معاوية'), ('رامي عيسى', 'رامي عيسى'),
]


def heading(caption):
    n = norm(clean(caption))
    topics = []
    subject = ''
    for term, label, slug in SUBJECTS:
        if norm(term) in n:
            if not subject:
                subject = label
            if slug not in topics:
                topics.append(slug)
    person = next((label for term, label in PEOPLE if norm(term) in n), '')
    if subject:
        title = f'{subject} — {person}' if person else subject
    elif person:
        title = f'حوار من أرشيف {person}'
    elif 'مناظرة' in n or 'نقاش' in n or 'محاور' in n:
        title = 'حوار في الروايات والتاريخ الإسلامي'
    elif 'العباسي' in n:
        title = 'نقاش في المنهج العثماني وقراءة التاريخ'
    else:
        title = 'مقطع من أرشيف الصحبة العثمانية'
    return title, topics


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((IMPORT / 'manifest.json').read_text())['videos']
    if len(manifest) != 1253 or any(v['state'] != 'verified' for v in manifest.values()):
        raise ValueError('Archive is incomplete')
    decisions = json.loads((IMPORT / 'review/duplicate-decisions.json').read_text())
    aliases = decisions['aliases']
    db = sqlite3.connect(f'file:{ROOT}/data/research/research.sqlite3?mode=ro', uri=True)
    known = {}
    for sha, id in db.execute('select o.sha256,m.legacy_id from research_objects o join research_media m on m.object_id=o.id'):
        if id is not None:
            known.setdefault(sha, []).append(id)
    hidden = set(json.loads((CONTENT / 'video-visibility.json').read_text())['hidden'])
    # Numeric IDs are stable, independent of thread completion order or retries.
    ids = {id: 2_000_000 + i for i, id in enumerate(sorted(manifest), 1)}
    catalogue = json.loads((CONTENT / 'media-catalogue.json').read_text())
    archive = json.loads((CONTENT / 'archive-index.json').read_text())
    objects = json.loads((CONTENT / 'media-objects.json').read_text())
    thumbnails = json.loads((CONTENT / 'thumbnails.json').read_text())
    for numeric in ids.values():
        catalogue.pop(str(numeric), None)
        objects.pop(str(numeric), None)
        thumbnails.pop(str(numeric), None)
    patches = {}
    for source, target in decisions.get('old_aliases', {}).items():
        catalogue[source]['canonical_id'] = target
        patches[source] = {'canonical_id': target}
        catalogue[str(target)]['occurrences'] = sorted(set(catalogue[str(target)]['occurrences'] + catalogue[source]['occurrences']))
    groups = {}
    for id in manifest:
        groups.setdefault(aliases.get('tt:' + id, 'tt:' + id), []).append(id)
    sources = {key: [dict(url=manifest[id]['source_url'], caption=manifest[id]['caption'].strip()) for id in group] for key, group in groups.items()}
    counts = Counter(); added = []; new = {}; work = []
    overrides = json.loads((CONTENT / 'tiktok-title-overrides.json').read_text())
    titlecounts = Counter(overrides.get(id) or heading(v['caption'])[0] for id, v in manifest.items())
    datecounts = Counter((overrides.get(id) or heading(v['caption'])[0], datetime.fromtimestamp(v['timestamp'], timezone.utc).strftime('%Y-%m-%d')) for id, v in manifest.items())
    seq = Counter()
    for id, v in sorted(manifest.items(), key=lambda kv: int(kv[0]), reverse=True):
        numeric = ids[id]; kind = v.get('kind', 'video'); sha = v['sha256']; targets = known.get(sha, [])
        if id in decisions.get('suppressed', []) or any(x in hidden for x in targets):
            counts['previously_hidden'] += 1
            continue
        existing = next((catalogue[str(x)]['canonical_id'] for x in targets if str(x) in catalogue and catalogue[str(x)]['visible']), None)
        alias = aliases.get('tt:' + id)
        target = existing or (int(alias[4:]) if alias and alias.startswith('old:') else ids[alias[3:]] if alias else numeric)
        if target in hidden:
            counts['previously_hidden'] += 1
            continue
        sourceposts = sources.get('tt:' + id, [dict(url=v['source_url'], caption=v['caption'].strip())])
        primary = max(sourceposts, key=lambda post: len(clean(post['caption'])))
        title, topics = heading(primary['caption'])
        title = overrides.get(id) or title
        date = datetime.fromtimestamp(v['timestamp'], timezone.utc).strftime('%Y-%m-%d')
        if titlecounts[title] > 1:
            base = title
            title += f' — {date}'
            if datecounts[(base, date)] > 1:
                seq[(base, date)] += 1
                title += f' ({seq[(base, date)]})'
        caption = primary['caption']
        description = 'بحسب وصف الناشر: «' + clean(caption)[:230] + ('…' if len(clean(caption)) > 230 else '') + '».' if clean(caption) else 'مقطع محفوظ من حساب الصحبة العثمانية؛ لم يرفق الناشر وصفًا نصيًا لهذا المنشور.'
        key = v['object_key'].removeprefix('othmani/')
        if not re.fullmatch(r'imports/tiktok/brad2557wtn/objects/[a-f0-9]{64}\.(mp4|webm|mov|m4a|mp3|ogg)|(?:originals/sha256/[a-f0-9]{2}|imports/muawiya4n/originals/sha256)/[a-f0-9]{64}', key):
            raise ValueError('Unexpected object key')
        row = dict(id=numeric, canonical_id=target, title=title, description=description,
            work_title='', author='', page_label='', scope='audio' if kind == 'audio' else 'clip',
            topics=topics, cases=[], tags=['TikTok', 'brad2557wtn', 'الصحبة العثمانية', clean(caption)],
            visible=True, duration=v['duration'], has_transcript=False, chapters=[], occurrences=[numeric],
            source_url=primary['url'], source_caption=caption, source_account='brad2557wtn', source_posts=sourceposts)
        if target != numeric:
            counts['duplicate_listings_merged'] += 1
        else:
            counts[kind] += 1
        if kind == 'video':
            work.append((numeric, v))
        new[str(numeric)] = row
        added.append(dict(id=numeric, date=datetime.fromtimestamp(v['timestamp'], timezone.utc).isoformat(), kind=kind,
            mime='audio/mp4' if kind == 'audio' else 'video/webm' if key.endswith('.webm') else 'video/mp4',
            path=f'tiktok/brad2557wtn/{id}{Path(key).suffix}', size=v['size'], name=title, object_key=key))
        objects[str(numeric)] = key
    for key, sourceposts in sources.items():
        if not key.startswith('old:'):
            continue
        targetid = key[4:]
        target = catalogue[targetid]
        primary = max(sourceposts, key=lambda post: len(clean(post['caption'])))
        target.update(source_url=primary['url'], source_caption=primary['caption'], source_account='brad2557wtn', source_posts=sourceposts)
        target['tags'] = list(dict.fromkeys(target['tags'] + ['TikTok', 'brad2557wtn', 'الصحبة العثمانية'] + [clean(post['caption']) for post in sourceposts]))
        preferred = decisions.get('preferred', {}).get(targetid)
        if preferred and preferred.startswith('tt:'):
            target['preferred_media_id'] = ids[preferred[3:]]
            target['asset_size'] = manifest[preferred[3:]]['size']
            target['duration'] = manifest[preferred[3:]]['duration']
    for id, row in new.items():
        if row['canonical_id'] != row['id']:
            target = new.get(str(row['canonical_id'])) or catalogue[str(row['canonical_id'])]
            target['occurrences'] = sorted(set(target['occurrences'] + row['occurrences']))
            row.update(title=target['title'], description=target['description'], visible=target['visible'])
    for source, target in decisions.get('old_aliases', {}).items():
        catalogue[source].update(title=catalogue[str(target)]['title'], description=catalogue[str(target)]['description'])
    for key in sources:
        if key.startswith('old:'):
            row = catalogue[key[4:]]
            patches[key[4:]] = {field: row[field] for field in ['source_url', 'source_caption', 'source_account', 'source_posts', 'tags', 'occurrences', 'preferred_media_id', 'asset_size', 'duration'] if field in row}
    targets = {row['canonical_id'] for row in new.values()}
    report = dict(discovered=len(manifest), **counts)
    report.update(new_video=counts['video'], video=counts['video'] + sum(id < 2_000_000 for id in targets),
        visible_records=len(new), upgraded_existing=sum(id < 2_000_000 for id in targets),
        existing_duplicates_merged=len(decisions.get('old_aliases', {})))
    save(IMPORT / 'review/publication-report.json', report)
    save(IMPORT / 'review/title-preview.json', {id: {k: v[k] for k in ['title', 'source_caption', 'canonical_id']} for id, v in new.items()})
    print(json.dumps(report), flush=True)
    if not args.apply:
        return
    def thumbnail(job):
        numeric, v = job; relative = f'/thumbnails/tiktok-{v["sha256"]}.webp'; out = ROOT / 'frontend/public' / relative.lstrip('/')
        if not out.exists():
            subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-ss', str(min(v['duration'] * .1, 8)), '-i', v['local_path'],
                '-frames:v', '1', '-vf', 'scale=480:480:force_original_aspect_ratio=decrease', '-quality', '76', '-threads', '1', str(out)], check=True, timeout=90)
        return str(numeric), relative
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        thumbnails.update(dict(pool.map(thumbnail, work)))
    for id in decisions.get('suppressed', []):
        path = ROOT / 'frontend/public/thumbnails' / f'tiktok-{manifest[id]["sha256"]}.webp'
        path.unlink(missing_ok=True)  # Generated preview only; originals remain untouched.
    catalogue.update(new)
    archive = [a for a in archive if a['id'] not in set(ids.values())]
    save(CONTENT / 'archive-index.json', added + archive)
    save(CONTENT / 'media-catalogue.json', catalogue)
    save(CONTENT / 'media-objects.json', objects)
    save(CONTENT / 'thumbnails.json', thumbnails)
    save(CONTENT / 'tiktok-collection.json', report)
    save(CONTENT / 'tiktok-catalogue-overlay.json', patches)


if __name__ == '__main__':
    main()
