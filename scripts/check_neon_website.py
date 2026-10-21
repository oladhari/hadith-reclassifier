"""Check live read models and review transitions inside a rolled-back transaction."""

import json
import uuid
from pathlib import Path

import psycopg
from psycopg.types.json import Json
from publish_research_database import configuration

ROOT = Path(__file__).resolve().parents[1]
config = configuration(ROOT / ".env")

with psycopg.connect(config["RESEARCH_READ_DATABASE_URL"]) as reader:
    assert (
        reader.execute(
            "select sum(total) from research.website_corpus_counts"
        ).fetchone()[0]
        == 36390
    )
    assert (
        reader.execute("select count(*) from research.website_media").fetchone()[0]
        == 1907
    )
    assert reader.execute(
        "select has_table_privilege(current_user,'research.research_provenance','SELECT'),has_table_privilege(current_user,'research.research_assessments','INSERT')"
    ).fetchone() == (False, False)
    source = reader.execute(
        "select files,quotes from research.website_sources where id=195"
    ).fetchone()
    local = json.loads((ROOT / "frontend/src/content/local-sources.json").read_text())[
        "195"
    ]
    assert source == (local["files"], local["quotes"])

with psycopg.connect(config["RESEARCH_POSTGRES_URL"]) as conn:
    try:
        hid = conn.execute(
            "select id from research.website_hadiths where slug='bukhari' and source_number='1'"
        ).fetchone()[0]
        run = conn.execute(
            "select r.id from research.research_filter_runs r join research.research_filter_profiles p on p.id=r.profile_id where r.hadith_id=%s order by p.version desc,r.created_at desc,r.id desc limit 1",
            (hid,),
        ).fetchone()[0]

        def state():
            return conn.execute(
                "select status,filtered,in_book from research.website_hadiths where id=%s",
                (hid,),
            ).fetchone()

        assert state() == ("unreviewed", False, False), (
            "Missing-evidence baselines must not count as filtered"
        )
        conn.execute(
            "update research.research_filter_runs set report=%s where id=%s",
            (
                Json(
                    {
                        "results": [
                            {
                                "state": "flagged",
                                "observation_ids": ["transaction-only-check"],
                            }
                        ]
                    }
                ),
                run,
            ),
        )
        assert state() == ("needs_review", True, False)
        aid = str(uuid.uuid4())
        conn.execute(
            "insert into research.research_assessments (id,hadith_id,methodology_version,verdict,reasoning,reviewer,reviewed_at,created_at) values (%s,%s,'website-test','accepted','transaction-only check',' ','2050-01-01T00:00:00Z','2050-01-01T00:00:00Z')",
            (aid, hid),
        )
        assert state() == ("needs_review", True, False), (
            "Blank reviewers cannot approve"
        )
        conn.execute(
            "update research.research_assessments set reviewer='transaction-only check' where id=%s",
            (aid,),
        )
        assert state() == ("accepted", True, False)
        conn.execute(
            "insert into research.research_book_entries (id,hadith_id,assessment_id,edition,status,reviewer,reviewed_at,created_at,required_verdict) values (%s,%s,%s,%s,'approved','transaction-only check','2050-01-01T00:00:00Z','2050-01-01T00:00:00Z','accepted')",
            (str(uuid.uuid4()), hid, aid, "test-" + uuid.uuid4().hex),
        )
        assert state() == ("accepted", True, True)
        conn.execute(
            "insert into research.research_assessments (id,hadith_id,methodology_version,verdict,reasoning,reviewer,reviewed_at,created_at) values (%s,%s,'website-test','rejected','transaction-only check','transaction-only check','2051-01-01T00:00:00Z','2051-01-01T00:00:00Z')",
            (str(uuid.uuid4()), hid),
        )
        assert state() == ("rejected", True, False), (
            "Later rejection must remove book eligibility"
        )
    finally:
        conn.rollback()

print(
    "Website DB checks passed: live inventory, source albums, restricted reader, evidence/review/book transitions. All test mutations rolled back."
)
