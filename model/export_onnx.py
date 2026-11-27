"""Export a trained SKEMANYA checkpoint to ONNX for the Android runtime.

This exports only the project's own randomly initialized and trained architecture.
It does not download or convert any third-party model.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch

from model import SkemanyaLM

ROOT = Path(__file__).resolve().parent


def export_checkpoint(checkpoint_path: Path, output_path: Path, opset: int = 17) -> Path:
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"Checkpoint tidak ditemukan: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint.get("initialized_from_pretrained_model") is not False:
        raise RuntimeError("Ekspor ditolak: checkpoint tidak membuktikan inisialisasi dari bobot acak.")
    config = checkpoint["config"]
    model = SkemanyaLM(
        vocab_size=int(checkpoint["vocab_size"]),
        width=int(config["width"]),
        layers=int(config["layers"]),
        heads=int(config["heads"]),
        context=int(config["context"]),
        dropout=0.0,
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()

    class InferenceOnly(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, tokens):
            logits, _ = self.inner(tokens)
            return logits

    wrapper = InferenceOnly(model)
    sample = torch.ones((1, min(8, model.context)), dtype=torch.long)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        wrapper,
        (sample,),
        str(output_path),
        input_names=["tokens"],
        output_names=["logits"],
        dynamic_axes={
            "tokens": {0: "batch", 1: "sequence"},
            "logits": {0: "batch", 1: "sequence"},
        },
        opset_version=opset,
        do_constant_folding=True,
        dynamo=False,
    )
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Export SKEMANYA's own trained checkpoint to ONNX.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "artifacts" / "skemanya-prototype.pt")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "skemanya.onnx")
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()
    result = export_checkpoint(args.checkpoint, args.output, args.opset)
    print(f"ONNX tersimpan: {result} ({result.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
