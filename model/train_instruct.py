"""Small supervised fine-tuning stage for the SKEMANYA prototype.

Requires a from-scratch pretraining checkpoint and its SentencePiece tokenizer.
The included seed set is tiny and only suitable for pipeline smoke tests.
"""
from pathlib import Path
import json

import sentencepiece as spm
import torch

from model import SkemanyaLM
from training_gate import require_commercial_training_approval

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset" / "instruction_seed.jsonl"
TOKENIZER = ROOT / "artifacts" / "skemanya_id.model"
CHECKPOINT = ROOT / "artifacts" / "skemanya-prototype.pt"
OUT = ROOT / "artifacts" / "skemanya-instruct-prototype.pt"
STEPS = 300
BATCH_SIZE = 4
LEARNING_RATE = 0.00005


def format_prompt(user: str) -> str:
    return f"<|user|>\n{user}\n<|assistant|>\n"


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

        prompt = sp.encode(format_prompt(user))
        # Keep at least one answer token inside the training window.
        if len(prompt) >= context:
            continue
        answer = sp.encode(assistant) + [sp.eos_id()]
        answer = answer[: context + 1 - len(prompt)]
        tokens = prompt + answer
        if len(answer) < 1 or len(tokens) < 2:
            continue

        labels = tokens[1:].copy()
        first_answer_target = len(prompt) - 1
        for i in range(first_answer_target):
            labels[i] = -100
        if all(label == -100 for label in labels):
            continue
        examples.append((tokens[:-1], labels))

    if not examples:
        raise SystemExit("Tidak ada contoh instruction yang muat di context dan memiliki target jawaban.")
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
    approval = require_commercial_training_approval(ROOT / "dataset" / "TRAINING_APPROVAL.json")

    if not DATA.exists() or not TOKENIZER.exists() or not CHECKPOINT.exists():
        raise SystemExit(
            "Butuh instruction_seed.jsonl, tokenizer, dan checkpoint pretraining. "
            "Tahap SFT belum bisa dijalankan sebelum pretraining selesai."
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    sp = spm.SentencePieceProcessor(model_file=str(TOKENIZER))
    saved = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
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
    loss_history = []

    for step in range(1, STEPS + 1):
        x, y = make_batch(examples, BATCH_SIZE, cfg["context"], sp.pad_id(), device)
        _, loss = model(x, y)
        if not torch.isfinite(loss):
            raise RuntimeError("Loss SFT tidak finite; hentikan training agar checkpoint tidak rusak.")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % 50 == 0 or step == STEPS:
            loss_history.append({"step": step, "loss": float(loss.item())})
            print(f"SFT step {step}/{STEPS} | loss {loss.item():.4f}")

    torch.save(
        {
            "model_state_dict": model.cpu().state_dict(),
            "config": cfg,
            "vocab_size": saved["vocab_size"],
            "instruction_examples": len(examples),
            "training_steps": STEPS,
            "final_loss": float(loss_history[-1]["loss"]),
            "initialized_from_pretrained_model": False,
            "training_approval_reviewer": approval["reviewer"],
            "training_scope": approval["training_scope"],
            "approved_for_commercial_use": approval["approved_for_commercial_use"],
            "warning": "Tiny seed set; prototype only, likely overfit.",
        },
        OUT,
    )
    (ROOT / "artifacts" / "instruction_training_history.json").write_text(
        json.dumps(loss_history, indent=2), encoding="utf-8"
    )
    print(f"Instruction checkpoint tersimpan: {OUT}")


if __name__ == "__main__":
    main()
