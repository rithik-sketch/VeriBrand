import ast
import json
import re
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = ROOT / "app.py"
FACTS = json.loads((ROOT / "knowledge_base.json").read_text(encoding="utf-8"))


def load_claim_functions():
    tree = ast.parse(APP_SOURCE.read_text(encoding="utf-8"))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if any(name in {"STOP", "ATTRIBUTE_GROUPS"} for name in names):
                selected.append(node)
        if isinstance(node, ast.FunctionDef) and node.name in {
            "tokens", "numbers", "attribute_groups", "claim_status"
        }:
            selected.append(node)
    namespace = {"re": re, "date": date}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(APP_SOURCE), "exec"), namespace)
    return namespace["claim_status"]


class ClaimStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claim_status = staticmethod(load_claim_functions())

    def assert_status(self, sentence, expected):
        actual = self.claim_status(sentence, FACTS)["status"]
        self.assertEqual(actual, expected, sentence)

    def test_seven_stage_supported(self):
        self.assert_status("AquaNest PureFlow includes a 7-stage filtration process.", "Supported")

    def test_nine_stage_contradicted(self):
        self.assert_status("AquaNest PureFlow includes a 9-stage filtration process.", "Contradicted")

    def test_five_litre_capacity_supported(self):
        self.assert_status("AquaNest PureFlow has a 5-litre storage capacity.", "Supported")

    def test_expired_warranty_outdated(self):
        self.assert_status("AquaNest PureFlow has a 2-year warranty.", "Outdated")

    def test_wrong_founding_year_contradicted(self):
        self.assert_status("AquaNest was founded in 2020.", "Contradicted")

    def test_unsupported_purity_claim_unverified(self):
        self.assert_status("AquaNest PureFlow removes 100% of all harmful chemicals.", "Unverified")


if __name__ == "__main__":
    unittest.main()
