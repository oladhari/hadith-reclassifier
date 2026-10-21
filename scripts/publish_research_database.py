#!/usr/bin/env python3
"""Copy a verified research export into an empty, private Neon schema.

Credentials stay in the root .env. Originals and private discussion provenance
remain local; this imports the same curated catalogue used by public projections.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Json
from sqlalchemy import JSON, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.research import schema as s
from app.research.catalogue import open_database


def configuration(path):
    values = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


def fingerprint(rows):
    hashes = sorted(
        hashlib.sha256(
            json.dumps(
                row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        for row in rows
    )
    return hashlib.sha256("".join(hashes).encode()).hexdigest()


def validate_export(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    known = {t.name for t in s.metadata.sorted_tables}
    if not manifest["tables"] or not set(manifest["tables"]) <= known:
        raise ValueError("Unknown or empty export tables")
    for name, info in manifest["tables"].items():
        data = (directory / f"{name}.jsonl").read_bytes()
        if hashlib.sha256(data).hexdigest() != info["sha256"]:
            raise ValueError(f"Export checksum mismatch: {name}")
        if len(data.splitlines()) != info["rows"]:
            raise ValueError(f"Export count mismatch: {name}")
    return manifest


def verify(conn, directory, manifest):
    for name, info in manifest["tables"].items():
        expected = [
            json.loads(line)
            for line in (directory / f"{name}.jsonl").read_text().splitlines()
        ]
        actual = conn.execute(
            sql.SQL("SELECT * FROM research.{}").format(sql.Identifier(name))
        ).fetchall()
        if len(actual) != info["rows"] or fingerprint(actual) != fingerprint(expected):
            raise ValueError(f"Remote row verification failed: {name}")
    security = conn.execute(
        "SELECT count(*) AS n FROM pg_tables WHERE schemaname='research' AND NOT rowsecurity"
    ).fetchone()
    if security["n"]:
        raise ValueError("Research tables missing row-level security")


def sync_storage(conn):
    engine = open_database(ROOT / "data/research/research.sqlite3", read_only=True)
    try:
        with engine.connect() as local:
            rows = list(
                local.execute(
                    select(s.locations).where(
                        (s.locations.c.provider == "r2")
                        & (s.locations.c.state == "available")
                    )
                ).mappings()
            )
        cols = [c.name for c in s.locations.columns]
        assignments = sql.SQL(",").join(
            sql.SQL("{}=EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c))
            for c in cols
            if c != "id"
        )
        query = sql.SQL(
            "INSERT INTO research.research_storage_locations ({}) VALUES ({}) ON CONFLICT (id) DO UPDATE SET {}"
        ).format(
            sql.SQL(",").join(map(sql.Identifier, cols)),
            sql.SQL(",").join(sql.Placeholder() for _ in cols),
            assignments,
        )
        with conn.cursor() as cur:
            cur.executemany(query, [[r[c] for c in cols] for r in rows])
        print(json.dumps({"verified_storage_locations_synced": len(rows)}), flush=True)
    finally:
        engine.dispose()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--env-file", type=Path, default=ROOT / ".env")
    p.add_argument("--export-dir", type=Path, default=ROOT / "data/research/export")
    p.add_argument("--expected-host")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--verify-only", action="store_true")
    p.add_argument("--sync-storage", action="store_true")
    args = p.parse_args()
    os.umask(0o077)
    manifest = validate_export(args.export_dir)
    summary = {
        "tables": len(manifest["tables"]),
        "rows": sum(v["rows"] for v in manifest["tables"].values()),
    }
    if args.dry_run:
        print(json.dumps({"validated_export": summary}))
        return
    config = configuration(args.env_file)
    url = config.get("RESEARCH_POSTGRES_URL", "")
    parsed = urlparse(url)
    if not parsed.hostname or not parsed.hostname.endswith(".neon.tech"):
        raise ValueError("A dedicated Neon connection is required")
    if parsed.hostname != (args.expected_host or config.get("NEON_DATABASE_HOST")):
        raise ValueError("Connection does not match the selected Neon host")
    if (
        "sslmode=require" not in parsed.query
        and "sslmode=verify-full" not in parsed.query
    ):
        raise ValueError("Encrypted database connection required")
    with psycopg.connect(url, row_factory=dict_row, connect_timeout=30) as conn:
        if args.sync_storage:
            sync_storage(conn)
            return
        if not args.verify_only:
            existing = conn.execute(
                "SELECT 1 FROM pg_namespace WHERE nspname='research'"
            ).fetchone()
            if existing:
                raise ValueError(
                    "Research schema already exists; refusing overwrite. Use --verify-only."
                )
            conn.execute("CREATE SCHEMA research")
            conn.execute("REVOKE ALL ON SCHEMA research FROM PUBLIC")
            conn.execute("SET LOCAL search_path TO research, pg_catalog")
            for table in s.metadata.sorted_tables:
                conn.execute(
                    str(CreateTable(table).compile(dialect=postgresql.dialect()))
                )
                for index in sorted(table.indexes, key=lambda x: x.name):
                    conn.execute(
                        str(CreateIndex(index).compile(dialect=postgresql.dialect()))
                    )
                conn.execute(
                    sql.SQL("ALTER TABLE research.{} ENABLE ROW LEVEL SECURITY").format(
                        sql.Identifier(table.name)
                    )
                )
                if table.name not in manifest["tables"]:
                    continue
                columns = [c.name for c in table.columns]
                copy = sql.SQL("COPY research.{} ({}) FROM STDIN").format(
                    sql.Identifier(table.name),
                    sql.SQL(",").join(map(sql.Identifier, columns)),
                )
                with (
                    conn.cursor().copy(copy) as transfer,
                    (args.export_dir / f"{table.name}.jsonl").open() as source,
                ):
                    for line in source:
                        row = json.loads(line)
                        transfer.write_row(
                            [
                                Json(row[c.name])
                                if isinstance(c.type, JSON)
                                and (row[c.name] is not None or not c.nullable)
                                else row[c.name]
                                for c in table.columns
                            ]
                        )
                print(
                    json.dumps(
                        {
                            "imported": table.name,
                            "rows": manifest["tables"][table.name]["rows"],
                        }
                    ),
                    flush=True,
                )
            conn.execute("REVOKE ALL ON ALL TABLES IN SCHEMA research FROM PUBLIC")
        verify(conn, args.export_dir, manifest)
        size = conn.execute(
            "SELECT pg_database_size(current_database()) AS bytes"
        ).fetchone()["bytes"]
    summary.update(
        verified_at=datetime.now(UTC).isoformat(),
        database_bytes=size,
        project_id=config.get("NEON_PROJECT_ID"),
        state="verified",
    )
    report = ROOT / "data/research/neon-migration.json"
    report.write_text(json.dumps(summary, indent=2) + "\n")
    report.chmod(0o600)
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
