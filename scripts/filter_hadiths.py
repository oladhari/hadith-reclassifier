#!/usr/bin/env python3
"""Local evidence-led filter workspace. No network, LLM calls or automatic hadith grades."""

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.research import schema
from app.research.catalogue import DEFAULT_DB, digest, initialize, open_database
from app.research.filters import (
    PROFILE_PATH,
    add_observation,
    add_route,
    canonical,
    evaluate,
    get_hadith,
    install_profile,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["init", "layers", "run", "route", "observe"]
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--profile", type=Path, default=PROFILE_PATH)
    parser.add_argument("--collection", default="bukhari")
    parser.add_argument("--number", default="1")
    parser.add_argument(
        "--data", type=Path, help="JSON observation or route {route_key,isnad_text}"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run and args.command != "run":
        parser.error("--dry-run is supported only for run")
    if args.dry_run and not args.database.exists():
        parser.error("Initialize a catalogue before a read-only dry run")
    engine = open_database(args.database, read_only=args.dry_run)
    try:
        if args.dry_run:
            definition = json.loads(args.profile.read_text())
            with engine.connect() as conn:
                row = (
                    conn.execute(
                        select(schema.filter_profiles).where(
                            schema.filter_profiles.c.profile_key == definition["key"],
                            schema.filter_profiles.c.version == definition["version"],
                        )
                    )
                    .mappings()
                    .first()
                )
            if not row or row["definition_sha256"] != digest(canonical(definition)):
                raise ValueError(
                    "Install this exact methodology version before a read-only dry run"
                )
            profile = dict(row)
        else:
            initialize(engine)
            profile = install_profile(engine, args.profile)
        if args.command in ["init", "layers"]:
            result = profile["definition"]
        else:
            with engine.connect() as conn:
                hadith = get_hadith(conn, args.collection, args.number)
            if args.command == "run":
                result = evaluate(
                    engine, profile, hadith["id"], persist=not args.dry_run
                )
            else:
                if not args.data:
                    parser.error("--data is required for route/observe")
                payload = json.loads(args.data.read_text())
                result = (
                    add_route(
                        engine,
                        hadith["id"],
                        payload["route_key"],
                        payload["isnad_text"],
                    )
                    if args.command == "route"
                    else add_observation(engine, profile, hadith["id"], payload)
                )
        content = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content)
            args.output.chmod(0o600)
            print(json.dumps({"output": str(args.output)}, ensure_ascii=False))
        else:
            print(content)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
