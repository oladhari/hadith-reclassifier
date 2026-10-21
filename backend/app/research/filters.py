"""Offline, versioned research triage. Findings are reviewed assertions, not AI grades."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import insert, select

from . import schema as s
from .catalogue import digest, now, uid

ENGINE_VERSION = "research-triage-v2"
PROFILE_PATH = Path(__file__).parent / "methodologies/othmani-v2.json"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def nonempty(value):
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None and value != [] and value != {}


def install_profile(engine, path=PROFILE_PATH):
    definition = json.loads(Path(path).read_text())
    layers = definition["layers"]
    if (
        not layers
        or len({r["code"] for r in layers}) != len(layers)
        or len({r["key"] for r in layers}) != len(layers)
    ):
        raise ValueError("Layer codes and keys must be unique")
    if not any(r["key"] == "quran_explicit" and r.get("blocking") for r in layers):
        raise ValueError("The explicit Quran gate is required")
    for r in layers:
        if r["scope"] not in {"route", "report"} or not r["required_fields"]:
            raise ValueError("Invalid layer scope or required fields")
    if definition["status"] == "active":
        approval = definition.get("approval", {})
        if not approval.get("reviewer") or not approval.get("reviewed_at"):
            raise ValueError("An active methodology requires a named approval")
        if any(r["rule_status"] == "scope_pending" for r in layers):
            raise ValueError(
                "Resolve pending rule scopes in a new methodology version first"
            )
    sha = digest(canonical(definition))
    with engine.begin() as conn:
        old = (
            conn.execute(
                select(s.filter_profiles).where(
                    s.filter_profiles.c.profile_key == definition["key"],
                    s.filter_profiles.c.version == definition["version"],
                )
            )
            .mappings()
            .first()
        )
        if old:
            if old["definition_sha256"] != sha:
                raise ValueError(
                    "This methodology version is immutable; increment its version"
                )
            return dict(old)
        row = {
            "id": uid("filter-profile", definition["key"], definition["version"]),
            "profile_key": definition["key"],
            "version": definition["version"],
            "definition": definition,
            "definition_sha256": sha,
            "status": definition["status"],
            "created_at": now(),
        }
        conn.execute(insert(s.filter_profiles), row)
    return row


def get_hadith(conn, collection, number):
    row = (
        conn.execute(
            select(s.hadiths)
            .join(s.collections)
            .where(
                s.collections.c.slug == collection,
                s.hadiths.c.source_number == str(number),
            )
        )
        .mappings()
        .first()
    )
    if not row:
        raise ValueError("Hadith not found in the original local corpus")
    return dict(row)


def add_route(engine, hadith_id, route_key, isnad_text):
    if not route_key.strip() or not isnad_text.strip():
        raise ValueError("A route requires a stable key and its explicit isnad text")
    row = {
        "id": uid("filter-route", hadith_id, route_key),
        "hadith_id": hadith_id,
        "route_key": route_key,
        "isnad_text": isnad_text,
        "created_at": now(),
    }
    with engine.begin() as conn:
        old = (
            conn.execute(
                select(s.filter_routes).where(s.filter_routes.c.id == row["id"])
            )
            .mappings()
            .first()
        )
        if old:
            if old["isnad_text"] != isnad_text:
                raise ValueError(
                    "A route is immutable; add a distinct route key for a correction"
                )
            return dict(old)
        conn.execute(insert(s.filter_routes), row)
    return row


def validate_observation(conn, profile, row):
    layer = next(
        (r for r in profile["definition"]["layers"] if r["code"] == row["layer_code"]),
        None,
    )
    if (
        not layer
        or row["scope"] != layer["scope"]
        or row["profile_id"] != profile["id"]
    ):
        raise ValueError(
            "Observation does not belong to this methodology layer and scope"
        )
    if row["finding"] not in {"clear", "concern", "disputed", "not_applicable"} or row[
        "review_state"
    ] not in {"draft", "reviewed"}:
        raise ValueError("Invalid observation finding or review state")
    if row["scope"] == "route":
        route = (
            conn.execute(
                select(s.filter_routes).where(
                    s.filter_routes.c.id == row.get("route_id")
                )
            )
            .mappings()
            .first()
        )
        if not route or route["hadith_id"] != row["hadith_id"]:
            raise ValueError("Route belongs to another hadith or is missing")
    elif row.get("route_id") is not None:
        raise ValueError("Report-scoped findings cannot reference a single route")
    if not row["reasoning"].strip():
        raise ValueError("A finding requires a reason")
    if row["finding"] == "not_applicable" and layer["key"] in {
        "text_identity",
        "quran_explicit",
        "review",
    }:
        raise ValueError("This foundational layer cannot be skipped")
    if row["review_state"] == "reviewed":
        if not row.get("reviewer") or not row.get("reviewed_at"):
            raise ValueError("A reviewed observation requires a reviewer and date")
        datetime.fromisoformat(row["reviewed_at"])
        if not row["evidence"]:
            raise ValueError("A reviewed finding requires original-source evidence")
        required = (
            ["not_applicable_reason"]
            if row["finding"] == "not_applicable"
            else layer["required_fields"]
        )
        if layer["key"] == "quran_explicit":
            # An unresolved concern needs its own evidence, not a speculative defence.
            required = [
                k
                for k in required
                if k not in {"proposed_reconciliation", "reconciliation_evidence"}
            ]
        if any(not nonempty(row["facts"].get(k)) for k in required):
            raise ValueError(
                "Missing structured fields: "
                + ", ".join(k for k in required if not nonempty(row["facts"].get(k)))
            )
        if (
            layer["key"] == "project_narrator_selection"
            and row["finding"] != "not_applicable"
        ):
            if not isinstance(row["facts"]["documented_tashayyu"], bool):
                raise ValueError(
                    "Documented tashayyu must be an explicit checked boolean, not a keyword guess"
                )
            if row["facts"]["documented_tashayyu"] and row["finding"] == "clear":
                raise ValueError(
                    "The selected profile excludes this route; resolve the attribution or record the selection concern"
                )
        if layer["key"] == "quran_explicit":
            conflict = row["facts"]["apparent_conflict"]
            if not isinstance(conflict, bool):
                raise ValueError(
                    "Specify whether the comparison identifies an apparent conflict"
                )
            if row["finding"] == "clear" and conflict:
                resolution = row["facts"].get("reconciliation_review", {})
                if not all(
                    nonempty(resolution.get(k))
                    for k in ["reviewer", "reviewed_at", "reasoning"]
                ):
                    raise ValueError(
                        "A proposed interpretation cannot clear a Quran concern without an explicit reviewed resolution"
                    )
                if not all(
                    nonempty(row["facts"].get(k))
                    for k in ["proposed_reconciliation", "reconciliation_evidence"]
                ):
                    raise ValueError(
                        "The reviewed reconciliation requires its argument and evidence"
                    )
                datetime.fromisoformat(resolution["reviewed_at"])
            verses = row["facts"]["quran_passages"]
            if not isinstance(verses, list) or not verses:
                raise ValueError("Specify the exact Quran passage and its checked text")
            for v in verses:
                if (
                    not isinstance(v.get("surah"), int)
                    or not 1 <= v["surah"] <= 114
                    or not isinstance(v.get("ayah"), int)
                    or v["ayah"] < 1
                    or not all(v.get(k) for k in ["text", "checked_by", "checked_at"])
                ):
                    raise ValueError(
                        "A Quran comparison requires surah, ayah, checked text and verification attribution"
                    )
        for evidence in row["evidence"]:
            source = conn.execute(
                select(s.sources.c.id).where(
                    s.sources.c.id == evidence.get("source_id")
                )
            ).scalar()
            if not source or not all(
                evidence.get(k)
                for k in ["quote", "locator", "checked_by", "checked_at"]
            ):
                raise ValueError(
                    "Evidence needs an existing source, exact passage, location and checking attribution"
                )
            if evidence.get("extract_id"):
                extract = (
                    conn.execute(
                        select(s.extracts).where(
                            s.extracts.c.id == evidence["extract_id"]
                        )
                    )
                    .mappings()
                    .first()
                )
                if (
                    not extract
                    or extract["source_id"] != source
                    or extract["review_state"] not in {"verified", "visually_checked"}
                ):
                    raise ValueError(
                        "An unverified OCR extract cannot establish a finding"
                    )
    if row.get("supersedes"):
        if row["review_state"] != "reviewed":
            raise ValueError(
                "Only reviewed evidence can supersede an earlier observation"
            )
        for identifier in row["supersedes"]:
            old = (
                conn.execute(
                    select(s.filter_observations).where(
                        s.filter_observations.c.id == identifier
                    )
                )
                .mappings()
                .first()
            )
            if not old or any(
                old[k] != row.get(k)
                for k in ["hadith_id", "profile_id", "route_id", "scope", "layer_code"]
            ):
                raise ValueError(
                    "A revision can supersede only observations of the same layer, scope and route"
                )
    return layer


def add_observation(engine, profile, hadith_id, payload):
    row = {
        "id": uid("filter-observation", hadith_id, profile["id"], canonical(payload)),
        "hadith_id": hadith_id,
        "profile_id": profile["id"],
        "route_id": payload.get("route_id"),
        "scope": payload["scope"],
        "layer_code": payload["layer_code"],
        "finding": payload["finding"],
        "facts": payload.get("facts", {}),
        "evidence": payload.get("evidence", []),
        "supersedes": payload.get("supersedes", []),
        "reasoning": payload.get("reasoning", ""),
        "review_state": payload.get("review_state", "draft"),
        "reviewer": payload.get("reviewer"),
        "reviewed_at": payload.get("reviewed_at"),
        "created_at": now(),
    }
    with engine.begin() as conn:
        validate_observation(conn, profile, row)
        old = (
            conn.execute(
                select(s.filter_observations).where(
                    s.filter_observations.c.id == row["id"]
                )
            )
            .mappings()
            .first()
        )
        if old:
            return dict(old)
        conn.execute(insert(s.filter_observations), row)
    return row


def evaluate(engine, profile, hadith_id, persist=True):
    if digest(canonical(profile["definition"])) != profile["definition_sha256"]:
        raise ValueError("Methodology checksum mismatch")
    with engine.begin() as conn:
        text = conn.execute(
            select(s.hadith_texts.c.text).where(
                s.hadith_texts.c.hadith_id == hadith_id,
                s.hadith_texts.c.language == "ar",
            )
        ).scalar()
        if text is None:
            raise ValueError("Arabic original text is missing")
        routes = [
            dict(r)
            for r in conn.execute(
                select(s.filter_routes)
                .where(s.filter_routes.c.hadith_id == hadith_id)
                .order_by(s.filter_routes.c.id)
            ).mappings()
        ]
        observations = [
            dict(r)
            for r in conn.execute(
                select(s.filter_observations)
                .where(
                    s.filter_observations.c.hadith_id == hadith_id,
                    s.filter_observations.c.profile_id == profile["id"],
                )
                .order_by(s.filter_observations.c.id)
            ).mappings()
        ]
        for observation in observations:
            validate_observation(conn, profile, observation)
        superseded = {
            i
            for o in observations
            if o["review_state"] == "reviewed"
            for i in o["supersedes"]
        }
        active = [
            o
            for o in observations
            if o["id"] not in superseded and o["review_state"] == "reviewed"
        ]
        results = []
        for layer in profile["definition"]["layers"]:
            scopes = routes or [None] if layer["scope"] == "route" else [None]
            for route in scopes:
                rid = route["id"] if route else None
                facts = [
                    o
                    for o in active
                    if o["layer_code"] == layer["code"] and o["route_id"] == rid
                ]
                states = {o["finding"] for o in facts}
                if "disputed" in states or len(states) > 1:
                    state = "disputed"
                elif "concern" in states:
                    state = "flagged"
                elif states:
                    state = (
                        "not_applicable" if states == {"not_applicable"} else "clear"
                    )
                else:
                    state = "needs_data"
                results.append(
                    {
                        "code": layer["code"],
                        "key": layer["key"],
                        "title": layer["title"],
                        "scope": layer["scope"],
                        "route_id": rid,
                        "route_key": route["route_key"] if route else None,
                        "state": state,
                        "observation_ids": [o["id"] for o in facts],
                        "rule_status": layer["rule_status"],
                        "blocking": layer.get("blocking", False),
                        "missing_fields": layer["required_fields"] if not facts else [],
                    }
                )
        # A Quran concern cannot be outweighed by a clear chain or a numeric score.
        blockers = [
            r
            for r in results
            if r["blocking"] and r["state"] not in {"clear", "not_applicable"}
        ]
        states = {r["state"] for r in results}
        outcome = (
            "flagged"
            if "flagged" in states
            else "disputed"
            if "disputed" in states
            else "needs_data"
            if "needs_data" in states or not routes or not text.strip()
            else "methodology_pending"
            if profile["status"] != "active"
            or any(r["rule_status"] == "scope_pending" for r in results)
            else "ready_for_review"
        )
        report = {
            "engine_version": ENGINE_VERSION,
            "methodology": {
                "key": profile["profile_key"],
                "version": profile["version"],
                "status": profile["status"],
                "sha256": profile["definition_sha256"],
            },
            "hadith_id": hadith_id,
            "outcome": outcome,
            "final_verdict": None,
            "eligible_for_book": False,
            "routes_mapped": len(routes),
            "blocking_layers": [
                {"code": r["code"], "state": r["state"]} for r in blockers
            ],
            "results": results,
            "summary": {
                k: sum(r["state"] == k for r in results)
                for k in [
                    "clear",
                    "flagged",
                    "disputed",
                    "needs_data",
                    "not_applicable",
                ]
            },
        }
        snapshot = {
            "engine_version": ENGINE_VERSION,
            "methodology": profile["definition"],
            "routes": routes,
            "observations": observations,
            "text_sha256": digest(text),
        }
        sha = digest(canonical(snapshot))
        run_id = uid("filter-run", hadith_id, profile["id"], sha)
        report["run_id"] = run_id
        if persist:
            exists = conn.execute(
                select(s.filter_runs.c.id).where(s.filter_runs.c.id == run_id)
            ).scalar()
            if not exists:
                conn.execute(
                    insert(s.filter_runs),
                    {
                        "id": run_id,
                        "hadith_id": hadith_id,
                        "profile_id": profile["id"],
                        "input_sha256": sha,
                        "text_sha256": digest(text),
                        "snapshot": snapshot,
                        "report": report,
                        "outcome": outcome,
                        "created_at": now(),
                    },
                )
    return report
