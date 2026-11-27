# SKEMANYA AI — Android App

Native Android application shell for SKEMANYA's independently developed language model.

## Non-negotiable project direction
- No Qwen, Gemini, or other third-party model is bundled, downloaded, or called by this Android app.
- No external AI app is required.
- No model download is required by this build.
- The app has no network permission and does not call a hosted AI API.
- Chat remains visibly unavailable until SKEMANYA's own model weights and an Android inference runtime are implemented and verified.

## Local inference runtime

The app now includes ONNX Runtime Android and a greedy autoregressive inference adapter for the project's exported Transformer. The adapter accepts a `TokenCodec` implementation so the exact matching SentencePiece tokenizer can be connected without substituting token IDs. No model or tokenizer assets are bundled yet, so chat remains disabled until a rights-approved checkpoint is trained, exported, packaged with its tokenizer, and device-tested.

## Current honest status
This build is the native app shell only. It is not yet an operating AI assistant. The separate `model/` directory contains the from-scratch Transformer training scaffold, but no trained checkpoint has been approved or produced. The app must not pretend that the untrained random-initialized network can answer users.

## Build
GitHub Actions workflow `.github/workflows/android-local-ai.yml` builds a debug APK artifact named `skemanya-local-ai-debug`.

## Next engineering stages
1. Complete corpus rights approval and assemble a sufficiently large Indonesian training corpus.
2. Train SKEMANYA weights from random initialization and evaluate them.
3. Implement/export a compatible on-device inference runtime for this exact architecture.
4. Package the quantized SKEMANYA weights inside the APK (or an explicitly chosen first-party install package) and verify fully offline on the target Android device.
5. Enable chat only after real inference tests pass.

No paid API, hosted model, paid GPU, or subscription is authorized.
