from pathlib import Path
import argparse
import json
import torch
import sentencepiece as spm
from model import SkemanyaLM
from training_gate import require_commercial_training_approval

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "dataset" / "processed" / "corpus.txt"
TOKENIZER = ROOT / "artifacts" / "skemanya_id.model"
OUT = ROOT / "artifacts"

PROFILES = {
    # Small CPU-only feasibility experiment for free GitHub-hosted runners.
    # It is not a production model or a claim of assistant-level capability.
    "cpu-pilot": {
        "width": 96, "layers": 3, "heads": 4, "context": 128,
        "dropout": 0.1, "batch_size": 4, "steps": 300,
        "learning_rate": 0.0003, "eval_interval": 50,
        "eval_batches": 5, "validation_fraction": 0.05, "seed": 42,
    },
    "standard": {
        "width": 256, "layers": 6, "heads": 8, "context": 512,
        "dropout": 0.1, "batch_size": 8, "steps": 5000,
        "learning_rate": 0.0003, "eval_interval": 250,
        "eval_batches": 20, "validation_fraction": 0.05, "seed": 42,
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description="Train SKEMANYA from random initialization.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="cpu-pilot")
    parser.add_argument("--steps", type=int, default=None, help="Override profile step count.")
    parser.add_argument("--output-name", default="skemanya-prototype.pt")
    return parser.parse_args()


def checkpoint_metadata(checkpoint):
    """Return JSON-safe checkpoint information without tensor weights."""
    return {key: value for key, value in checkpoint.items() if key != "model_state_dict"}


def validate_output_name(value):
    """Reject paths and unsafe names; the output must be a plain .pt filename."""
    if not value.endswith(".pt") or value in {".pt", "..pt"} or "/" in value or "\\" in value:
        raise ValueError("--output-name harus nama file .pt tanpa folder.")
    return value


def batches(ids, batch_size, context, device):
    max_start = len(ids) - context - 1
    if max_start < 1:
        raise ValueError("Korpus terlalu pendek untuk panjang context yang dipilih.")
    starts = torch.randint(max_start, (batch_size,))
    x = torch.stack([ids[i:i + context] for i in starts])
    y = torch.stack([ids[i + 1:i + context + 1] for i in starts])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(model, train_ids, val_ids, config, device):
    model.eval()
    results = {}
    for name, split_ids in (("train", train_ids), ("validation", val_ids)):
        losses = []
        for _ in range(config["eval_batches"]):
            x, y = batches(split_ids, config["batch_size"], config["context"], device)
            _, loss = model(x, y)
            losses.append(loss.item())
        results[name] = sum(losses) / len(losses)
    model.train()
    return results


def main():
    args = parse_args()
    config = dict(PROFILES[args.profile])
    if args.steps is not None:
        if args.steps < 1 or args.steps > config["steps"]:
            raise SystemExit(f"--steps harus di antara 1 dan {config['steps']} untuk profile ini.")
        config["steps"] = args.steps
    try:
        validate_output_name(args.output_name)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    # Rights approval is deliberately checked before reading any training data.
    approval = require_commercial_training_approval(ROOT / "dataset" / "TRAINING_APPROVAL.json")
    if not CORPUS.exists() or not TOKENIZER.exists():
        raise SystemExit("Jalankan prepare_data.py dan train_tokenizer.py terlebih dahulu.")

    OUT.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(config["seed"])
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config["seed"])

    sp = spm.SentencePieceProcessor(model_file=str(TOKENIZER))
    ids = torch.tensor(sp.encode(CORPUS.read_text(encoding="utf-8")), dtype=torch.long)
    split_at = int(len(ids) * (1 - config["validation_fraction"]))
    train_ids, val_ids = ids[:split_at], ids[split_at:]
    minimum = config["context"] + 2
    if len(train_ids) < minimum or len(val_ids) < minimum:
        raise SystemExit("Korpus belum cukup untuk train/validation split.")

    # The free pilot intentionally uses CPU. No GPU/cloud service is provisioned.
    device = "cpu" if args.profile == "cpu-pilot" else ("cuda" if torch.cuda.is_available() else "cpu")
    model = SkemanyaLM(
        vocab_size=sp.get_piece_size(), width=config["width"],
        layers=config["layers"], heads=config["heads"],
        context=config["context"], dropout=config["dropout"],
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"])
    history = []
    model.train()

    for step in range(1, config["steps"] + 1):
        x, y = batches(train_ids, config["batch_size"], config["context"], device)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % config["eval_interval"] == 0 or step == config["steps"]:
            metrics = estimate_loss(model, train_ids, val_ids, config, device)
            metrics["step"] = step
            history.append(metrics)
            print(
                f"step {step}/{config['steps']} | train {metrics['train']:.4f} | "
                f"validation {metrics['validation']:.4f} | device {device}"
            )

    checkpoint = {
        "model_state_dict": model.cpu().state_dict(),
        "config": config,
        "profile": args.profile,
        "vocab_size": sp.get_piece_size(),
        "training_steps": config["steps"],
        "initialized_from_pretrained_model": False,
        "training_approval_reviewer": approval["reviewer"],
        "final_metrics": history[-1] if history else {},
    }
    torch.save(checkpoint, OUT / args.output_name)
    (OUT / "training_config.json").write_text(
        json.dumps(checkpoint_metadata(checkpoint), indent=2), encoding="utf-8"
    )
    (OUT / "training_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )
    print(f"Checkpoint tersimpan: {OUT / args.output_name}")


if __name__ == "__main__":
    main()
