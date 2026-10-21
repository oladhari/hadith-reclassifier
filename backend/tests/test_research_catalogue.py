"""Local catalogue integration checks; no API calls, cloud connections, or paid jobs."""

import json, sqlite3, tempfile, unittest
from pathlib import Path
from sqlalchemy import select, func, insert, update
from sqlalchemy.exc import IntegrityError
from app.research import schema as s
from app.research.catalogue import (
    DEFAULT_DB,
    open_database,
    initialize,
    import_all,
    audit,
    export_portable,
    now,
)
from app.research.projections import project_frontend


class CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEFAULT_DB.exists():
            raise unittest.SkipTest("Run scripts/research_db.py import first")
        cls.engine = open_database(DEFAULT_DB)
        initialize(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_real_import_is_idempotent_and_complete(self):
        first = import_all(self.engine)
        second = import_all(self.engine)
        self.assertEqual(first["counts"], second["counts"])
        self.assertEqual(second["integrity"], "ok")
        self.assertEqual(second["counts"]["research_sources"], 2477)
        self.assertEqual(second["counts"]["research_media"], 1907)
        self.assertEqual(second["counts"]["research_hadiths"], 36390)
        self.assertEqual(second["counts"]["research_hadith_texts"], 72780)
        self.assertEqual(second["foreign_key_errors"], [])
        self.assertEqual(second["missing_or_wrong_size_media"], [])
        self.assertEqual(second["unmatched_hadith_texts"], 0)
        self.assertEqual(second["counts"]["research_assessments"], 0)
        self.assertEqual(second["counts"]["research_book_entries"], 0)
        self.assertEqual(second["counts"]["research_processing_jobs"], first["counts"]["research_processing_jobs"])
        with self.engine.connect() as conn:
            self.assertEqual(conn.scalar(select(func.count()).select_from(s.extracts).where(s.extracts.c.kind == "ocr_text", s.extracts.c.review_state != "unverified")), 0)

    def test_deduplication_preserves_all_attachments(self):
        report = audit(self.engine)
        self.assertEqual(report["counts"]["research_objects"], 1805)
        self.assertEqual(report["duplicate_attachment_instances"], 102)
        with self.engine.connect() as conn:
            planned = conn.scalar(
                select(func.count())
                .select_from(s.locations)
                .where(s.locations.c.provider == "r2", s.locations.c.state.in_(["planned", "available"]))
            )
            self.assertEqual(planned, 1805)

    def test_frontend_projection_has_complete_albums_and_no_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            project_frontend(self.engine, d)
            sources = json.loads((Path(d) / "local-sources.json").read_text())
            self.assertEqual(sources["195"]["files"], [195, 196])
            self.assertEqual(sources["219"]["files"], [219, 220, 221])
            self.assertEqual(sources["1315"]["files"], [1315, 1316])
            public = "".join(p.read_text() for p in Path(d).glob("*.json"))
            self.assertNotIn("https://t.me/", public)
            self.assertNotIn("original_payload", public)
            editorial = json.loads((Path(d) / "editorial-seed.json").read_text())
            self.assertEqual(len(editorial["cases"]), 17)
            self.assertTrue(editorial["sources"]["195"]["quote"])
            self.assertEqual(len(editorial["topics"]), 8)
            profile = json.loads((Path(d) / "filter-layers.json").read_text())
            self.assertEqual(len(profile["layers"]), 22)
            self.assertEqual(profile["layers"][1]["key"], "quran_explicit")
            studies = json.loads((Path(d) / "filter-case-studies.json").read_text())
            self.assertEqual(len(studies), 5)
            self.assertTrue(all("source_posts" not in study for study in studies))
            keys = {layer["key"] for layer in profile["layers"]}
            self.assertTrue(all(set(study["layer_keys"]) <= keys for study in studies))
            evidence = json.loads((Path(d) / "public-evidence.json").read_text())
            self.assertEqual(evidence["cases"]["uthman-shirt"], [1316])
            self.assertNotIn(1315, evidence["cases"]["uthman-shirt"])
            readings = json.loads((Path(d) / "evidence-analysis.json").read_text())
            self.assertEqual(set(readings["media"]), {str(i) for ids in evidence["cases"].values() for i in ids})
            self.assertIn("محمد بن أبي بكر", readings["media"]["1315"]["reading"])
            self.assertNotIn("provenance", readings)
            self.assertNotIn("original_text", readings)
            self.assertIn("لا تصرّح", readings["media"]["1315"]["qualification"])

    def test_portable_export_restores_all_foreign_keys(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "export"
            manifest = export_portable(self.engine, out)
            self.assertFalse((out / "research_provenance.jsonl").exists())
            self.assertFalse((out / "research_imports.jsonl").exists())
            clone = open_database(Path(d) / "restored.sqlite3")
            s.metadata.create_all(clone)
            try:
                with clone.begin() as conn:
                    for table in s.metadata.sorted_tables:
                        file = out / f"{table.name}.jsonl"
                        if not file.exists():
                            continue
                        rows = [
                            json.loads(line) for line in file.read_text().splitlines()
                        ]
                        for start in range(0, len(rows), 500):
                            conn.execute(insert(table), rows[start : start + 500])
                        self.assertEqual(
                            conn.scalar(select(func.count()).select_from(table)),
                            manifest["tables"][table.name]["rows"],
                        )
                    self.assertEqual(
                        conn.exec_driver_sql("PRAGMA foreign_key_check").fetchall(), []
                    )
            finally:
                clone.dispose()
            keys = [
                json.loads(line)["object_key"]
                for line in (out / "r2-upload-manifest.jsonl").read_text().splitlines()
            ]
            self.assertEqual(len(keys), 1805)
            self.assertEqual(len(keys), len(set(keys)))

    def test_reimport_does_not_overwrite_editorial_changes(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "edited.sqlite3"
            with (
                sqlite3.connect(f"file:{DEFAULT_DB}?mode=ro", uri=True) as src,
                sqlite3.connect(dest) as target,
            ):
                src.backup(target)
            clone = open_database(dest)
            try:
                with clone.begin() as conn:
                    conn.execute(
                        update(s.cases)
                        .where(s.cases.c.slug == "ammar")
                        .values(title="عنوان تحريري محفوظ")
                    )
                import_all(clone)
                with clone.connect() as conn:
                    self.assertEqual(
                        conn.scalar(
                            select(s.cases.c.title).where(s.cases.c.slug == "ammar")
                        ),
                        "عنوان تحريري محفوظ",
                    )
            finally:
                clone.dispose()

    def test_review_and_book_guards(self):
        with tempfile.TemporaryDirectory() as d:
            engine = open_database(Path(d) / "guards.sqlite3")
            initialize(engine)
            try:
                with engine.begin() as c:
                    c.execute(
                        insert(s.collections),
                        dict(
                            id="collection",
                            slug="sample",
                            title="Sample",
                            created_at=now(),
                        ),
                    )
                    for h in ["h1", "h2"]:
                        c.execute(
                            insert(s.hadiths),
                            dict(
                                id=h,
                                collection_id="collection",
                                source_number=h,
                                source_ordinal=1,
                                review_state="unreviewed",
                                created_at=now(),
                            ),
                        )
                with self.assertRaises(IntegrityError), engine.begin() as c:
                    c.execute(
                        insert(s.assessments),
                        dict(
                            id="bad",
                            hadith_id="h1",
                            methodology_version="v1",
                            verdict="accepted",
                            created_at=now(),
                        ),
                    )
                with engine.begin() as c:
                    c.execute(
                        insert(s.assessments),
                        dict(
                            id="accepted",
                            hadith_id="h1",
                            methodology_version="v1",
                            verdict="accepted",
                            reviewer="test reviewer",
                            reviewed_at=now(),
                            created_at=now(),
                        ),
                    )
                    c.execute(
                        insert(s.assessments),
                        dict(
                            id="pending",
                            hadith_id="h2",
                            methodology_version="v1",
                            verdict="under_review",
                            created_at=now(),
                        ),
                    )
                for hadith, assessment in [("h2", "accepted"), ("h2", "pending")]:
                    with self.assertRaises(IntegrityError), engine.begin() as c:
                        c.execute(
                            insert(s.book_entries),
                            dict(
                                id="invalid",
                                hadith_id=hadith,
                                assessment_id=assessment,
                                edition="v1",
                                status="draft",
                                created_at=now(),
                            ),
                        )
                with self.assertRaises(IntegrityError), engine.begin() as c:
                    c.execute(
                        insert(s.book_entries),
                        dict(
                            id="missing-review",
                            hadith_id="h1",
                            assessment_id="accepted",
                            edition="v1",
                            status="approved",
                            created_at=now(),
                        ),
                    )
                with engine.begin() as c:
                    c.execute(
                        insert(s.book_entries),
                        dict(
                            id="valid",
                            hadith_id="h1",
                            assessment_id="accepted",
                            edition="v1",
                            status="approved",
                            reviewer="test reviewer",
                            reviewed_at=now(),
                            created_at=now(),
                        ),
                    )
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
