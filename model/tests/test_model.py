import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model import SkemanyaLM
from training_gate import require_commercial_training_approval
from train_instruct import format_prompt, load_examples


class ModelSmokeTests(unittest.TestCase):
    def test_model_forward_and_loss(self):
        torch.manual_seed(7)
        model = SkemanyaLM(vocab_size=128, width=32, layers=2, heads=4, context=16, dropout=0.0)
        tokens = torch.randint(0, 128, (2, 12))
        logits, loss = model(tokens, tokens)
        self.assertEqual(tuple(logits.shape), (2, 12, 128))
        self.assertIsNotNone(loss)
        self.assertTrue(torch.isfinite(loss).item())

    def test_generation_respects_context_and_returns_tokens(self):
        from generate import generate_tokens
        torch.manual_seed(11)
        model = SkemanyaLM(vocab_size=32, width=16, layers=1, heads=2, context=8, dropout=0.0)
        prompt = torch.tensor([[1, 2, 3]], dtype=torch.long)
        output = generate_tokens(model, prompt, max_new_tokens=3, temperature=1.0, top_k=8)
        self.assertEqual(tuple(output.shape), (1, 6))
        self.assertTrue(torch.all(output[:, :3] == prompt).item())

    def test_context_limit_is_enforced(self):
        model = SkemanyaLM(vocab_size=64, width=32, layers=1, heads=4, context=8, dropout=0.0)
        with self.assertRaises(ValueError):
            model(torch.randint(0, 64, (1, 9)))

    def test_instruction_seed_is_valid_jsonl(self):
        path = ROOT / "dataset" / "instruction_seed.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(rows), 20)
        for row in rows:
            self.assertTrue(row.get("id"))
            roles = {m.get("role") for m in row.get("messages", [])}
            self.assertIn("user", roles)
            self.assertIn("assistant", roles)

    def test_training_gate_rejects_missing_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                require_commercial_training_approval(Path(directory) / "missing.json")

    def test_training_gate_rejects_unapproved_template(self):
        with self.assertRaises(RuntimeError):
            require_commercial_training_approval(ROOT / "dataset" / "TRAINING_APPROVAL.template.json")

    def _write_approval_fixture(self, root, extra_files=None):
        raw = root / "raw"
        raw.mkdir(parents=True)
        content = b"Original SKEMANYA text that has been reviewed and approved."
        source = raw / "owned.txt"
        source.write_bytes(content)
        manifest = (
            "source,license,commercial_use_allowed,model_training_allowed,privacy_review_passed,"
            "reviewer,review_date,decision,dataset_file,sha256\n"
            f"Original SKEMANYA text,Owned,true,true,true,Rights reviewer,2026-11-27,"
            f"approved,raw/owned.txt,{hashlib.sha256(content).hexdigest()}\n"
        )
        (root / "manifest.csv").write_text(manifest, encoding="utf-8")
        approval = {
            "approved_for_training": True, "approved_for_commercial_use": True,
            "reviewer": "Rights reviewer", "review_date": "2026-11-27",
            "source_manifest": "manifest.csv",
        }
        path = root / "approval.json"
        path.write_text(json.dumps(approval), encoding="utf-8")
        return path, source

    def test_training_gate_accepts_complete_approval_and_matching_file_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = self._write_approval_fixture(Path(directory))
            result = require_commercial_training_approval(path)
            self.assertTrue(result["approved_for_commercial_use"])

    def test_training_gate_rejects_file_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path, source = self._write_approval_fixture(Path(directory))
            source.write_text("Modified after review", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                require_commercial_training_approval(path)

    def test_training_gate_rejects_unreviewed_text_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = self._write_approval_fixture(Path(directory))
            (Path(directory) / "raw" / "unreviewed.txt").write_text("Unreviewed data", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "tanpa review sumber"):
                require_commercial_training_approval(path)

    def test_training_gate_rejects_manifest_with_unresolved_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.csv").write_text(
                "source,license,commercial_use_allowed,model_training_allowed,privacy_review_passed,"
                "reviewer,review_date,decision,dataset_file,sha256\n"
                "Unknown,Unknown,false,false,false,,,pending,raw/none.txt,0000000000000000000000000000000000000000000000000000000000000000\n",
                encoding="utf-8",
            )
            approval = {"approved_for_training": True, "approved_for_commercial_use": True,
                        "reviewer": "Reviewer", "review_date": "2026-11-27", "source_manifest": "manifest.csv"}
            path = root / "approval.json"
            path.write_text(json.dumps(approval), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                require_commercial_training_approval(path)

    def test_training_gate_rejects_missing_source_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "approval.json"
            path.write_text(json.dumps({
                "approved_for_training": True, "approved_for_commercial_use": True,
                "reviewer": "Reviewer", "review_date": "2026-11-27", "source_manifest": "missing.csv",
            }), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                require_commercial_training_approval(path)

    def test_instruction_prompt_uses_real_line_breaks(self):
        self.assertEqual(format_prompt("Halo"), "<|user|>\\nHalo\\n<|assistant|>\\n")

    def test_instruction_examples_keep_answer_targets_inside_context(self):
        class FakeSentencePiece:
            def encode(self, text):
                return list(range(1, len(text.split()) + 1))
            def eos_id(self):
                return 2

        examples = load_examples(FakeSentencePiece(), context=128)
        self.assertGreater(len(examples), 0)
        for tokens, labels in examples:
            self.assertEqual(len(tokens), len(labels))
            self.assertTrue(any(label != -100 for label in labels))
            self.assertLessEqual(len(tokens), 128)

    def test_persona_document_exists(self):
        self.assertTrue((ROOT / "PERSONA.md").is_file())


if __name__ == "__main__":
    unittest.main()
