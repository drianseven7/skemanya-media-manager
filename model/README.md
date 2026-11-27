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
2. Put approved plain-text files in `dataset/raw/` (that folder is intentionally not populated).
3. Run `python prepare_data.py` to normalize, deduplicate, and build `dataset/processed/corpus.txt`.
4. Install dependencies: `pip install -r requirements.txt`.
5. Train a SentencePiece tokenizer: `python train_tokenizer.py`.
6. Train model weights from random initialization: `python train.py`.
7. Evaluate factuality, Indonesian fluency, safety, memorization, and editorial performance before considering deployment.

## Persona and response style
The intended assistant persona is defined in `PERSONA.md`: natural Indonesian, witty and sarcastic, direct, critical, and useful. Sarcasm must target ideas or decisions rather than a person's identity or dignity. In sensitive or high-stakes topics, the model should prioritize empathy and clarity. This persona requires instruction-tuning and application integration; the base pretraining script alone does not implement it.

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
- [ ] Approved training corpus collected.
- [ ] Tokenizer trained.
- [ ] Model trained from random initialization.
- [ ] Evaluation passed.
- [ ] Android conversion and device testing passed.
- [ ] One-package APK built and verified.
