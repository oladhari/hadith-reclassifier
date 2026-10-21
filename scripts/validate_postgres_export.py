"""Rehearse the portable export inside an explicitly named disposable PostgreSQL container.
This does not connect to Supabase or the application's existing database.
"""

import argparse, json, subprocess, uuid
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--container", required=True)
    p.add_argument("--export-dir", type=Path, required=True)
    args = p.parse_args()
    directory = args.export_dir
    manifest = json.loads((directory / "manifest.json").read_text())
    cmd = [
        "docker",
        "exec",
        "-i",
        args.container,
        "psql",
        "-U",
        "postgres",
        "-v",
        "ON_ERROR_STOP=1",
        "-q",
        "-t",
        "-A",
    ]
    schema = "validation_" + uuid.uuid4().hex

    def sql(text):
        r = subprocess.run(
            cmd,
            input=f'SET search_path TO "{schema}";\n' + text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if r.returncode:
            raise RuntimeError(r.stderr[-1500:])
        return r.stdout

    sql(f'CREATE SCHEMA "{schema}";')
    sql((directory / "postgresql-schema.sql").read_text())
    # The manifest table insertion order follows SQLAlchemy's FK dependency order.
    for name, info in manifest["tables"].items():
        rows = []
        count = 0
        with (directory / f"{name}.jsonl").open() as stream:
            for line in stream:
                rows.append(json.loads(line))
                if len(rows) == 500:
                    payload = json.dumps(rows, ensure_ascii=False)
                    tag = "$transfer_" + uuid.uuid4().hex + "$"
                    sql(
                        f'INSERT INTO "{name}" SELECT * FROM json_populate_recordset(NULL::"{name}", {tag}{payload}{tag}::json);'
                    )
                    count += len(rows)
                    rows = []
            if rows:
                payload = json.dumps(rows, ensure_ascii=False)
                tag = "$transfer_" + uuid.uuid4().hex + "$"
                sql(
                    f'INSERT INTO "{name}" SELECT * FROM json_populate_recordset(NULL::"{name}", {tag}{payload}{tag}::json);'
                )
                count += len(rows)
        result = sql(f'SELECT count(*) FROM "{name}";')
        actual = int(result.strip())
        if count != info["rows"] or actual != count:
            raise RuntimeError(f"Count mismatch in {name}")
    print(
        "PostgreSQL schema and full public export restored successfully. Private provenance was excluded."
    )


if __name__ == "__main__":
    main()
