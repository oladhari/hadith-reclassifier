#!/usr/bin/env python3
"""Publish curated Arabic metadata and captions, preserving every original.

No scholarly assessments or accepted-book entries are created. Only the public
projection enters the website view. Private selection notes remain restricted.
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from enrich_media import CACHE, ROOT, inventory, save, config

TOPICS = {"uthman", "camel", "allegiance", "siffin", "virtues", "narrators", "karbala", "manuscripts"}
CASES = {row["slug"] for row in json.loads((ROOT / "frontend/src/content/editorial-seed.json").read_text())["cases"]}
MANUAL = ROOT / "data/research/enrichment/manual-overrides.json"


def timestamp(seconds):
    milliseconds = max(0, round(seconds * 1000))
    return f"{milliseconds // 3600000:02}:{milliseconds // 60000 % 60:02}:{milliseconds // 1000 % 60:02}.{milliseconds % 1000:03}"


def assemble():
    items = inventory()
    metadata, public, transcripts, missing = {}, {}, {}, []
    overrides = json.loads(MANUAL.read_text()) if MANUAL.exists() else {}
    for item in items:
        path = CACHE / "verified" / (item["sha"] + ".json")
        if not path.exists():
            missing.append(item["id"])
            continue
        row = json.loads(path.read_text())
        matching_overrides = [overrides[str(id)] for id in item["ids"] if str(id) in overrides]
        if matching_overrides:
            row.update(overrides.get(str(item["id"]), matching_overrides[0]))
            row["topics"] = list(dict.fromkeys(topic for override in matching_overrides for topic in override.get("topics", [])))
            row["cases"] = list(dict.fromkeys(slug for override in matching_overrides for slug in override.get("cases", [])))
        row["topics"] = list(dict.fromkeys(topic for topic in row["topics"] if topic in TOPICS))[:3]
        row["cases"] = list(dict.fromkeys(slug for slug in row["cases"] if slug in CASES))
        row["title"] = re.sub(r"\s+", " ", row["title"]).strip()
        row["description"] = re.sub(r"\s+", " ", row["description"]).strip()
        # Display public names/tags in Arabic, without exposing account handles.
        for before, after in {"AmoyToon": "أموي تون", "MBC": "إم بي سي"}.items():
            row["title"] = row["title"].replace(before, after)
            row["description"] = row["description"].replace(before, after)
            row["tags"] = [tag.replace(before, after) for tag in row["tags"]]
        row["tags"] = list(dict.fromkeys(tag for tag in row["tags"] if re.search("[\u0600-\u06ff]", tag)))
        # File names marked WIP must never become assertions of completed books.
        if any("wip" in name.lower() for name in item["names"]):
            row["scope"] = "article"
            row["title"] = re.sub(r"\b(?:شاملة كاملة|كاملة|كامل|مكتمل|مكتملة)\b", "", row["title"]).strip()
            row["description"] = re.sub(r"\b(?:مكتمل|مكتملة|كامل|كاملة)\b", "", row["description"])
        visible = row["role"] in {"supports", "framework"} and row["confidence"] >= .72 and bool(row["topics"])
        if "visible" in row:
            visible = row["visible"]
        elif item["kind"] == "image" and re.search("كاريكات|أموي تون|رسم ساخر", row["title"] + " " + row["description"]):
            visible = False
            row["selection_reason"] += " استُبعد الرسم الساخر من كتالوج المصادر البحثية مع الاحتفاظ بالأصل."
        data = {key: row[key] for key in ["title", "description", "work_title", "author", "page_label", "scope", "topics", "cases", "tags"]}
        data.update(id=item["id"], canonical_id=item["id"], visible=visible,
                    occurrences=item["ids"], chapters=[])
        if item["kind"] in {"pdf", "document"}:
            document = json.loads((CACHE / "documents" / (item["sha"] + ".json")).read_text())
            data["page_count"] = document["pages"]
            if data["scope"] == "page":
                data["scope"] = "excerpt"
            if data["scope"] == "full_book" and document["pages"] < 20:
                data["scope"] = "article"
        elif item["kind"] == "image":
            data["scope"] = "page"
        elif item["kind"] == "audio":
            data["scope"] = "audio"
        if item["kind"] in {"video", "audio"}:
            transcript = json.loads((CACHE / "transcripts" / (item["sha"] + ".json")).read_text())
            data["duration"] = transcript["duration"]
            segments = [dict(segment) for segment in transcript["segments"]]
            # Only literal, bounded orthographic replacements; raw transcription stays intact.
            for fix in row.get("transcript_fixes", []):
                before, after = fix["from"], fix["to"]
                if not before or before == after or len(before) > 80 or len(after) > 100:
                    continue
                if before not in transcript["text"]:
                    continue
                for segment in segments:
                    segment["text"] = segment["text"].replace(before, after)
            # Use several segments per paragraph, keeping all spoken content searchable.
            data["transcript"] = "\n".join(" ".join(part["text"] for part in segments[n:n+6]) for n in range(0, len(segments), 6))
            data["has_transcript"] = bool(data["transcript"])
            chapters = sorted(row["chapters"], key=lambda chapter: chapter["start"])
            for chapter in chapters:
                if chapter["topic"] not in TOPICS or not 0 <= chapter["start"] < chapter["end"] <= transcript["duration"] + 1 or chapter["end"] - chapter["start"] < 45:
                    continue
                if data["chapters"] and chapter["start"] < data["chapters"][-1]["end"] - .1:
                    continue
                chapter["end"] = min(chapter["end"], transcript["duration"])
                data["chapters"].append(chapter)
            transcripts[item["id"]] = {"raw": transcript, "segments": segments, "visible": visible}
        metadata[str(item["id"])] = row
        for occurrence in item["ids"]:
            # Retain duplicate ID resolution without making repeated cards.
            public[str(occurrence)] = {**data, "id": occurrence} if visible else {
                "id": occurrence, "canonical_id": item["id"], "visible": False,
                "title": "", "description": "", "work_title": "", "author": "", "page_label": "",
                "scope": row["scope"], "topics": [], "cases": [], "tags": [], "chapters": [], "occurrences": item["ids"],
            }
    if missing:
        raise ValueError(f"Crosscheck incomplete for {len(missing)} unique files; first IDs: {missing[:15]}")
    registry = ROOT / "frontend/src/content/media-collections.json"
    collections = json.loads(registry.read_text()) if registry.exists() else {}
    claimed = set()
    for collection in collections.values():
        canonical = collection["canonical_id"]
        members = collection["members"]
        if canonical not in members or claimed.intersection(members):
            raise ValueError("Invalid or overlapping editorial collection")
        claimed.update(members)
        asset = (ROOT / "frontend/public" / collection["asset_url"].lstrip("/")).resolve()
        if not asset.is_relative_to((ROOT / "frontend/public/collections").resolve()):
            raise ValueError("Collection asset outside public collections directory")
        if asset.stat().st_size != collection["asset_size"] or hashlib.sha256(asset.read_bytes()).hexdigest() != collection["asset_sha256"]:
            raise ValueError("Collection PDF checksum mismatch")
        if len(collection["page_map"]) != collection["page_count"]:
            raise ValueError("Collection page provenance incomplete")
        base = dict(public[str(canonical)])
        if not base["visible"] or any(not public[str(member)]["visible"] for member in members):
            raise ValueError("Only already selected sources can enter a public collection")
        occurrences = sorted({id for member in members for id in public[str(member)]["occurrences"]})
        base.update(canonical_id=canonical, title=collection["title"], description=collection["description"],
            page_count=collection["page_count"], asset_url=collection["asset_url"], asset_size=collection["asset_size"],
            scope="excerpt", work_title="", author="", page_label="", occurrences=occurrences,
            collection_sources=[{"id": row["id"], "page_count": row["page_count"]} for row in collection["originals"]],
            collection_page_map=[{key: row[key] for key in ["page", "source_id", "source_page"]} for row in collection["page_map"]])
        for id in occurrences:
            public[str(id)] = {**base, "id": id}
    return items, metadata, public, transcripts


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync-cloud", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    items, editorial, public, transcripts = assemble()
    selected = [row for key, row in public.items() if row["visible"] and row["canonical_id"] == int(key)]
    report = {"unique_originals": len(items), "public_unique": len(selected), "hidden_unique": sum(not public[str(item["id"])]["visible"] for item in items),
        "collection_members_consolidated": sum(public[str(item["id"])]["visible"] and public[str(item["id"])]["canonical_id"] != item["id"] for item in items),
        "duplicate_listings_removed": sum(len(item["ids"]) - 1 for item in items),
        "scopes": dict(Counter(row["scope"] for row in selected)),
        "roles": dict(Counter(row["role"] for row in editorial.values())),
        "transcribed": len(transcripts), "public_transcripts": sum(row["visible"] for row in transcripts.values()),
        "chapters": sum(len(row["chapters"]) for row in selected)}
    print(json.dumps(report), flush=True)
    if args.dry_run:
        return
    now = datetime.now(timezone.utc).isoformat()
    settings = {"version": 1, "updated_at": now, "public": public, "editorial": editorial,
                "review_state": "descriptive_metadata_only_not_scholarly_assessments"}
    registry = ROOT / "frontend/src/content/media-collections.json"
    settings["collections"] = json.loads(registry.read_text()) if registry.exists() else {}
    local_path = ROOT / "data/research/research.sqlite3"
    backup = ROOT / "data/research/backups" / ("pre-media-catalogue-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + ".sqlite3")
    with sqlite3.connect(local_path) as source, sqlite3.connect(backup) as target:
        source.backup(target)
    backup.chmod(0o600)
    extracts = []
    with sqlite3.connect(local_path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        for item in items:
            row = editorial[str(item["id"])]
            for occurrence in item["ids"]:
                db.execute("UPDATE research_sources SET editorial_title=? WHERE legacy_id=?", (row["title"], occurrence))
            if item["id"] in transcripts:
                transcript = transcripts[item["id"]]["raw"]
                media_id, source_id = db.execute("SELECT id,source_id FROM research_media WHERE legacy_id=?", (item["id"],)).fetchone()
                text = transcript["text"]
                extract = (str(uuid.uuid5(uuid.NAMESPACE_URL, "othmani/transcript/" + item["sha"])), source_id, media_id,
                    "speech_transcript", text, hashlib.sha256(text.encode()).hexdigest(), 0, "ar", 0,
                    round(transcript["duration"] * 1000), "unverified", "whisper-1_word_timed", now)
                db.execute("INSERT INTO research_extracts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET text=excluded.text,text_sha256=excluded.text_sha256", extract)
                extracts.append(tuple(db.execute("SELECT * FROM research_extracts WHERE id=?", (extract[0],)).fetchone()))
        db.execute("INSERT INTO research_catalogue_settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ("media_catalogue", json.dumps(settings, ensure_ascii=False)))
    if args.sync_cloud:
        import psycopg
        from psycopg.types.json import Json
        values = config()
        url = values["RESEARCH_POSTGRES_URL"]
        host = urlparse(url).hostname
        if host != values["NEON_DATABASE_HOST"] or not host.endswith(".neon.tech"):
            raise ValueError("Unexpected cloud destination")
        with psycopg.connect(url, connect_timeout=30) as conn:
            previous = conn.execute("SELECT value FROM research.research_catalogue_settings WHERE key='media_catalogue'").fetchone()
            save(CACHE / "pre-cloud-catalogue.json", previous[0] if previous else {})
            conn.execute("INSERT INTO research.research_catalogue_settings(key,value) VALUES ('media_catalogue',%s) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (Json(settings),))
            with conn.cursor() as cursor:
                cursor.executemany("UPDATE research.research_sources SET editorial_title=%s WHERE legacy_id=%s", [(editorial[str(item["id"])]["title"], occurrence) for item in items for occurrence in item["ids"]])
                cursor.executemany("INSERT INTO research.research_extracts VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET text=excluded.text,text_sha256=excluded.text_sha256", extracts)
            conn.execute((ROOT / "scripts/media-catalogue-view.sql").read_text())
            count = conn.execute("SELECT count(*) FROM research.website_catalogue").fetchone()[0]
            if count != len(public):
                raise ValueError("Public catalogue verification mismatch")
        # Verify read-only access separately; never send administrator credentials to the app.
        with psycopg.connect(values["RESEARCH_READ_DATABASE_URL"], connect_timeout=30) as reader:
            assert reader.execute("SELECT count(*) FROM research.website_catalogue").fetchone()[0] == len(public)
    save(ROOT / "frontend/src/content/media-catalogue.json", {key: {field: value for field, value in row.items() if field != "transcript"} for key, row in public.items()})
    save(ROOT / "frontend/src/content/transcript-content.json", {key: row["transcript"] for key, row in public.items() if "transcript" in row and int(key) == row["canonical_id"]})
    captions = ROOT / "frontend/public/transcripts"
    captions.mkdir(parents=True, exist_ok=True)
    for id, record in transcripts.items():
        if not record["visible"]:
            continue
        rows = ["WEBVTT", "", "NOTE تفريغ آلي غير معتمد للاقتباس دون مراجعة الصوت", ""]
        for index, segment in enumerate(record["segments"], 1):
            if segment["end"] <= segment["start"]:
                continue
            rows.extend([str(index), f"{timestamp(segment['start'])} --> {timestamp(segment['end'])}",
                         segment["text"].replace("-->", "→").replace("\n", " "), ""])
        (captions / f"{id}.vtt").write_text("\n".join(rows))
    save(CACHE / "publication-report.json", report)
    print("Arabic catalogue, restricted cloud view and caption assets prepared.", flush=True)


if __name__ == "__main__":
    main()
