import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from download_vqfat_candidate import validate_approval


class VQFatDownloadGateTests(unittest.TestCase):
    def test_template_is_rejected(self):
        import json
        template = ROOT / "dataset" / "VQFAT_APPROVAL.template.json"
        with self.assertRaises(RuntimeError):
            validate_approval(json.loads(template.read_text(encoding="utf-8")))

    def test_wrong_revision_is_rejected(self):
        value = {
            "publisher_permission_confirmed": True,
            "full_license_archived": True,
            "synthetic_provenance_confirmed": True,
            "commercial_training_allowed": True,
            "reviewer": "Reviewer",
            "review_date": "2026-11-27",
            "revision": "main",
            "expected_sha256": "a" * 64,
        }
        with self.assertRaises(RuntimeError):
            validate_approval(value)

    def test_invalid_hash_is_rejected(self):
        value = {
            "publisher_permission_confirmed": True,
            "full_license_archived": True,
            "synthetic_provenance_confirmed": True,
            "commercial_training_allowed": True,
            "reviewer": "Reviewer",
            "review_date": "2026-11-27",
            "revision": "99ccc02",
            "expected_sha256": "not-a-hash",
        }
        with self.assertRaises(RuntimeError):
            validate_approval(value)


if __name__ == "__main__":
    unittest.main()
