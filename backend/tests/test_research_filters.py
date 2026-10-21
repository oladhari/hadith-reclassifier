"""Semantic triage tests using synthetic evidence in a disposable database."""

import json
import tempfile
import unittest
from pathlib import Path

from app.research import schema as s
from app.research.catalogue import initialize, now, open_database, uid
from app.research.corpus_progress import project_progress
from app.research.filters import (
    PROFILE_PATH,
    add_observation,
    add_route,
    evaluate,
    install_profile,
)
from sqlalchemy import func, insert, select
from sqlalchemy.exc import OperationalError


class FilterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = open_database(Path(self.tmp.name) / "test.sqlite3")
        initialize(self.engine)
        self.profile = install_profile(self.engine)
        self.hadith = uid("fixture-hadith")
        self.source = uid("fixture-source")
        collection = uid("fixture-collection")
        with self.engine.begin() as c:
            c.execute(
                insert(s.collections),
                {
                    "id": collection,
                    "slug": "test",
                    "title": "اختبار",
                    "created_at": now(),
                },
            )
            c.execute(
                insert(s.hadiths),
                {
                    "id": self.hadith,
                    "collection_id": collection,
                    "source_number": "1",
                    "source_ordinal": 0,
                    "created_at": now(),
                },
            )
            c.execute(
                insert(s.hadith_texts),
                {
                    "id": uid("fixture-text"),
                    "hadith_id": self.hadith,
                    "collection_id": collection,
                    "language": "ar",
                    "source_ordinal": 0,
                    "source_number": "1",
                    "text": "نص اصطناعي للاختبار",
                    "normalized_text": "نص اصطناعي للاختبار",
                    "original_data": {},
                    "source_file": "fixture.json",
                    "source_file_sha256": "0" * 64,
                    "created_at": now(),
                },
            )
            c.execute(
                insert(s.sources),
                {
                    "id": self.source,
                    "legacy_id": 1,
                    "reference_code": "TEST-1",
                    "kind": "image",
                    "created_at": now(),
                },
            )
        self.route = add_route(
            self.engine, self.hadith, "primary", "إسناد اصطناعي للاختبار"
        )

    def tearDown(self):
        self.engine.dispose()
        self.tmp.cleanup()

    def payload(self, key, finding="clear", route=None):
        layer = next(l for l in self.profile["definition"]["layers"] if l["key"] == key)
        facts = {k: "معلومة اصطناعية للاختبار" for k in layer["required_fields"]}
        if key == "quran_explicit":
            facts["apparent_conflict"] = finding in {"concern", "disputed"}
            facts["quran_passages"] = [
                {
                    "surah": 1,
                    "ayah": 1,
                    "text": "نص تجريبي لا يُنشر",
                    "checked_by": "مراجع الاختبار",
                    "checked_at": now(),
                }
            ]
        if key == "project_narrator_selection":
            facts["documented_tashayyu"] = False
        return {
            "scope": layer["scope"],
            "layer_code": layer["code"],
            "route_id": (route or self.route)["id"]
            if layer["scope"] == "route"
            else None,
            "finding": finding,
            "facts": facts,
            "evidence": [
                {
                    "source_id": self.source,
                    "quote": "اقتباس اصطناعي",
                    "locator": "موضع اختبار",
                    "checked_by": "مراجع الاختبار",
                    "checked_at": now(),
                }
            ],
            "reasoning": "تعليل اصطناعي للاختبار فقط",
            "review_state": "reviewed",
            "reviewer": "مراجع الاختبار",
            "reviewed_at": now(),
        }

    def observe(self, key, finding="clear", route=None):
        return add_observation(
            self.engine, self.profile, self.hadith, self.payload(key, finding, route)
        )

    def test_read_only_run_cannot_modify_database(self):
        readonly = open_database(Path(self.tmp.name) / "test.sqlite3", read_only=True)
        try:
            result = evaluate(readonly, self.profile, self.hadith, persist=False)
            self.assertEqual(result["outcome"], "needs_data")
            with readonly.begin() as conn, self.assertRaises(OperationalError):
                conn.exec_driver_sql("DELETE FROM research_hadiths")
            with self.engine.connect() as conn:
                self.assertEqual(
                    conn.scalar(select(func.count()).select_from(s.filter_runs)), 0
                )
        finally:
            readonly.dispose()

    def test_corpus_baseline_does_not_inflate_filtered_totals(self):
        with self.engine.begin() as conn:
            conn.execute(s.filter_routes.delete())
        evaluate(self.engine, self.profile, self.hadith)
        with self.engine.connect() as conn:
            progress = project_progress(conn)
        self.assertEqual(progress["counts"]["total"], 1)
        self.assertEqual(progress["counts"]["unreviewed"], 1)
        self.assertEqual(progress["counts"]["filtered"], 0)
        self.assertEqual(progress["records"], {})

    def test_corpus_review_and_book_require_human_decisions(self):
        self.observe("quran_explicit", "concern")
        evaluate(self.engine, self.profile, self.hadith)
        with self.engine.connect() as conn:
            progress = project_progress(conn)
        self.assertEqual(progress["counts"]["needs_review"], 1)
        self.assertEqual(progress["counts"]["filtered"], 1)
        self.assertEqual(progress["counts"]["accepted"], 0)
        assessment = uid("test-final-assessment")
        with self.engine.begin() as conn:
            conn.execute(
                insert(s.assessments),
                {
                    "id": assessment,
                    "hadith_id": self.hadith,
                    "methodology_version": "test",
                    "verdict": "accepted",
                    "reasoning": "قرار اصطناعي للاختبار",
                    "reviewer": "مراجع اختبار",
                    "reviewed_at": now(),
                    "created_at": now(),
                },
            )
            conn.execute(
                insert(s.book_entries),
                {
                    "id": uid("test-book-entry"),
                    "hadith_id": self.hadith,
                    "assessment_id": assessment,
                    "edition": "test",
                    "entry_number": 1,
                    "status": "approved",
                    "reviewer": "مراجع اختبار",
                    "reviewed_at": now(),
                    "created_at": now(),
                },
            )
        with self.engine.connect() as conn:
            progress = project_progress(conn)
        self.assertEqual(progress["counts"]["accepted"], 1)
        self.assertEqual(progress["counts"]["in_book"], 1)
        with self.engine.begin() as conn:
            conn.execute(
                insert(s.assessments),
                {
                    "id": uid("test-revised-assessment"),
                    "hadith_id": self.hadith,
                    "methodology_version": "test",
                    "verdict": "rejected",
                    "reasoning": "مراجعة اصطناعية لاحقة",
                    "reviewer": "مراجع اختبار",
                    "reviewed_at": now(),
                    "created_at": now(),
                },
            )
        with self.engine.connect() as conn:
            progress = project_progress(conn)
        self.assertEqual(progress["counts"]["accepted"], 0)
        self.assertEqual(progress["counts"]["rejected"], 1)
        self.assertEqual(progress["counts"]["in_book"], 0)

    def test_missing_data_is_not_acceptance(self):
        r = evaluate(self.engine, self.profile, self.hadith)
        self.assertEqual(r["summary"]["needs_data"], 22)
        self.assertEqual(r["outcome"], "needs_data")
        self.assertIsNone(r["final_verdict"])
        self.assertFalse(r["eligible_for_book"])
        self.assertEqual(r["blocking_layers"], [{"code": "L02", "state": "needs_data"}])
        with self.engine.connect() as c:
            self.assertEqual(
                c.scalar(select(func.count()).select_from(s.assessments)), 0
            )
            self.assertEqual(
                c.scalar(select(func.count()).select_from(s.book_entries)), 0
            )

    def test_quran_concern_cannot_be_outweighed_by_all_other_clear_layers(self):
        for l in self.profile["definition"]["layers"]:
            self.observe(
                l["key"], "concern" if l["key"] == "quran_explicit" else "clear"
            )
        r = evaluate(self.engine, self.profile, self.hadith)
        self.assertEqual(r["summary"]["clear"], 21)
        self.assertEqual(r["outcome"], "flagged")
        self.assertEqual(r["blocking_layers"], [{"code": "L02", "state": "flagged"}])
        self.assertFalse(r["eligible_for_book"])

    def test_foundational_layers_cannot_be_skipped(self):
        p = self.payload("quran_explicit", "not_applicable")
        with self.assertRaises(ValueError):
            add_observation(self.engine, self.profile, self.hadith, p)
        p = self.payload("quran_explicit")
        p["facts"].pop("resolution_reason")
        with self.assertRaises(ValueError):
            add_observation(self.engine, self.profile, self.hadith, p)
        p = self.payload("quran_explicit")
        p["facts"]["quran_passages"][0]["surah"] = 0
        with self.assertRaises(ValueError):
            add_observation(self.engine, self.profile, self.hadith, p)

    def test_proposed_interpretation_alone_cannot_clear_quran_concern(self):
        p = self.payload("quran_explicit")
        p["facts"]["apparent_conflict"] = True
        with self.assertRaises(ValueError):
            add_observation(self.engine, self.profile, self.hadith, p)
        p = self.payload("quran_explicit", "concern")
        p["facts"].pop("proposed_reconciliation")
        p["facts"].pop("reconciliation_evidence")
        add_observation(self.engine, self.profile, self.hadith, p)
        self.assertEqual(
            evaluate(self.engine, self.profile, self.hadith)["outcome"], "flagged"
        )

    def test_different_routes_do_not_cancel_each_other(self):
        other = add_route(self.engine, self.hadith, "second", "إسناد آخر اصطناعي")
        self.observe("continuity", "concern")
        self.observe("continuity", "clear", other)
        rows = [
            r
            for r in evaluate(self.engine, self.profile, self.hadith)["results"]
            if r["key"] == "continuity"
        ]
        self.assertEqual(
            {r["route_key"]: r["state"] for r in rows},
            {"primary": "flagged", "second": "clear"},
        )

    def test_conflict_remains_until_explicit_reviewed_revision(self):
        old = self.observe("quran_explicit", "concern")
        self.observe("quran_explicit", "clear")
        r = evaluate(self.engine, self.profile, self.hadith)
        self.assertEqual(r["outcome"], "disputed")
        p = self.payload("quran_explicit")
        p["supersedes"] = [old["id"]]
        add_observation(self.engine, self.profile, self.hadith, p)
        q = next(
            r
            for r in evaluate(self.engine, self.profile, self.hadith)["results"]
            if r["key"] == "quran_explicit"
        )
        self.assertEqual(q["state"], "clear")
        with self.engine.connect() as c:
            self.assertEqual(
                c.scalar(select(func.count()).select_from(s.filter_observations)), 3
            )

    def test_unreviewed_ocr_cannot_be_evidence(self):
        identifier = uid("fixture-ocr")
        with self.engine.begin() as c:
            c.execute(
                insert(s.extracts),
                {
                    "id": identifier,
                    "source_id": self.source,
                    "kind": "ocr_text",
                    "text": "خام",
                    "text_sha256": "1" * 64,
                    "ordinal": 0,
                    "review_state": "unverified",
                    "method": "fixture",
                    "created_at": now(),
                },
            )
        p = self.payload("quran_explicit")
        p["evidence"][0]["extract_id"] = identifier
        with self.assertRaises(ValueError):
            add_observation(self.engine, self.profile, self.hadith, p)

    def test_draft_cannot_clear_layer_and_run_is_reproducible(self):
        p = self.payload("quran_explicit")
        p["review_state"] = "draft"
        p["reviewer"] = None
        p["reviewed_at"] = None
        add_observation(self.engine, self.profile, self.hadith, p)
        r = evaluate(self.engine, self.profile, self.hadith)
        self.assertEqual(r["outcome"], "needs_data")
        self.assertEqual(r, evaluate(self.engine, self.profile, self.hadith))
        with self.engine.connect() as c:
            self.assertEqual(
                c.scalar(select(func.count()).select_from(s.filter_runs)), 1
            )

    def test_profile_version_is_immutable(self):
        p = Path(self.tmp.name) / "changed.json"
        d = json.loads(PROFILE_PATH.read_text())
        d["layers"][0]["title"] = "تغيير تجريبي"
        p.write_text(json.dumps(d))
        with self.assertRaises(ValueError):
            install_profile(self.engine, p)
        d["version"] += 1
        p.write_text(json.dumps(d))
        self.assertEqual(install_profile(self.engine, p)["version"], d["version"])

    def test_project_narrator_condition_is_route_specific(self):
        p = self.payload("project_narrator_selection")
        p["facts"]["documented_tashayyu"] = True
        with self.assertRaises(ValueError):
            add_observation(self.engine, self.profile, self.hadith, p)
        p["finding"] = "concern"
        add_observation(self.engine, self.profile, self.hadith, p)
        other = add_route(
            self.engine, self.hadith, "independent", "إسناد مستقل اصطناعي"
        )
        self.observe("project_narrator_selection", "clear", other)
        rows = [
            r
            for r in evaluate(self.engine, self.profile, self.hadith)["results"]
            if r["key"] == "project_narrator_selection"
        ]
        self.assertEqual(
            {r["route_key"]: r["state"] for r in rows},
            {"primary": "flagged", "independent": "clear"},
        )

    def test_route_must_belong_to_the_same_hadith(self):
        p = self.payload("continuity")
        p["route_id"] = uid("nonexistent-route")
        with self.assertRaises(ValueError):
            add_observation(self.engine, self.profile, self.hadith, p)

    def test_all_clear_under_draft_methodology_is_not_a_final_grade(self):
        for l in self.profile["definition"]["layers"]:
            self.observe(l["key"])
        r = evaluate(self.engine, self.profile, self.hadith)
        self.assertEqual(r["outcome"], "methodology_pending")
        self.assertEqual(r["summary"]["clear"], 22)
        self.assertIsNone(r["final_verdict"])
        self.assertFalse(r["eligible_for_book"])


if __name__ == "__main__":
    unittest.main()
