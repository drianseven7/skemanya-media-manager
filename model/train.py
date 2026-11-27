from pathlib import Path
import json
import torch
import sentencepiece as spm
from model import SkemanyaLM

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "dataset" / "processed" / "corpus.txt"
TOKENIZER = ROOT / "artifacts" / "skemanya_id.model"
OUT = ROOT / "artifacts"
CONFIG = {
    "width": 256,
    "layers": 6,
    "heads": 8,
    "context": 512,
    "dropout": 0.1,
    "batch_size": 8,
    "steps": 5000,
    "learning_rate": 0.0003,
    "eval_interval": 250,
    "eval_batches": 20,
    "validation_fraction": 0.05,
    "seed": 42,
}


def batches(ids, batch_size, context, device):
    max_start = len(ids) - context - 1
    if max_start < 1:
        raise ValueError("Korpus terlalu pendek untuk panjang context yang dipilih.")
    starts = torch.randint(max_start, (batch_size,))
    x = torch.stack([ids[i:i + context] for i in starts])
    y = torch.stack([ids[i + 1:i + context + 1] for i in starts])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(model, train_ids, val_ids, device):
    model.eval()
    results = {}
    for name, split_ids in (("train", train_ids), ("validation", val_ids)):
        losses = []
        for _ in range(CONFIG["eval_batches"]):
            x, y = batches(split_ids, CONFIG["batch_size"], CONFIG["context"], device)
            _, loss = model(x, y)
            losses.append(loss.item())
        results[name] = sum(losses) / len(losses)
    model.train()
    return results


def main():
    if not CORPUS.exists() or not TOKENIZER.exists():
        raise SystemExit("Jalankan prepare_data.py dan train_tokenizer.py terlebih dahulu.")

    OUT.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(CONFIG["seed"])
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(CONFIG["seed"])

    sp = spm.SentencePieceProcessor(model_file=str(TOKENIZER))
    ids = torch.tensor(sp.encode(CORPUS.read_text(encoding="utf-8")), dtype=torch.long)
    split_at = int(len(ids) * (1 - CONFIG["validation_fraction"]))
    train_ids, val_ids = ids[:split_at], ids[split_at:]
    minimum = CONFIG["context"] + 2
    if len(train_ids) < minimum or len(val_ids) < minimum:
        raise SystemExit(
            "Korpus belum cukup untuk train/validation split. Tambahkan data berizin "
            "sebelum menjalankan training."
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SkemanyaLM(
        vocab_size=sp.get_piece_size(),
        width=CONFIG["width"],
        layers=CONFIG["layers"],
        heads=CONFIG["heads"],
        context=CONFIG["context"],
        dropout=CONFIG["dropout"],
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG["learning_rate"])
    history = []
    model.train()
    for step in range(1, CONFIG["steps"] + 1):
        x, y = batches(train_ids, CONFIG["batch_size"], CONFIG["context"], device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % CONFIG["eval_interval"] == 0:
            metrics = estimate_loss(model, train_ids, val_ids, device)
            metrics["step"] = step
            history.append(metrics)
            print(
                f"step {step}/{CONFIG['steps']} | "
                f"train {metrics['train']:.4f} | "
                f"validation {metrics['validation']:.4f} | device {device}"
            )

    checkpoint = {
        "model_state_dict": model.cpu().state_dict(),
        "config": CONFIG,
        "vocab_size": sp.get_piece_size(),
        "training_steps": CONFIG["steps"],
        "initialized_from_pretrained_model": False,
        "final_metrics": history[-1] if history else {},
    }
    torch.save(checkpoint, OUT / "skemanya-prototype.pt")
    (OUT / "training_config.json").write_text(
        json.dumps(checkpoint, indent=2), encoding="utf-8"
    )
    (OUT / "training_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )
    print(f"Checkpoint tersimpan: {OUT / 'skemanya-prototype.pt'}")


if __name__ == "__main__":
    main()
