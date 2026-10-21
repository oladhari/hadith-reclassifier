"""Seed research-case links, never hadith grades. Existing editorial edits are preserved."""

import json
import sqlite3
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.research.catalogue import normalize

c = sqlite3.connect(root / "data/research/research.sqlite3")
c.row_factory = sqlite3.Row
if c.execute(
    "select 1 from research_catalogue_settings where key='filter_case_studies'"
).fetchone():
    print("Existing case-study edits preserved.")
    sys.exit(0)
rows = c.execute(
    "select h.id,h.source_number,t.text,co.slug,co.title from research_hadiths h join research_collections co on co.id=h.collection_id join research_hadith_texts t on t.hadith_id=h.id and t.language='ar'"
).fetchall()


def candidates(kind):
    out = []
    for row in rows:
        t = normalize(row["text"])
        matched = (
            ("عمار" in t and ("الباغية" in t or ("الجنة" in t and "النار" in t)))
            if kind == "ammar"
            else (
                (("سهلة" in t or "سالم" in t) and ("ارضع" in t or "رضاع" in t))
                if kind == "nursing"
                else (("لا يحبني" in t or "لا يحبك" in t) and "منافق" in t)
                if kind == "love"
                else ("من كنت مولاه" in t or "من كنت وليه" in t)
            )
        )
        if matched:
            out.append(
                {
                    "hadith_id": row["id"],
                    "collection": row["slug"],
                    "collection_title": row["title"],
                    "number": row["source_number"],
                    "match_state": "text_candidate",
                }
            )
    return out


studies = [
    {
        "slug": "ammar-addition",
        "case_slug": "ammar",
        "title": "رواية عمار: الزيادة واختلاف النقل",
        "question": "أين ورد لفظ «تقتله الفئة الباغية»، وما صلته بالطريق والنسخة وعبارة الناقد؟",
        "layer_keys": [
            "text_identity",
            "variants",
            "attribution_conflict",
            "hidden_defects",
            "critical_disagreement",
        ],
        "source_media": [373, 379, 1881, 221],
        "checks": [
            "مقارنة لفظ أبي سعيد في مواضع البخاري مع الطرق الأخرى.",
            "مقابلة كلام فتح الباري وتحفة الأشراف بالأصل وتحديد المقصود بالإدراج.",
            "توثيق هوية المخطوط وتاريخه ومقارنة شهوده؛ صورة ورقة وحدها لا تثبت ترتيب جميع النسخ.",
        ],
        "corpus_candidates": candidates("ammar"),
        "source_posts": [100, 373, 379, 1881, 219],
        "evidence_status": "images_compared_bibliography_pending",
    },
    {
        "slug": "adult-nursing-quran",
        "case_slug": "adult-nursing",
        "title": "رضاع الكبير: المقارنة بالقرآن وآثار الرضاعة",
        "question": "ما الآية التي يُحتج بها وما وجه دلالتها على اللفظ المعين من الرواية؟",
        "layer_keys": ["quran_explicit", "matn", "early_practice", "corroboration"],
        "source_media": [2380, 2381],
        "checks": [
            "تثبيت النص القرآني والآية ووجه الاعتراض في سجل المقارنة.",
            "فصل أثر عمر وقول ابن عمر عن رواية سالم.",
            "عرض التفسير المقترح وحجته قبل تسجيل نتيجة المقارنة.",
        ],
        "corpus_candidates": candidates("nursing"),
        "source_posts": [2210, 2380],
        "evidence_status": "quran_argument_source_pending",
    },
    {
        "slug": "love-and-faith",
        "case_slug": "love-and-faith",
        "title": "رواية المحبة والإيمان: اللفظ والإسناد",
        "question": "كيف تُدرس دلالة الربط بالإيمان، وما الأدلة المحددة في رواة كل طريق؟",
        "layer_keys": [
            "quran_explicit",
            "tadlis",
            "innovation_support",
            "project_narrator_selection",
            "regional_corroboration",
            "matn",
        ],
        "source_media": [],
        "checks": [
            "اعتماد اللفظ الموجود في النص الحديثي؛ ولفظ «منافق» لا يستبدل بلفظ «كافر».",
            "تعيين الأعمش وعدي بن ثابت وغيرهما من الإسناد الفعلي وجمع أقوال النقاد.",
            "فصل الاعتراض على الدلالة عن إثبات البدعة وعن اتصال الطريق.",
        ],
        "corpus_candidates": candidates("love"),
        "source_posts": [1920, 1931, 2080],
        "evidence_status": "caption_claims_need_primary_citations",
    },
    {
        "slug": "kufan-ghadir",
        "case_slug": "kufan",
        "title": "الطرق الكوفية: خبر الغدير نموذجًا",
        "question": "أي طريق عُرض على الناقد، وما منشؤه وشواهده المستقلة؟",
        "layer_keys": [
            "regional_corroboration",
            "isolation",
            "corroboration",
            "hidden_defects",
            "project_narrator_selection",
        ],
        "source_media": [32, 344],
        "checks": [
            "فحص عبارة النقد ومدى انطباقها على الطريق المعروض.",
            "تمييز منشأ الرواية من مجرد نسبة بعض رواتها إلى بلد.",
            "تسجيل نطاق البحث عن الأصل المدني والطرق المستقلة.",
        ],
        "corpus_candidates": candidates("ghadir"),
        "source_posts": [32, 344, 2371, 2395, 2438],
        "evidence_status": "specific_route_scope_pending",
    },
    {
        "slug": "narrator-selection",
        "case_slug": "innovation",
        "title": "توصيف الراوي وأثره في الانتقاء",
        "question": "هل ثبت التوصيف في الراوي المعين وما أثره في هذا الطريق؟",
        "layer_keys": [
            "narrator_identity",
            "integrity",
            "innovation_support",
            "project_narrator_selection",
            "precision",
        ],
        "source_media": [195, 196],
        "checks": [
            "تسجيل لفظ الناقد والكتاب والصفحة دون الاكتفاء بوصف في تعليق.",
            "تمييز شرط الانتقاء الخاص بالمشروع من قاعدة ما يقوّي البدعة.",
            "تتبع الراوي في الطرق بعد تثبيت هويته، ثم دراسة كل طريق مستقل.",
        ],
        "corpus_candidates": [],
        "source_posts": [195, 1920, 1931],
        "evidence_status": "narrator_identities_and_judgments_pending",
    },
]
# Provenance is private. Study cards contain no raw posts or Telegram links.
public = []
for study in studies:
    public.append(
        {k: v for k, v in study.items() if k not in {"source_posts", "evidence_status"}}
    )
data = {
    "public": public,
    "provenance": {
        x["slug"]: {
            "source_posts": x["source_posts"],
            "evidence_status": x["evidence_status"],
        }
        for x in studies
    },
    "status": "research_cases_not_final_verdicts",
}
c.execute(
    "insert into research_catalogue_settings(key,value) values(?,?) on conflict(key) do update set value=excluded.value",
    ("filter_case_studies", json.dumps(data, ensure_ascii=False)),
)
c.commit()
for x in studies:
    print(x["slug"], len(x["corpus_candidates"]))
