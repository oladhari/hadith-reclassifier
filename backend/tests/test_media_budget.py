"""The user-authorized additional spending limit must hold across workers."""
import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
try:
    import finish_media_catalogue as budget
except ModuleNotFoundError:
    budget = None


@unittest.skipIf(budget is None, "Optional media-processing dependencies are not installed")
class SpendingGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "budget.json"
        self.path.write_text(json.dumps({"limit_usd": .2, "spent_usd": 0, "reserved_usd": 0, "requests": []}))
        self.override = patch.object(budget, "BUDGET", self.path)
        self.override.start()
        self.addCleanup(self.override.stop)

    def request(self, client):
        return budget.BudgetResponses(client).create(model="gpt-5-mini", max_output_tokens=16000)

    def test_parallel_requests_cannot_exceed_authorized_amount(self):
        def response(**kwargs):
            return SimpleNamespace(id="synthetic", usage=SimpleNamespace(input_tokens=400000, output_tokens=16000))
        client = SimpleNamespace(responses=SimpleNamespace(create=response))
        def work(_):
            try:
                self.request(client)
                return True
            except budget.BudgetLimit:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            accepted = list(pool.map(work, range(30)))
        state = json.loads(self.path.read_text())
        self.assertEqual(sum(accepted), 1)
        self.assertLessEqual(state["spent_usd"] + state["reserved_usd"], .2)

    def test_unknown_network_outcome_keeps_full_cost_reservation(self):
        def response(**kwargs):
            raise TimeoutError("synthetic timeout")
        client = SimpleNamespace(responses=SimpleNamespace(create=response))
        with self.assertRaises(TimeoutError):
            self.request(client)
        state = json.loads(self.path.read_text())
        self.assertEqual(state["spent_usd"], .2)
        with self.assertRaises(budget.BudgetLimit):
            self.request(client)

    def test_other_model_cannot_bypass_pricing_guard(self):
        client = SimpleNamespace(responses=None)
        with self.assertRaises(ValueError):
            budget.BudgetResponses(client).create(model="other", max_output_tokens=100)
        self.assertEqual(json.loads(self.path.read_text())["spent_usd"], 0)


if __name__ == "__main__":
    unittest.main()
