# SKEMANYA Original Language Model — Research Scaffold

This is the independent model-development workstream for SKEMANYA. The Android app does not call Gemini, download Qwen, or require another AI app.

## What exists today
- A decoder-only Transformer implementation in `model.py`, initialized from random weights.
- SentencePiece tokenizer preparation.
- Corpus normalization, provenance validation, deduplication, and audit scripts.
- A small Indonesian Wikipedia-derived prototype corpus with attribution metadata. Its CC BY-SA terms still require review before commercial use.
- A documented rights gate that blocks training until every source and exact dataset file has been reviewed and approved.

## What does not exist yet
- One internal CPU pilot has completed from random initialization: 300 steps, validation loss 13.42, checkpoint about 4.5 MB. This is a pipeline proof only, not assistant-quality.
- A longer 3,000-step CPU run and direct APK packaging are now configured; its quality must be measured before calling it usable.
- No Android inference engine for this exact Transformer architecture.
- No working AI chat in the APK yet.

The Android app now has an offline ONNX inference adapter and the matching pure-Java SentencePiece BPE tokenizer. The chat UI only activates when a matching ONNX model, tokenizer, and training configuration are bundled. The first 300-step model is not good enough for normal use; a longer run is in progress.

## Development sequence
1. Assemble a large Indonesian corpus from original SKEMANYA-authored material and sources whose terms explicitly permit model training and the intended distribution.
2. Record source, license, commercial-use permission, privacy review, reviewer, decision, file path, and SHA-256 for every training file.
3. Complete the approval manifest. Never invent approvals, reviewer identities, dates, licenses, or hashes.
4. Train the tokenizer and Transformer from random initialization; retain checkpoints and train/validation metrics.
5. Evaluate Indonesian fluency, instruction following, factuality, memorization, safety, and robustness. A tiny CPU pilot is only a pipeline test, not a usable assistant.
6. Implement an inference runtime for this exact architecture, export and quantize the trained weights, then test on the target Android device.
7. Bundle the verified SKEMANYA model with the native Android app and enable chat only after on-device tests pass.

## Training gate
`train.py` calls `training_gate.py` before reading the corpus. The current approval is explicitly limited to internal prototype training. It does not authorize commercial release or redistribution of model weights. Every raw text file must have a matching SHA-256 and source manifest. The Wikipedia attribution ledger is retained with the training artifact and must accompany any internal prototype APK.

## Cost and dependency policy
- No paid APIs, paid GPU, paid cloud training, or subscriptions are authorized.
- No third-party pretrained model may be substituted as the SKEMANYA model.
- Open-source libraries may be used as software tooling, but model weights must be trained from SKEMANYA's approved corpus and random initialization.
- If free compute is insufficient, pause and report the limitation rather than silently activating a paid service.

## Target app
The target is a standalone Android APK with the SKEMANYA model packaged inside it, fully usable offline. Packaging is conditional on a trained, evaluated, runtime-compatible model; do not promise a one-file APK before its actual size and device constraints are measured.


## Android inference export

`export_onnx.py` exports a verified from-scratch SKEMANYA checkpoint to ONNX for a future Android runtime. See `ANDROID_RUNTIME_HANDOFF.md`. Exporting does not create or train a model, and random weights are not useful assistant behavior.
