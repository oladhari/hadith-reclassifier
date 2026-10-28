"""No database access, ingestion, writes or AI calls are made by these tests."""
import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with patch.dict("os.environ", {"DEBUG": "false"}):
    from app.core.config import settings
    from app.core.security import require_admin_api_key


class AdministrativeBoundary(unittest.TestCase):
    def setUp(self):
        self.previous = settings.ADMIN_API_KEY
        self.calls = 0
        app = FastAPI()

        @app.post("/protected", dependencies=[Depends(require_admin_api_key)])
        def protected():
            self.calls += 1
            return {"ok": True}

        self.client = TestClient(app)

    def tearDown(self):
        settings.ADMIN_API_KEY = self.previous

    def test_unconfigured_fails_closed(self):
        for key in ["", "weak"]:
            settings.ADMIN_API_KEY = SecretStr(key)
            self.assertEqual(self.client.post("/protected").status_code, 503)
        self.assertEqual(self.calls, 0)

    def test_missing_wrong_unicode_and_oversized_keys_do_not_enter_handler(self):
        settings.ADMIN_API_KEY = SecretStr("audit-fixture-only-not-a-production-key")
        for headers in [{}, {"X-Admin-Api-Key": "wrong"}, {"X-Admin-Api-Key": "a" * 257}]:
            self.assertEqual(self.client.post("/protected", headers=headers).status_code, 401)
        with self.assertRaises(HTTPException) as caught:
            require_admin_api_key("مفتاح غير صحيح")
        self.assertEqual(caught.exception.status_code, 401)
        self.assertEqual(self.calls, 0)

    def test_valid_key_enters_only_dummy_handler(self):
        settings.ADMIN_API_KEY = SecretStr("audit-fixture-only-not-a-production-key")
        self.assertEqual(self.client.post("/protected", headers={"X-Admin-Api-Key": settings.ADMIN_API_KEY.get_secret_value()}).status_code, 200)
        self.assertEqual(self.calls, 1)

    def test_all_real_post_routes_declare_auth_dependency(self):
        root = Path(__file__).resolve().parents[1] / "app/api/v1"
        guarded = []
        for path in root.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "post":
                        self.assertIn("Depends(require_admin_api_key)", ast.unparse(decorator))
                        guarded.append(node.name)
        self.assertEqual(sorted(guarded), ["bulk_classify", "classify_hadith", "ingest_hadiths"])


if __name__ == "__main__":
    unittest.main()
