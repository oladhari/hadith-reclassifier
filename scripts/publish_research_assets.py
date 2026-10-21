#!/usr/bin/env python3
"""Publish this app's immutable evidence into its own public R2 prefix.
Reads credentials at runtime; never prints or persists credentials. Originals stay local.
"""

import argparse
import hashlib
import json
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[1]


def env_values(path):
    result = {}
    for line in path.read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", line)
        if m:
            result[m[1]] = m[2].strip().strip("\"'")
    return result


def checksum(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--credentials-file", type=Path, required=True)
    p.add_argument(
        "--database", type=Path, default=ROOT / "data/research/research.sqlite3"
    )
    p.add_argument(
        "--archive", type=Path, default=ROOT.parent / "telegram-archive/kkee9938"
    )
    p.add_argument("--prefix", default="othmani")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if not re.fullmatch(r"othmani(?:-[a-z0-9-]+)?", args.prefix):
        raise ValueError("Use an isolated Othmani prefix")
    values = env_values(args.credentials_file)
    if not all(
        values.get(k)
        for k in [
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_ENDPOINT",
            "R2_BUCKET",
            "R2_PUBLIC_URL",
        ]
    ):
        raise ValueError("Public storage configuration is incomplete")
    bucket = values["R2_BUCKET"]
    if "private" in bucket.lower() or bucket == values.get("R2_ARCHIVE_BUCKET"):
        raise ValueError("This publication must not use the private archive bucket")
    db = sqlite3.connect(args.database)
    db.row_factory = sqlite3.Row
    records = [
        dict(r)
        for r in db.execute("""select o.*,min(m.archive_relative_path) as local_path,min(m.legacy_id) as source_number
      from research_objects o join research_media m on m.object_id=o.id group by o.id order by o.byte_size""")
    ]
    if args.dry_run:
        print(
            json.dumps(
                {
                    "objects": len(records),
                    "bytes": sum(r["byte_size"] for r in records),
                    "corpus_files": 7,
                    "prefix": args.prefix,
                }
            )
        )
        return
    backup = (
        args.database.parent
        / "backups"
        / ("pre-publish-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".sqlite3")
    )
    with sqlite3.connect(backup) as target:
        db.backup(target)
    backup.chmod(0o600)
    client = boto3.client(
        "s3",
        endpoint_url=values["R2_ENDPOINT"],
        aws_access_key_id=values["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=values["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            retries={"mode": "standard", "max_attempts": 8},
        ),
    )
    transfer = TransferConfig(
        multipart_threshold=32 * 1024 * 1024,
        multipart_chunksize=32 * 1024 * 1024,
        max_concurrency=2,
    )

    def upload(path, key, sha, mime, size):
        try:
            existing = client.head_object(Bucket=bucket, Key=key)
        except ClientError as e:
            if e.response["Error"]["Code"] not in {"404", "NoSuchKey", "NotFound"}:
                raise
            existing = None
        if existing:
            if (
                existing["ContentLength"] != size
                or existing.get("Metadata", {}).get("sha256") != sha
            ):
                raise ValueError("Existing object differs; refusing overwrite: " + key)
            return "verified_existing"
        client.upload_file(
            str(path),
            bucket,
            key,
            ExtraArgs={
                "ContentType": mime,
                "CacheControl": "public, max-age=31536000, immutable",
                "Metadata": {"sha256": sha},
            },
            Config=transfer,
        )
        remote = client.head_object(Bucket=bucket, Key=key)
        if (
            remote["ContentLength"] != size
            or remote.get("Metadata", {}).get("sha256") != sha
        ):
            raise ValueError("Upload verification failed: " + key)
        return "uploaded"

    # The website build fetches public Arabic corpus files; no private database is uploaded.
    for name in [
        "bukhari",
        "muslim",
        "malik",
        "abudawud",
        "tirmidhi",
        "nasai",
        "ibnmajah",
    ]:
        path = ROOT / "data/hadiths" / f"ara-{name}.json"
        sha = checksum(path)
        state = upload(
            path,
            f"{args.prefix}/corpus/{path.name}",
            sha,
            "application/json; charset=utf-8",
            path.stat().st_size,
        )
        print(json.dumps({"corpus": name, "state": state}), flush=True)

    def publish(record):
        path = (args.archive / record["local_path"]).resolve()
        if not path.is_relative_to(args.archive.resolve()):
            raise ValueError("Invalid original path")
        if (
            path.stat().st_size != record["byte_size"]
            or checksum(path) != record["sha256"]
        ):
            raise ValueError("Original checksum mismatch")
        key = f"{args.prefix}/{record['object_key']}"
        state = upload(
            path, key, record["sha256"], record["mime_type"], record["byte_size"]
        )
        return record, key, state

    completed = 0
    total_bytes = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(publish, r) for r in records]
        for future in as_completed(futures):
            record, key, state = future.result()
            stamp = datetime.now(UTC).isoformat()
            with db:
                planned = db.execute(
                    "select id from research_storage_locations where object_id=? and provider='r2' order by state='planned' desc limit 1",
                    (record["id"],),
                ).fetchone()
                if not planned:
                    raise ValueError("Missing planned storage location")
                db.execute(
                    "update research_storage_locations set bucket=?,key=?,state='available',verified_at=? where id=?",
                    (bucket, key, stamp, planned["id"]),
                )
            completed += 1
            total_bytes += record["byte_size"]
            if completed % 20 == 0 or completed == len(records):
                print(
                    json.dumps(
                        {
                            "completed": completed,
                            "total": len(records),
                            "bytes": total_bytes,
                        }
                    ),
                    flush=True,
                )
    report = {
        "completed": completed,
        "bytes": total_bytes,
        "prefix": args.prefix,
        "verified_at": datetime.now(UTC).isoformat(),
    }
    out = args.database.parent / "hosting-assets.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    out.chmod(0o600)
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
