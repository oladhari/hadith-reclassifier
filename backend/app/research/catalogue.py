"""Idempotent local import, storage planning, audit, and portable export.
No networking, AI, cloud writes, or changes to original archives.
"""

from __future__ import annotations
import hashlib, json, os, re, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, event, select, func, insert
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from . import schema as s

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / "data/research/research.sqlite3"
ARCHIVE = ROOT.parent / "telegram-archive/kkee9938"


def now():
    return datetime.now(timezone.utc).isoformat()


def uid(*parts):
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            "othmani/research/v1/"
            + json.dumps(parts, ensure_ascii=False, separators=(",", ":")),
        )
    )


def digest(value):
    return hashlib.sha256(
        value if isinstance(value, bytes) else value.encode()
    ).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def normalize(text):
    return (
        re.sub(
            r"\s+",
            " ",
            re.sub("[\u064b-\u065f\u0670\u0640]", "", text).translate(
                str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي"})
            ),
        )
        .strip()
        .lower()
    )


def open_database(path=DEFAULT_DB, *, read_only=False):
    os.umask(0o077)
    path = Path(path).resolve()
    if read_only:
        if not path.is_file():
            raise FileNotFoundError(path)
        engine = create_engine(
            "sqlite://",
            creator=lambda: sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=30),
        )
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            f"sqlite:///{path}",
            connect_args={"timeout": 30},
            json_serializer=lambda value: json.dumps(
                value, ensure_ascii=False, separators=(",", ":")
            ),
        )

    @event.listens_for(engine, "connect")
    def setup(dbapi, _):
        dbapi.execute("PRAGMA foreign_keys=ON")
        if not read_only:
            dbapi.execute("PRAGMA journal_mode=WAL")
        dbapi.execute("PRAGMA busy_timeout=30000")

    return engine


def missing(conn, table, rows):
    if not rows:
        return 0
    keys = list(table.primary_key.columns)
    if not keys:
        raise ValueError(f"No primary key: {table.name}")
    existing = {tuple(row) for row in conn.execute(select(*keys))}
    fresh = []
    for row in rows:
        key = tuple(row[col.name] for col in keys)
        if key not in existing:
            fresh.append(row)
            existing.add(key)
    for start in range(0, len(fresh), 500):
        conn.execute(insert(table), fresh[start : start + 500])
    return len(fresh)


SCHEMA_VERSION = 3


def initialize(engine):
    # Version 3 adds filter profiles, routes, observations and reproducible runs.
    s.schema_versions.create(engine, checkfirst=True)
    with engine.connect() as conn:
        versions = conn.execute(select(s.schema_versions.c.version)).scalars().all()
        if versions and max(versions) > SCHEMA_VERSION:
            raise RuntimeError("Database schema is newer than this importer")
    s.metadata.create_all(engine)
    with engine.begin() as conn:
        missing(conn, s.schema_versions, [{"version": 1, "applied_at": now()}])
        columns = {
            r[1]
            for r in conn.exec_driver_sql("PRAGMA table_info(research_book_entries)")
        }
        if "required_verdict" not in columns:
            if conn.scalar(select(func.count()).select_from(s.book_entries)):
                raise RuntimeError(
                    "Book entries exist; explicit reviewed migration is required"
                )
            s.book_entries.drop(conn)
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_research_assessment_identity_verdict ON research_assessments (id, hadith_id, verdict)"
            )
            s.book_entries.create(conn)
        missing(
            conn, s.schema_versions, [{"version": 2, "applied_at": now()}, {"version": SCHEMA_VERSION, "applied_at": now()}]
        )


def import_all(engine, archive=ARCHIVE, corpus=None, content=None):
    archive = Path(archive).resolve()
    corpus = Path(corpus or ROOT / "data/hadiths").resolve()
    content = Path(content or ROOT / "frontend/src/content").resolve()
    seed = load(content / "editorial-seed.json")
    report = load(content / "archive-themes.json")
    public = load(content / "local-sources.json")
    index = load(content / "archive-index.json")
    paths = [
        content / n
        for n in [
            "editorial-seed.json",
            "archive-themes.json",
            "local-sources.json",
            "archive-index.json",
        ]
    ] + sorted(corpus.glob("*.json"))
    inputs = {p.name: digest(p.read_bytes()) for p in paths}
    raw = sqlite3.connect(f"file:{archive / 'archive.sqlite3'}?mode=ro", uri=True)
    raw.row_factory = sqlite3.Row
    records = [dict(row) for row in raw.execute("SELECT * FROM messages ORDER BY id")]
    raw.close()
    inputs["archive_snapshot"] = digest(
        json.dumps([(r["id"], digest(r["raw_json"]), r["sha256"]) for r in records])
    )
    fingerprint = digest(json.dumps(inputs, sort_keys=True))
    batch = uid("import", fingerprint)
    timestamp = now()
    for item in index:
        file = archive / item["path"]
        if not file.is_file() or file.stat().st_size != item["size"]:
            raise RuntimeError(f"Missing/wrong-size original: {item['id']}")
    raw_by_id = {r["id"]: r for r in records}
    asset_by_id = {a["id"]: a for a in index}
    # Input validation prevents silent merging or dropping of original hadith records.
    corpus_data = {}
    for slug in seed["collections"]:
        corpus_data[slug] = {
            lang: (
                load(corpus / f"{lang}-{slug}.json"),
                digest((corpus / f"{lang}-{slug}.json").read_bytes()),
            )
            for lang in ["ara", "eng"]
        }
        numbers = [
            str(r.get("hadithnumber")) for r in corpus_data[slug]["ara"][0]["hadiths"]
        ]
        if len(numbers) != len(set(numbers)):
            raise RuntimeError(f"Ambiguous Arabic source numbering: {slug}")
    with engine.begin() as conn:
        missing(
            conn,
            s.settings,
            [
                {
                    "key": "archive_analysis",
                    "value": {
                        k: report[k]
                        for k in [
                            "schemaVersion",
                            "scope",
                            "totalPosts",
                            "textPosts",
                            "latestMessageId",
                            "method",
                        ]
                    },
                },
                {"key": "collection_order", "value": list(seed["collections"])},
                {
                    "key": "case_match_configuration",
                    "value": {
                        slug: {"terms": v["terms"], "requiredTerms": v["requiredTerms"]}
                        for slug, v in report["cases"].items()
                    },
                },
            ],
        )
        missing(
            conn,
            s.imports,
            [
                dict(
                    id=batch,
                    fingerprint=fingerprint,
                    inputs=inputs,
                    created_at=timestamp,
                )
            ],
        )
        missing(
            conn,
            s.sources,
            [
                dict(
                    id=uid("source", r["id"]),
                    legacy_id=r["id"],
                    reference_code=f"SRC-{r['id']:06d}",
                    source_date=r["date"],
                    kind="attachment" if r["media_path"] else "research_lead",
                    review_state="imported",
                    editorial_title=None,
                    reviewed_by=None,
                    reviewed_at=None,
                    created_at=timestamp,
                )
                for r in records
            ],
        )
        missing(
            conn,
            s.provenance,
            [
                dict(
                    id=uid("provenance", r["id"], digest(r["raw_json"])),
                    source_id=uid("source", r["id"]),
                    import_id=batch,
                    provider="telegram_collection",
                    external_id=str(r["id"]),
                    content_sha256=digest(r["raw_json"]),
                    original_text=r["text"],
                    original_payload=json.loads(r["raw_json"]),
                    created_at=timestamp,
                )
                for r in records
            ],
        )
        group_records = {}
        for r in records:
            g = json.loads(r["raw_json"]).get("grouped_id")
            if g:
                group_records.setdefault(str(g), []).append(r["id"])
        missing(
            conn,
            s.albums,
            [
                dict(id=uid("album", g), external_group_id=g, created_at=timestamp)
                for g in group_records
            ],
        )
        missing(
            conn,
            s.album_members,
            [
                dict(album_id=uid("album", g), source_id=uid("source", mid), position=i)
                for g, members in group_records.items()
                for i, mid in enumerate(members)
            ],
        )
        object_rows = []
        location_rows = []
        media_rows = []
        for item in index:
            raw_item = raw_by_id[item["id"]]
            sha = raw_item["sha256"]
            if not sha or not re.fullmatch("[0-9a-f]{64}", sha):
                raise RuntimeError("Missing verified content hash")
            object_id = uid("object", sha)
            key = f"originals/sha256/{sha[:2]}/{sha}"
            object_rows.append(
                dict(
                    id=object_id,
                    sha256=sha,
                    byte_size=item["size"],
                    mime_type=item["mime"],
                    object_key=key,
                    created_at=timestamp,
                )
            )
            location_rows.extend(
                [
                    dict(
                        id=uid("location", sha, "local", item["path"]),
                        object_id=object_id,
                        provider="local",
                        bucket="",
                        key=item["path"],
                        state="available",
                        verified_at=timestamp,
                    ),
                    dict(
                        id=uid("location", sha, "r2", key),
                        object_id=object_id,
                        provider="r2",
                        bucket="",
                        key=key,
                        state="planned",
                        verified_at=None,
                    ),
                ]
            )
            media_rows.append(
                dict(
                    id=uid("media", item["id"]),
                    source_id=uid("source", item["id"]),
                    object_id=object_id,
                    legacy_id=item["id"],
                    kind=item["kind"],
                    original_name=item["name"],
                    mime_type=item["mime"],
                    archive_relative_path=item["path"],
                    source_date=item["date"],
                    created_at=timestamp,
                )
            )
        missing(conn, s.objects, object_rows)
        missing(conn, s.locations, location_rows)
        missing(conn, s.media, media_rows)
        for mid, book in seed["sources"].items():
            mid = int(mid)
            work_id = uid("work", mid)
            missing(
                conn,
                s.works,
                [
                    dict(
                        id=work_id,
                        title=book["title"],
                        author_name=None,
                        verification_state="needs_verification",
                        created_at=timestamp,
                    )
                ],
            )
            missing(
                conn,
                s.editions,
                [
                    dict(
                        id=uid("edition", mid),
                        work_id=work_id,
                        editor_name=None,
                        publisher=None,
                        edition_label=None,
                        publication_year=None,
                        verification_state="needs_verification",
                        created_at=timestamp,
                    )
                ],
            )
            page = re.search(r"الصفحة الظاهرة:\s*(\d+)", book["detail"])
            missing(
                conn,
                s.citations,
                [
                    dict(
                        id=uid("citation", mid),
                        source_id=uid("source", mid),
                        media_id=uid("media", mid) if mid in asset_by_id else None,
                        work_id=work_id,
                        edition_id=uid("edition", mid),
                        volume_label=None,
                        printed_page=page.group(1) if page else None,
                        pdf_page=None,
                        description=book["detail"],
                        verification_state="needs_verification",
                        created_at=timestamp,
                    )
                ],
            )
        extracted = [
            dict(
                id=uid(
                    "extract", int(mid), "manual_partial_quote", digest(book["quote"])
                ),
                source_id=uid("source", int(mid)),
                media_id=uid("media", int(mid)),
                kind="manual_partial_quote",
                text=book["quote"],
                text_sha256=digest(book["quote"]),
                ordinal=0,
                language="ar",
                start_ms=None,
                end_ms=None,
                review_state="visually_checked",
                method="manual_partial_transcription",
                created_at=timestamp,
            )
            for mid, book in seed["sources"].items()
            if book.get("quote")
        ]
        for key, r in public.items():
            for ordinal, text in enumerate(r["quotes"]):
                extracted.append(
                    dict(
                        id=uid("extract", int(key), "collection_quote", digest(text)),
                        source_id=uid("source", int(key)),
                        media_id=None,
                        kind="collection_quote",
                        text=text,
                        text_sha256=digest(text),
                        ordinal=ordinal,
                        language="ar",
                        start_ms=None,
                        end_ms=None,
                        review_state="unverified",
                        method="quoted_fragment_extraction_v1",
                        created_at=timestamp,
                    )
                )
        missing(conn, s.extracts, extracted)
        topic_report = {r["slug"]: r for r in report["topics"]}
        missing(
            conn,
            s.topics,
            [
                dict(
                    id=uid("topic", t["slug"]),
                    slug=t["slug"],
                    title=t["title"],
                    description=t["description"],
                    sort_order=i,
                    terms=topic_report[t["slug"]]["terms"],
                    required_terms=topic_report[t["slug"]]["requiredTerms"],
                    created_at=timestamp,
                )
                for i, t in enumerate(seed["topics"])
            ],
        )
        missing(
            conn,
            s.cases,
            [
                dict(
                    id=uid("case", c["slug"]),
                    slug=c["slug"],
                    title=c["title"],
                    category=c["category"],
                    editorial_data=c,
                    review_state="draft",
                    created_at=timestamp,
                )
                for c in seed["cases"]
            ],
        )
        missing(
            conn,
            s.topic_cases,
            [
                dict(
                    topic_id=uid("topic", t["slug"]),
                    case_id=uid("case", slug),
                    position=i,
                )
                for t in seed["topics"]
                for i, slug in enumerate(t["cases"])
            ],
        )
        missing(
            conn,
            s.topic_sources,
            [
                dict(
                    topic_id=uid("topic", t["slug"]),
                    source_id=uid("source", r["id"]),
                    matched_terms=r["matchedTerms"],
                    normalized_text_hash=r["normalizedTextHash"],
                    selected_reference=False,
                    link_state="suggested",
                )
                for t in report["topics"]
                for r in t["posts"]
            ],
        )
        case_links = []
        for case in seed["cases"]:
            matched = {p["id"]: p for p in report["cases"][case["slug"]]["posts"]}
            selected = set(case["posts"] + case["evidence"])
            for mid in sorted(set(matched) | selected):
                m = matched.get(mid, {})
                case_links.append(
                    dict(
                        case_id=uid("case", case["slug"]),
                        source_id=uid("source", mid),
                        matched_terms=m.get("matchedTerms", []),
                        normalized_text_hash=m.get("normalizedTextHash"),
                        selected_reference=mid in selected,
                        link_state="suggested",
                    )
                )
        missing(conn, s.case_sources, case_links)
        missing(
            conn,
            s.rules,
            [
                dict(
                    id=uid("rule", n),
                    code=f"layer-{n}",
                    title=title,
                    description=description,
                    version=1,
                    status="proposed",
                    created_at=timestamp,
                )
                for n, title, description in seed["layers"]
            ],
        )
        missing(
            conn,
            s.collections,
            [
                dict(
                    id=uid("collection", slug),
                    slug=slug,
                    title=title,
                    created_at=timestamp,
                )
                for slug, title in seed["collections"].items()
            ],
        )
        missing(
            conn,
            s.corpus_files,
            [
                dict(
                    id=uid("corpus_file", slug, lang, sha),
                    collection_id=uid("collection", slug),
                    language={"ara": "ar", "eng": "en"}[lang],
                    filename=f"{lang}-{slug}.json",
                    sha256=sha,
                    metadata=data.get("metadata", {}),
                    record_count=len(data["hadiths"]),
                    created_at=timestamp,
                )
                for slug, languages in corpus_data.items()
                for lang, (data, sha) in languages.items()
            ],
        )
        for slug, languages in corpus_data.items():
            arabic = languages["ara"][0]["hadiths"]
            number_ids = {
                str(h["hadithnumber"]): uid("hadith", slug, str(h["hadithnumber"]))
                for h in arabic
            }
            cid = uid("collection", slug)
            missing(
                conn,
                s.hadiths,
                [
                    dict(
                        id=number_ids[str(h["hadithnumber"])],
                        collection_id=cid,
                        source_number=str(h["hadithnumber"]),
                        source_ordinal=i,
                        book_number=str(h.get("reference", {}).get("book"))
                        if h.get("reference", {}).get("book") is not None
                        else None,
                        book_hadith_number=str(h.get("reference", {}).get("hadith"))
                        if h.get("reference", {}).get("hadith") is not None
                        else None,
                        review_state="unreviewed",
                        created_at=timestamp,
                    )
                    for i, h in enumerate(arabic)
                ],
            )
            for lang, (data, file_sha) in languages.items():
                texts = [
                    dict(
                        id=uid("hadith_text", slug, lang, i),
                        hadith_id=number_ids.get(str(h.get("hadithnumber"))),
                        collection_id=cid,
                        language={"ara": "ar", "eng": "en"}[lang],
                        source_ordinal=i,
                        source_number=str(h.get("hadithnumber")),
                        text=h.get("text") or "",
                        normalized_text=normalize(h.get("text") or ""),
                        original_data=h,
                        source_file=f"{lang}-{slug}.json",
                        source_file_sha256=file_sha,
                        created_at=timestamp,
                    )
                    for i, h in enumerate(data["hadiths"])
                ]
                missing(conn, s.hadith_texts, texts)
    return audit(engine, archive)


def audit(engine, archive=ARCHIVE):
    with engine.connect() as conn:
        counts = {
            t.name: conn.scalar(select(func.count()).select_from(t))
            for t in s.metadata.sorted_tables
        }
        missing_files = []
        for row in conn.execute(
            select(
                s.media.c.legacy_id,
                s.media.c.archive_relative_path,
                s.objects.c.byte_size,
            ).join(s.objects, s.media.c.object_id == s.objects.c.id)
        ):
            file = Path(archive) / row.archive_relative_path
            if not file.is_file() or file.stat().st_size != row.byte_size:
                missing_files.append(row.legacy_id)
        fk_errors = [list(r) for r in conn.exec_driver_sql("PRAGMA foreign_key_check")]
        integrity = conn.exec_driver_sql("PRAGMA quick_check").scalar()
        unmatched = conn.scalar(
            select(func.count())
            .select_from(s.hadith_texts)
            .where(s.hadith_texts.c.hadith_id.is_(None))
        )
        object_bytes = conn.scalar(select(func.sum(s.objects.c.byte_size))) or 0
        media_bytes = (
            conn.scalar(
                select(func.sum(s.objects.c.byte_size)).select_from(
                    s.media.join(s.objects, s.media.c.object_id == s.objects.c.id)
                )
            )
            or 0
        )
    return {
        "counts": counts,
        "integrity": integrity,
        "foreign_key_errors": fk_errors,
        "missing_or_wrong_size_media": missing_files,
        "unmatched_hadith_texts": unmatched,
        "unique_object_bytes": object_bytes,
        "all_attachment_bytes": media_bytes,
        "duplicate_attachment_instances": counts[s.media.name] - counts[s.objects.name],
    }


def export_portable(engine, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    private_tables = {s.provenance.name, s.imports.name}
    # No rows are published by this export. RLS defaults to deny until policies are designed.
    ddl = [
        "-- PostgreSQL baseline v2. Apply to an empty research database/schema.\nBEGIN;"
    ]
    for table in s.metadata.sorted_tables:
        ddl.append(str(CreateTable(table).compile(dialect=postgresql.dialect())) + ";")
        for index in sorted(table.indexes, key=lambda x: x.name):
            ddl.append(
                str(CreateIndex(index).compile(dialect=postgresql.dialect())) + ";"
            )
        ddl.append(f'ALTER TABLE "{table.name}" ENABLE ROW LEVEL SECURITY;')
    ddl.append("COMMIT;")
    (directory / "postgresql-schema.sql").write_text("\n\n".join(ddl))
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "private_tables_omitted": sorted(private_tables),
        "tables": {},
        "storage": "R2 object keys are planned only. No cloud upload has occurred.",
    }
    with engine.connect() as conn:
        for table in s.metadata.sorted_tables:
            if table.name in private_tables:
                continue
            rows = [dict(r) for r in conn.execute(select(table)).mappings()]
            if table is s.locations:
                rows = [r for r in rows if r["provider"] == "r2"]
            if table is s.media:
                for row in rows:
                    row["archive_relative_path"] = None
            target = directory / f"{table.name}.jsonl"
            target.write_text(
                "".join(
                    json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                    for r in rows
                )
            )
            manifest["tables"][table.name] = {
                "rows": len(rows),
                "sha256": digest(target.read_bytes()),
            }
        objects = {r["id"]: dict(r) for r in conn.execute(select(s.objects)).mappings()}
        local = {
            r["object_id"]: r["key"]
            for r in conn.execute(
                select(s.locations).where(s.locations.c.provider == "local")
            ).mappings()
        }
        remote_locations = {
            r["object_id"]: dict(r) for r in conn.execute(select(s.locations).where(s.locations.c.provider == "r2")).mappings()
        }
        upload = []
        for oid, obj in objects.items():
            upload.append(
                {
                    "object_id": oid,
                    "object_key": obj["object_key"],
                    "sha256": obj["sha256"],
                    "byte_size": obj["byte_size"],
                    "mime_type": obj["mime_type"],
                    "local_relative_path": local[oid],
                    "upload_state": "verified_uploaded" if remote_locations.get(oid, {}).get("state") == "available" else "not_uploaded",
                    "remote_key": remote_locations.get(oid, {}).get("key"),
                    "remote_bucket": remote_locations.get(oid, {}).get("bucket"),
                }
            )
        (directory / "r2-upload-manifest.jsonl").write_text(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in upload)
        )
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return manifest
