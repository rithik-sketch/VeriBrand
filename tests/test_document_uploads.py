import ast
import json
import re
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = ROOT / "app.py"
SAMPLES = ROOT / "sample_uploads"


class Upload:
    def __init__(self, path):
        self.name = path.name
        self._data = path.read_bytes()

    def getvalue(self):
        return self._data


def load_app_functions():
    tree = ast.parse(APP_SOURCE.read_text(encoding="utf-8"))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if any(name in {"STOP", "ATTRIBUTE_GROUPS"} for name in names):
                selected.append(node)
        if isinstance(node, ast.FunctionDef) and node.name in {
            "tokens", "numbers", "attribute_groups", "claim_status",
            "extract_uploaded_text", "analyse"
        }:
            selected.append(node)
    namespace = {
        "re": re,
        "date": date,
        "BRAND": json.loads((ROOT / "brand_rules.json").read_text(encoding="utf-8")),
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(APP_SOURCE), "exec"), namespace)
    return namespace


class DocumentUploadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load_app_functions()
        cls.facts = json.loads((ROOT / "knowledge_base.json").read_text(encoding="utf-8"))

    def check_sample(self, filename, expected_kind, expected_text):
        text, kind = self.ns["extract_uploaded_text"](Upload(SAMPLES / filename))
        self.assertEqual(kind, expected_kind)
        self.assertIn(expected_text.lower(), text.lower())
        findings = self.ns["analyse"](text, self.facts)
        return text, findings

    def test_txt_product_name_and_guarantee(self):
        _, findings = self.check_sample("test_post.txt", "TXT", "Aqua Nest PureFlow")
        types = {item["type"] for item in findings}
        self.assertIn("Product naming", types)
        self.assertIn("Brand rule", types)

    def test_pdf_nine_stage_contradiction(self):
        _, findings = self.check_sample("test_ad.pdf", "PDF", "9-stage")
        statuses = [item.get("claim_status") for item in findings]
        self.assertIn("Contradicted", statuses)

    def test_docx_unsupported_purity_unverified(self):
        _, findings = self.check_sample("test_email.docx", "DOCX", "100% pure")
        statuses = [item.get("claim_status") for item in findings]
        self.assertIn("Unverified", statuses)


if __name__ == "__main__":
    unittest.main()
