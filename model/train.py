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
}


def batches(ids, batch_size, context, device):
    max_start = len(ids) - context - 1
    if max_start < 1:
        raise ValueError("Korpus terlalu pendek untuk panjang context yang dipilih.")
    starts = torch.randint(max_start, (batch_size,))
    x = torch.stack([ids[i:i + context] for i in starts])
    y = torch.stack([ids[i + 1:i + context + 1] for i in starts])
    return x.to(device), y.to(device)


def main():
    if not CORPUS.exists() or not TOKENIZER.exists():
        raise SystemExit("Jalankan prepare_data.py dan train_tokenizer.py terlebih dahulu.")

    OUT.mkdir(parents=True, exist_ok=True)
    sp = spm.SentencePieceProcessor(model_file=str(TOKENIZER))
    ids = torch.tensor(sp.encode(CORPUS.read_text(encoding="utf-8")), dtype=torch.long)
    if len(ids) < CONFIG["context"] + 2:
        raise SystemExit("Korpus terlalu kecil. Tambahkan data berizin sebelum training.")

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
    model.train()
    for step in range(1, CONFIG["steps"] + 1):
        x, y = batches(ids, CONFIG["batch_size"], CONFIG["context"], device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % CONFIG["eval_interval"] == 0:
            print(f"step {step}/{CONFIG['steps']} | loss {loss.item():.4f} | device {device}")

    checkpoint = {
        "model_state_dict": model.cpu().state_dict(),
        "config": CONFIG,
        "vocab_size": sp.get_piece_size(),
        "training_steps": CONFIG["steps"],
        "initialized_from_pretrained_model": False,
    }
    torch.save(checkpoint, OUT / "skemanya-prototype.pt")
    (OUT / "training_config.json").write_text(
        json.dumps(checkpoint["config"], indent=2), encoding="utf-8"
    )
    print(f"Checkpoint tersimpan: {OUT / 'skemanya-prototype.pt'}")


if __name__ == "__main__":
    main()
