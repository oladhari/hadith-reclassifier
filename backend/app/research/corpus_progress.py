"""Publish accurate collection/workflow totals without exposing raw research notes."""

from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import func, select

from . import schema as s
from .catalogue import now

STATES = ("unreviewed", "in_progress", "needs_review", "accepted", "rejected")


def date_value(value):
    try:
        date = datetime.fromisoformat(value)
        return date.replace(tzinfo=UTC) if date.tzinfo is None else date.astimezone(UTC)
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=UTC)


def counters():
    return dict(
        total=0, with_text=0, filtered=0, in_book=0, **{key: 0 for key in STATES}
    )


def project_progress(conn):
    books = {
        r["id"]: {"slug": r["slug"], "title": r["title"], "counts": counters()}
        for r in conn.execute(select(s.collections)).mappings()
    }
    hadiths = [dict(r) for r in conn.execute(select(s.hadiths)).mappings()]
    nonempty = set(
        conn.execute(
            select(s.hadith_texts.c.hadith_id).where(
                s.hadith_texts.c.language == "ar",
                func.length(func.trim(s.hadith_texts.c.text)) > 0,
            )
        ).scalars()
    )
    routes = set(conn.execute(select(s.filter_routes.c.hadith_id)).scalars())
    observations = set(
        conn.execute(select(s.filter_observations.c.hadith_id)).scalars()
    )
    profile_versions = {
        r["id"]: r["version"]
        for r in conn.execute(select(s.filter_profiles)).mappings()
    }
    latest_runs = {}
    for run in conn.execute(select(s.filter_runs)).mappings():
        old = latest_runs.get(run["hadith_id"])
        rank = (
            profile_versions.get(run["profile_id"], 0),
            date_value(run["created_at"]),
            run["id"],
        )
        if not old or rank > old[0]:
            latest_runs[run["hadith_id"]] = (rank, dict(run))
    latest_assessments = {}
    for row in conn.execute(select(s.assessments)).mappings():
        old = latest_assessments.get(row["hadith_id"])
        rank = (
            date_value(row["reviewed_at"] or row["created_at"]),
            date_value(row["created_at"]),
            row["id"],
        )
        if not old or rank > old[0]:
            latest_assessments[row["hadith_id"]] = (rank, dict(row))
    entries = {}
    for entry in conn.execute(
        select(s.book_entries).where(s.book_entries.c.status == "approved")
    ).mappings():
        if entry["reviewer"] and entry["reviewed_at"]:
            entries.setdefault(entry["hadith_id"], []).append(dict(entry))
    records = {}
    for hadith in hadiths:
        hid = hadith["id"]
        book = books[hadith["collection_id"]]
        run = latest_runs.get(hid, (None, None))[1]
        assessment = latest_assessments.get(hid, (None, None))[1]
        # A dry baseline with every layer missing is not a filtered hadith.
        meaningful = bool(
            run
            and any(
                r.get("state") in {"clear", "flagged", "disputed", "not_applicable"}
                and r.get("observation_ids")
                for r in run["report"].get("results", [])
            )
        )
        final = bool(
            assessment
            and assessment["verdict"] in {"accepted", "rejected"}
            and (assessment["reviewer"] or "").strip()
            and date_value(assessment["reviewed_at"]) > datetime.min.replace(tzinfo=UTC)
        )
        state = (
            assessment["verdict"]
            if final
            else "needs_review"
            if assessment or meaningful
            else "in_progress"
            if hid in routes or hid in observations
            else "unreviewed"
        )
        approved_entries = [
            e
            for e in entries.get(hid, [])
            if final and state == "accepted" and e["assessment_id"] == assessment["id"]
        ]
        counts = book["counts"]
        counts["total"] += 1
        counts["with_text"] += int(hid in nonempty)
        counts[state] += 1
        counts["filtered"] += int(meaningful)
        counts["in_book"] += int(bool(approved_entries))
        if state != "unreviewed" or meaningful:
            record = {
                "status": state,
                "filtered": meaningful,
                "in_book": bool(approved_entries),
            }
            if run and meaningful:
                record["checks"] = run["report"].get("summary", {})
            if final:
                record["review"] = {
                    "verdict": assessment["verdict"],
                    "reasoning": assessment["reasoning"] or "",
                    "reviewed_at": assessment["reviewed_at"],
                }
            if approved_entries:
                record["book_entries"] = [
                    {"edition": e["edition"], "number": e["entry_number"]}
                    for e in approved_entries
                ]
            records[book["slug"] + ":" + hadith["source_number"]] = record
    totals = Counter()
    for book in books.values():
        totals.update(book["counts"])
    return {
        "generated_at": now(),
        "counts": dict(totals),
        "collections": sorted(
            books.values(),
            key=lambda b: (
                [
                    "bukhari",
                    "muslim",
                    "malik",
                    "abudawud",
                    "tirmidhi",
                    "nasai",
                    "ibnmajah",
                ].index(b["slug"])
                if b["slug"]
                in [
                    "bukhari",
                    "muslim",
                    "malik",
                    "abudawud",
                    "tirmidhi",
                    "nasai",
                    "ibnmajah",
                ]
                else 99
            ),
        ),
        "records": records,
        "missing_collections": [
            {
                "title": "مسند الإمام أحمد",
                "note": "توجد صفحات مصوّرة للاستدلال؛ المجموعة الحديثية الكاملة غير مضافة بعد.",
            }
        ],
    }
