# Android inference handoff

The Android app will run the exact SKEMANYA Transformer exported from its own training checkpoint. ONNX Runtime is an inference library only; it is not a pretrained model and contributes no model weights.

## Export after a rights-approved training run

```bash
pip install onnx
python model/export_onnx.py \
  --checkpoint model/artifacts/skemanya-prototype.pt \
  --output model/artifacts/skemanya.onnx
```

The exporter refuses checkpoints that do not explicitly record
`initialized_from_pretrained_model: false`. It exports token IDs to logits
with dynamic batch and sequence dimensions. The model's configured context
length remains the upper bound.

## Remaining Android integration work

- Add the ONNX file and the matching SentencePiece tokenizer to the app's
  assets after a real checkpoint exists.
- Add an Android tokenizer implementation that reads the exact SentencePiece
  model; token IDs must match training exactly.
- Run greedy/top-k token generation against ONNX Runtime, with a strict
  context-length limit and cancellation support.
- Test memory, latency, thermal behavior, and APK size on the target realme 7.
- Do not enable chat or label the app offline-capable until these tests pass.

No model is bundled by this scaffold. An ONNX file exported from untrained
random weights is not a usable assistant.
