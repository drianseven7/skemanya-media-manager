import json
import sys
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model import SkemanyaLM


class ModelSmokeTests(unittest.TestCase):
    def test_model_forward_and_loss(self):
        torch.manual_seed(7)
        model = SkemanyaLM(
            vocab_size=128, width=32, layers=2, heads=4, context=16, dropout=0.0
        )
        tokens = torch.randint(0, 128, (2, 12))
        logits, loss = model(tokens, tokens)
        self.assertEqual(tuple(logits.shape), (2, 12, 128))
        self.assertIsNotNone(loss)
        self.assertTrue(torch.isfinite(loss).item())


    def test_generation_respects_context_and_returns_tokens(self):
        from generate import generate_tokens

        torch.manual_seed(11)
        model = SkemanyaLM(
            vocab_size=32, width=16, layers=1, heads=2, context=8, dropout=0.0
        )
        prompt = torch.tensor([[1, 2, 3]], dtype=torch.long)
        output = generate_tokens(
            model, prompt, max_new_tokens=3, temperature=1.0, top_k=8
        )
        self.assertEqual(tuple(output.shape), (1, 6))
        self.assertTrue(torch.all(output[:, :3] == prompt).item())

    def test_context_limit_is_enforced(self):
        model = SkemanyaLM(
            vocab_size=64, width=32, layers=1, heads=4, context=8, dropout=0.0
        )
        tokens = torch.randint(0, 64, (1, 9))
        with self.assertRaises(ValueError):
            model(tokens)

    def test_instruction_seed_is_valid_jsonl(self):
        path = ROOT / "dataset" / "instruction_seed.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertGreaterEqual(len(rows), 20)
        for row in rows:
            self.assertTrue(row.get("id"))
            roles = {m.get("role") for m in row.get("messages", [])}
            self.assertIn("user", roles)
            self.assertIn("assistant", roles)

    def test_persona_document_exists(self):
        self.assertTrue((ROOT / "PERSONA.md").is_file())


if __name__ == "__main__":
    unittest.main()
