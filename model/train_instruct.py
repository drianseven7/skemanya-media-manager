"""Small supervised fine-tuning stage for the SKEMANYA prototype.

Requires a from-scratch pretraining checkpoint and its SentencePiece tokenizer.
The included seed set is tiny and is only for pipeline smoke tests; it will
overfit and must not be treated as a capable assistant model.
"""
from pathlib import Path
import json
import torch
import sentencepiece as spm
from model import SkemanyaLM

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset" / "instruction_seed.jsonl"
TOKENIZER = ROOT / "artifacts" / "skemanya_id.model"
CHECKPOINT = ROOT / "artifacts" / "skemanya-prototype.pt"
OUT = ROOT / "artifacts" / "skemanya-instruct-prototype.pt"
STEPS = 300
BATCH_SIZE = 4
LEARNING_RATE = 0.00005


def load_examples(sp, context):
    examples = []
    for line in DATA.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        messages = row.get("messages", [])
        user = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
        assistant = next((m.get("content", "") for m in messages if m.get("role") == "assistant"), "")
        if not user or not assistant:
            continue
        prompt = sp.encode(f"<|user|>\\n{user}\\n<|assistant|>\\n")
        answer = sp.encode(assistant) + [sp.eos_id()]
        tokens = (prompt + answer)[: context + 1]
        if len(tokens) < 3:
            continue
        labels = tokens[1:].copy()
        first_answer_target = max(0, len(prompt) - 1)
        for i in range(min(first_answer_target, len(labels))):
            labels[i] = -100
        examples.append((tokens[:-1], labels))
    if not examples:
        raise SystemExit("Tidak ada contoh instruction yang valid.")
    return examples


def make_batch(examples, batch_size, context, pad_id, device):
    selected = [examples[i] for i in torch.randint(len(examples), (batch_size,)).tolist()]
    x = torch.full((batch_size, context), pad_id, dtype=torch.long)
    y = torch.full((batch_size, context), -100, dtype=torch.long)
    for row, (tokens, labels) in enumerate(selected):
        length = min(context, len(tokens))
        x[row, :length] = torch.tensor(tokens[:length], dtype=torch.long)
        y[row, :length] = torch.tensor(labels[:length], dtype=torch.long)
    return x.to(device), y.to(device)


def main():
    if not DATA.exists() or not TOKENIZER.exists() or not CHECKPOINT.exists():
        raise SystemExit(
            "Butuh instruction_seed.jsonl, tokenizer, dan checkpoint pretraining. "
            "Tahap SFT belum bisa dijalankan sebelum pretraining selesai."
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    sp = spm.SentencePieceProcessor(model_file=str(TOKENIZER))
    saved = torch.load(CHECKPOINT, map_location="cpu")
    cfg = saved["config"]
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
    examples = load_examples(sp, cfg["context"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    model.train()

    for step in range(1, STEPS + 1):
        x, y = make_batch(
            examples, BATCH_SIZE, cfg["context"], sp.pad_id(), device
        )
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % 50 == 0:
            print(f"SFT step {step}/{STEPS} | loss {loss.item():.4f}")

    torch.save(
        {
            "model_state_dict": model.cpu().state_dict(),
            "config": cfg,
            "vocab_size": saved["vocab_size"],
            "instruction_examples": len(examples),
            "initialized_from_pretrained_model": False,
            "warning": "Tiny seed set; prototype only, likely overfit.",
        },
        OUT,
    )
    print(f"Instruction checkpoint tersimpan: {OUT}")


if __name__ == "__main__":
    main()
