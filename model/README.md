# SKEMANYA Original Model — Research Scaffold

This directory is the beginning of a **from-scratch model research project**. It does not contain a trained model yet.

## Important distinction
- The Android app currently uses a third-party Qwen model. That is only the existing test engine.
- This directory defines a separate path to train SKEMANYA's own small language model: tokenizer and Transformer weights are initialized and trained from scratch.
- Do not describe the model as trained, production-ready, or suitable for Android until training, evaluation, conversion, and on-device tests have actually passed.

## First target
A small Indonesian-first decoder-only Transformer prototype. Initial defaults are intentionally modest and configurable; they are not a claim that this size will provide ChatGPT-level ability.

## Pipeline
1. Collect text that SKEMANYA owns or is explicitly licensed to use. Keep source, license, date, and permission records.
2. The current prototype seed includes Indonesian Wikipedia CC BY-SA 4.0 text with a per-record attribution manifest. Review attribution and ShareAlike obligations before commercial distribution.
3. Run \`python validate_corpus.py\` to verify every text record has matching source attribution and license metadata.
4. Run \`python prepare_data.py\` to normalize, deduplicate, and build \`dataset/processed/corpus.txt\`.
5. Install dependencies: \`pip install -r requirements.txt\`.
6. Train a SentencePiece tokenizer: \`python train_tokenizer.py\`.
7. Train model weights from random initialization: \`python train.py\`. The script now holds out a validation split and records train/validation loss.
8. Test local generation after a checkpoint exists: \`python generate.py --prompt "Jelaskan apa itu SKEMANYA."\`.
8. Run \`python train_instruct.py\` only after pretraining; the included 20 original examples are a tiny smoke-test seed and will overfit.
9. Expand and human-review instruction data, then evaluate factuality, Indonesian fluency, safety, memorization, and editorial performance before considering deployment.

## Additional corpus candidate: Indo4B
See \`dataset/INDO4B_REVIEW.md\`. Indo4B is large, but its license information is inconsistent across public sources. It is blocked from ingestion into commercial-intended training until clarified by the maintainers or rights holders.

## Additional corpus candidate: CommonLingua-Train
See `dataset/COMMONLINGUA_REVIEW.md`. It has per-row language, source, creator, identifier, and license metadata, so a filtered Indonesian subset may be auditable. It is not approved for training yet; first measure the Indonesian subset and review every source/license group. No CommonLingua text has been downloaded or ingested.

## Persona and response style
The intended assistant persona is defined in \`PERSONA.md\`: natural Indonesian, witty and sarcastic, direct, critical, and useful. Sarcasm must target ideas or decisions rather than a person's identity or dignity. In sensitive or high-stakes topics, the model should prioritize empathy and clarity. This persona requires instruction-tuning and application integration; the base pretraining script alone does not implement it.

## Data rules
- Do not scrape or ingest copyrighted articles/books without permission or a license that permits model training.
- Do not put personal, confidential, patient, account, or credential data in the corpus.
- Preserve a manifest of every source and its usage rights.
- A model trained on a small corpus will be limited; data quality and quantity matter.

## Hardware / cost
Training a useful language model from scratch requires substantial text and compute. This scaffold is free software, but it does not provide free GPU time or guarantee that a free notebook can finish training. No paid service is configured or authorized.

## Android packaging
The eventual Android target is a single install package containing both app and model. That work comes **after** a model exists and is converted to a runtime-compatible, quantized format. The current Qwen download flow has not been removed or silently relabeled.

## Current status
- [x] Separate model-development directory created in the existing repository.
- [x] Initial training pipeline scaffold added.
- [x] Small original instruction/persona seed set created (20 examples; smoke-test only).
- [x] Provenance-filtered Wikipedia subset downloaded and attribution validated (CC BY-SA 4.0; commercial-use review remains).
- [x] Initial tokenizer trained (prototype only; corpus is far too small for a capable LLM).
- [x] Python syntax and model smoke tests passed.
- [ ] Approved large-scale training corpus collected.
- [ ] Indo4B rights conflict resolved.
- [ ] Model trained from random initialization.
- [ ] Evaluation passed.
- [ ] Android conversion and device testing passed.
- [ ] One-package APK built and verified.
