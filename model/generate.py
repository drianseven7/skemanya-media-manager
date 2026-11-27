"""Run local text generation with a trained SKEMANYA prototype checkpoint."""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
import sentencepiece as spm
from model import SkemanyaLM

ROOT = Path(__file__).resolve().parent

@torch.no_grad()
def generate_tokens(model, tokens, max_new_tokens=120, temperature=0.8, top_k=40, eos_id=None):
    if temperature <= 0:
        raise ValueError("temperature harus lebih besar dari 0")
    model.eval()
    for _ in range(max_new_tokens):
        context = tokens[:, -model.context:]
        logits, _ = model(context)
        logits = logits[:, -1, :] / temperature
        if top_k and top_k > 0:
            k = min(top_k, logits.size(-1))
            values, _ = torch.topk(logits, k)
            logits[logits < values[:, [-1]]] = float("-inf")
        probabilities = torch.softmax(logits, dim=-1)
        next_token = torch.multinomial(probabilities, num_samples=1)
        tokens = torch.cat((tokens, next_token), dim=1)
        if eos_id is not None and bool((next_token == eos_id).all()):
            break
    return tokens

def main():
    parser = argparse.ArgumentParser(description="Generate text with SKEMANYA original prototype.")
    parser.add_argument("--prompt", required=True, help="Prompt berbahasa Indonesia.")
    parser.add_argument("--checkpoint", default=str(ROOT / "artifacts" / "skemanya-prototype.pt"))
    parser.add_argument("--tokenizer", default=str(ROOT / "artifacts" / "skemanya_id.model"))
    parser.add_argument("--max-new-tokens", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=40)
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    tokenizer_path = Path(args.tokenizer)
    if not checkpoint_path.is_file() or not tokenizer_path.is_file():
        raise SystemExit("Checkpoint/tokenizer belum tersedia. Model belum dilatih.")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    saved = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    cfg = saved["config"]
    sp = spm.SentencePieceProcessor(model_file=str(tokenizer_path))
    model = SkemanyaLM(
        vocab_size=saved["vocab_size"],
        width=cfg["width"],
        layers=cfg["layers"],
        heads=cfg["heads"],
        context=cfg["context"],
        dropout=cfg["dropout"],
    )
    model.load_state_dict(saved["model_state_dict"])
    model.to(device)
    prompt_ids = sp.encode(args.prompt)
    if not prompt_ids:
        prompt_ids = [sp.unk_id()]
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    output_ids = generate_tokens(
        model, input_ids, args.max_new_tokens, args.temperature, args.top_k, sp.eos_id()
    )
    print(sp.decode(output_ids[0].tolist()))

if __name__ == "__main__":
    main()