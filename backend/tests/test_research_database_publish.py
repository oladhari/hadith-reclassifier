"""Migration integrity guards; no network or database writes."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
try:
    from publish_research_database import fingerprint, validate_export
except ModuleNotFoundError as error:
    if error.name == "psycopg":
        raise unittest.SkipTest("Optional PostgreSQL publishing driver not installed")
    raise


class MigrationIntegrityTests(unittest.TestCase):
    def test_fingerprint_preserves_duplicates_and_values_but_ignores_order(self):
        rows = [{"id": 1, "text": "نص عربي"}, {"id": 2, "text": None}]
        self.assertEqual(fingerprint(rows), fingerprint(list(reversed(rows))))
        self.assertNotEqual(fingerprint(rows), fingerprint(rows + [rows[0]]))
        self.assertNotEqual(
            fingerprint(rows), fingerprint([{**rows[0], "text": "نص مختلف"}, rows[1]])
        )

    def test_export_tampering_is_rejected_before_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b'{"version":1,"applied_at":"2026-10-21"}\n'
            path = root / "research_schema_versions.jsonl"
            path.write_bytes(data)
            manifest = {
                "tables": {
                    "research_schema_versions": {
                        "rows": 1,
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                }
            }
            (root / "manifest.json").write_text(json.dumps(manifest))
            self.assertEqual(validate_export(root), manifest)
            path.write_bytes(data + data)
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                validate_export(root)

    def test_manifest_cannot_select_an_unrecognized_table(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(
                json.dumps({"tables": {"../other": {}}})
            )
            with self.assertRaisesRegex(ValueError, "Unknown or empty"):
                validate_export(root)


if __name__ == "__main__":
    unittest.main()
