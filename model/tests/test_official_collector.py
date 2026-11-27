import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collect_official_legal_text import validate_url, safe_name


class OfficialCollectorTests(unittest.TestCase):
    def test_allows_official_https_pdf_host(self):
        parsed = validate_url("https://peraturan.bpk.go.id/Download/123/document.pdf")
        self.assertEqual(parsed.hostname, "peraturan.bpk.go.id")

    def test_rejects_non_https(self):
        with self.assertRaises(ValueError):
            validate_url("http://peraturan.bpk.go.id/document.pdf")

    def test_rejects_unapproved_host(self):
        with self.assertRaises(ValueError):
            validate_url("https://example.com/document.pdf")

    def test_rejects_credentials(self):
        with self.assertRaises(ValueError):
            validate_url("https://user:pass@jdih.anri.go.id/document.pdf")

    def test_safe_filename(self):
        self.assertEqual(safe_name("UU No. 1/2024"), "UU-No.-1-2024")


if __name__ == "__main__":
    unittest.main()
