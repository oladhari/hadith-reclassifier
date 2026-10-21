"""Research catalogue CLI. Works without backend settings, credentials, or a running API."""

import argparse, json, sys, sqlite3, os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.research.catalogue import (
    DEFAULT_DB,
    ARCHIVE,
    open_database,
    initialize,
    import_all,
    audit,
    export_portable,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["import", "audit", "export", "project", "backup"]
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    engine = open_database(args.database)
    try:
        if args.command == "import":
            initialize(engine)
            result = import_all(engine, args.archive)
        elif args.command == "audit":
            result = audit(engine, args.archive)
        elif args.command == "backup":
            output = args.output or ROOT / "data/research/backups" / (
                "research-"
                + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                + ".sqlite3"
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.exists():
                raise RuntimeError("Backup destination already exists")
            with (
                sqlite3.connect(
                    f"file:{args.database.resolve()}?mode=ro", uri=True
                ) as original,
                sqlite3.connect(output) as backup,
            ):
                original.backup(backup)
                if backup.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise RuntimeError("Backup verification failed")
            os.chmod(output, 0o600)
            result = {"backup": str(output), "integrity": "ok"}
        elif args.command == "project":
            from app.research.projections import project_frontend

            result = project_frontend(
                engine, args.output or ROOT / "frontend/src/content"
            )
        else:
            result = export_portable(
                engine, args.output or ROOT / "data/research/export"
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command in ("import", "audit") and (
            result["integrity"] != "ok"
            or result["foreign_key_errors"]
            or result["missing_or_wrong_size_media"]
            or result["unmatched_hadith_texts"]
        ):
            return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
