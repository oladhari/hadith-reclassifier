import json
import asyncio
import httpx
from pathlib import Path

CDN_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
CDN_FALLBACK = "https://rawcdn.githack.com/fawazahmed0/hadith-api/1/editions"

_project_root = Path(__file__).parent.parent.parent.parent
LOCAL_DATA_DIR = (
    Path("/data/hadiths")          # inside Docker (mounted volume)
    if Path("/data/hadiths").exists()
    else _project_root / "data" / "hadiths"   # local development
)

EDITION_MAP = {
    "bukhari":  ("eng-bukhari",  "ara-bukhari"),
    "muslim":   ("eng-muslim",   "ara-muslim"),
    "malik":    ("eng-malik",    "ara-malik"),
    "abudawud": ("eng-abudawud", "ara-abudawud"),
    "tirmidhi": ("eng-tirmidhi", "ara-tirmidhi"),
    "nasai":    ("eng-nasai",    "ara-nasai"),
    "ibnmajah": ("eng-ibnmajah", "ara-ibnmajah"),
}


def _load_local(edition: str) -> dict:
    path = LOCAL_DATA_DIR / f"{edition}.json"
    if not path.exists():
        raise FileNotFoundError(f"Local file not found: {path}. Run scripts/download_hadiths.py first.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


async def _fetch_json(client: httpx.AsyncClient, url: str) -> dict:
    try:
        resp = await client.get(url, timeout=30.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        fallback = url.replace(CDN_BASE, CDN_FALLBACK)
        resp = await client.get(fallback, timeout=30.0)
        resp.raise_for_status()
        return resp.json()


def _extract_chain(arabic_text: str) -> str:
    if not arabic_text:
        return ""
    return arabic_text[:400]


def _normalize(h_eng: dict, ara_index: dict, collection: str) -> dict:
    num = h_eng["hadithnumber"]
    ara_text = ara_index.get(num, "")
    grades = h_eng.get("grades", [])
    return {
        "collection": collection,
        "book_number": h_eng.get("reference", {}).get("book"),
        "hadith_number": num,
        "urn": f"{collection}:{num}",
        "text_english": h_eng.get("text", ""),
        "text_arabic": ara_text,
        "narrator_chain_raw": _extract_chain(ara_text),
        "traditional_grade": grades[0].get("grade", "") if grades else "",
        "topics": None,
    }


class HadithClient:

    def load_all_from_local(self, collection: str) -> list[dict]:
        """Load entire collection from local JSON files (fast, no network)."""
        if collection not in EDITION_MAP:
            raise ValueError(f"'{collection}' not supported. Available: {list(EDITION_MAP.keys())}")
        eng_edition, ara_edition = EDITION_MAP[collection]
        eng_data = _load_local(eng_edition)
        ara_data = _load_local(ara_edition)
        ara_index = {h["hadithnumber"]: h["text"] for h in ara_data.get("hadiths", [])}
        return [_normalize(h, ara_index, collection) for h in eng_data.get("hadiths", []) if h.get("text")]

    async def get_hadith(self, collection: str, hadith_number: int) -> dict | None:
        """Fetch a single hadith — tries local first, falls back to CDN."""
        try:
            hadiths = self.load_all_from_local(collection)
            match = next((h for h in hadiths if h["hadith_number"] == hadith_number), None)
            return match
        except FileNotFoundError:
            pass
        if collection not in EDITION_MAP:
            return None
        eng_edition, ara_edition = EDITION_MAP[collection]
        async with httpx.AsyncClient() as client:
            eng_data, ara_data = await asyncio.gather(
                _fetch_json(client, f"{CDN_BASE}/{eng_edition}/{hadith_number}.json"),
                _fetch_json(client, f"{CDN_BASE}/{ara_edition}/{hadith_number}.json"),
            )
        eng_list = eng_data.get("hadiths", [])
        ara_list = ara_data.get("hadiths", [])
        if not eng_list:
            return None
        ara_index = {h["hadithnumber"]: h["text"] for h in ara_list}
        return _normalize(eng_list[0], ara_index, collection)


hadith_client = HadithClient()
fawazahmed_client = hadith_client
sunnah_client = hadith_client
