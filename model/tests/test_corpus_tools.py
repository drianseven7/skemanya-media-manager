import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit_corpus import audit
from extract_official_legal_text import clean_text


class CorpusToolTests(unittest.TestCase):
    def test_clean_text_removes_nulls_and_excess_whitespace(self):
        self.assertEqual(clean_text("A\x00  B\n\n\nC"), "A B\n\nC")

    def test_audit_counts_and_detects_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("teks contoh bahasa Indonesia", encoding="utf-8")
            (root / "b.txt").write_text("teks contoh bahasa Indonesia", encoding="utf-8")
            result = audit(root)
            self.assertEqual(result["file_count"], 2)
            self.assertEqual(result["unique_file_count"], 1)
            self.assertEqual(result["duplicate_count"], 1)
            self.assertEqual(result["rights_status"], "not_assessed_by_this_tool")


if __name__ == "__main__":
    unittest.main()
