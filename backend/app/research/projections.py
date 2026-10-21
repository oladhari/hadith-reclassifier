"""Build the current website's read-only JSON projections from the catalogue.
The relational database is the editing/import store; frontend snapshots contain no private provenance.
"""

import json
from pathlib import Path
from sqlalchemy import select
from . import schema as s
from .catalogue import digest


def project_frontend(engine, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with engine.connect() as conn:
        records = [
            dict(row)
            for row in conn.execute(
                select(s.sources).order_by(s.sources.c.legacy_id)
            ).mappings()
        ]
        record_by_id = {r["id"]: r for r in records}
        media = [
            dict(r)
            for r in conn.execute(
                select(s.media).order_by(s.media.c.legacy_id)
            ).mappings()
        ]
        objects = {r["id"]: dict(r) for r in conn.execute(select(s.objects)).mappings()}
        assets = []
        for m in media:
            if m["archive_relative_path"] is None:
                raise RuntimeError(
                    "Local frontend media projection requires local locations; use an R2 adapter after migration"
                )
            assets.append(
                dict(
                    id=m["legacy_id"],
                    date=m["source_date"],
                    kind=m["kind"],
                    mime=m["mime_type"],
                    path=m["archive_relative_path"],
                    size=objects[m["object_id"]]["byte_size"],
                    name=m["original_name"],
                )
            )
        media_by_source = {m["source_id"]: m["legacy_id"] for m in media}
        albums = {}
        for r in conn.execute(
            select(s.album_members).order_by(s.album_members.c.position)
        ).mappings():
            albums.setdefault(r["album_id"], []).append(r["source_id"])
        album_files = {}
        for members in albums.values():
            files = [media_by_source[mid] for mid in members if mid in media_by_source]
            for member in members:
                album_files[member] = files
        quotes = {}
        for r in conn.execute(
            select(s.extracts)
            .where(
                s.extracts.c.kind == "collection_quote",
                s.extracts.c.review_state.in_(["unverified", "verified"]),
            )
            .order_by(s.extracts.c.ordinal)
        ).mappings():
            quotes.setdefault(r["source_id"], []).append(r["text"])
        local = {
            str(r["legacy_id"]): dict(
                id=r["legacy_id"],
                date=r["source_date"],
                files=album_files.get(
                    r["id"],
                    [media_by_source[r["id"]]] if r["id"] in media_by_source else [],
                ),
                quotes=quotes.get(r["id"], []),
            )
            for r in records
        }
        case_rows = [dict(r) for r in conn.execute(select(s.cases)).mappings()]
        case_rows.sort(key=lambda r: r["editorial_data"].get("number", ""))
        cases = [
            {**r["editorial_data"], "title": r["title"], "category": r["category"]}
            for r in case_rows
        ]
        topic_rows = [
            dict(r)
            for r in conn.execute(
                select(s.topics).order_by(s.topics.c.sort_order)
            ).mappings()
        ]
        tc = {}
        for r in conn.execute(
            select(s.topic_cases).order_by(s.topic_cases.c.position)
        ).mappings():
            tc.setdefault(r["topic_id"], []).append(
                next(c["slug"] for c in case_rows if c["id"] == r["case_id"])
            )
        topic_defs = [
            dict(
                slug=t["slug"],
                title=t["title"],
                description=t["description"],
                cases=tc.get(t["id"], []),
            )
            for t in topic_rows
        ]
        known_sources = {}
        for row in conn.execute(
            select(s.citations, s.works.c.title.label("work_title")).join(
                s.works, s.citations.c.work_id == s.works.c.id
            )
        ).mappings():
            mid = record_by_id[row["source_id"]]["legacy_id"]
            known_sources[str(mid)] = dict(
                title=row["work_title"], detail=row["description"], quote=""
            )
        for quote in conn.execute(
            select(s.extracts).where(s.extracts.c.kind == "manual_partial_quote")
        ).mappings():
            mid = record_by_id[quote["source_id"]]["legacy_id"]
            if str(mid) in known_sources:
                known_sources[str(mid)]["quote"] = quote["text"]
        layer_rows = (
            conn.execute(select(s.rules).order_by(s.rules.c.code)).mappings().all()
        )
        layers = [
            [r["code"].removeprefix("layer-"), r["title"], r["description"]]
            for r in layer_rows
        ]
        collections = {
            r["slug"]: r["title"]
            for r in conn.execute(
                select(s.collections).order_by(s.collections.c.slug)
            ).mappings()
        }
        settings = {
            r["key"]: r["value"] for r in conn.execute(select(s.settings)).mappings()
        }
        collections = {slug: collections[slug] for slug in settings["collection_order"]}
        profile_row = conn.execute(select(s.filter_profiles).where(s.filter_profiles.c.profile_key == "othmani-research").order_by(s.filter_profiles.c.version.desc())).mappings().first()
        filter_profile = profile_row["definition"] if profile_row else {"key": "othmani-research", "version": 0, "status": "draft", "layers": []}
        report = {**settings["archive_analysis"], "topics": [], "cases": {}}

        def matched(table, owner_column, owner_id):
            rows = conn.execute(
                select(table).where(
                    table.c[owner_column] == owner_id,
                    table.c.normalized_text_hash.is_not(None),
                )
            ).mappings()
            posts = sorted(
                [
                    dict(
                        id=record_by_id[r["source_id"]]["legacy_id"],
                        matchedTerms=r["matched_terms"],
                        normalizedTextHash=r["normalized_text_hash"],
                    )
                    for r in rows
                ],
                key=lambda p: p["id"],
            )
            return dict(
                postCount=len(posts),
                distinctTextCount=len({p["normalizedTextHash"] for p in posts}),
                posts=posts,
            )

        for t in topic_rows:
            report["topics"].append(
                dict(
                    slug=t["slug"],
                    title=t["title"],
                    terms=t["terms"],
                    requiredTerms=t["required_terms"],
                    **matched(s.topic_sources, "topic_id", t["id"]),
                )
            )
        for c in case_rows:
            report["cases"][c["slug"]] = {
                **settings["case_match_configuration"][c["slug"]],
                **matched(s.case_sources, "case_id", c["id"]),
            }
    from .corpus_progress import project_progress

    with engine.connect() as conn:
        corpus_progress = project_progress(conn)
    generated = {
        "archive-index.json": assets,
        "media-objects.json": {str(m["legacy_id"]): objects[m["object_id"]]["object_key"] for m in media},
        "corpus-progress.json": corpus_progress,
        "filter-layers.json": filter_profile,
        "filter-case-studies.json": settings.get("filter_case_studies", {}).get("public", []),
        "local-sources.json": local,
        "editorial-seed.json": dict(
            cases=cases,
            layers=layers,
            sources=known_sources,
            collections=collections,
            topics=topic_defs,
        ),
        "archive-themes.json": report,
        "evidence-analysis.json": settings.get("evidence_analysis", {}).get("public", {"media": {}, "cases": {}}),
        "public-evidence.json": settings.get("public_evidence", {"cases": {}, "labels": {}}),
    }
    result = {}
    for name, data in generated.items():
        target = directory / name
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(target)
        result[name] = {"sha256": digest(target.read_bytes())}
    return result
