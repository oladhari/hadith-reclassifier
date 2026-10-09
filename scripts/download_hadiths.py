#!/usr/bin/env python3
"""
Download all hadith collections from fawazahmed0/hadith-api once.
Saves to data/hadiths/{lang}-{collection}.json
Run once: python scripts/download_hadiths.py
"""
import asyncio
import json
import os
from pathlib import Path

import httpx

CDN = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
FALLBACK = "https://rawcdn.githack.com/fawazahmed0/hadith-api/1/editions"

COLLECTIONS = ["bukhari", "muslim", "malik", "abudawud", "tirmidhi", "nasai", "ibnmajah"]
DATA_DIR = Path(__file__).parent.parent / "data" / "hadiths"


async def download(client: httpx.AsyncClient, url: str, dest: Path):
    if dest.exists():
        print(f"  [skip] {dest.name} already exists")
        return
    try:
        print(f"  Downloading {dest.name} ...", end=" ", flush=True)
        resp = await client.get(url, timeout=120.0)
        resp.raise_for_status()
    except Exception:
        url = url.replace(CDN, FALLBACK)
        resp = await client.get(url, timeout=120.0)
        resp.raise_for_status()
    dest.write_bytes(resp.content)
    size_kb = dest.stat().st_size // 1024
    print(f"{size_kb} KB")


async def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []
        for col in COLLECTIONS:
            for lang in ("ara", "eng"):
                url = f"{CDN}/{lang}-{col}.json"
                dest = DATA_DIR / f"{lang}-{col}.json"
                tasks.append(download(client, url, dest))
        await asyncio.gather(*tasks)

    print("\nAll done. Files saved to data/hadiths/")
    total = sum(f.stat().st_size for f in DATA_DIR.glob("*.json"))
    print(f"Total size: {total / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    asyncio.run(main())
