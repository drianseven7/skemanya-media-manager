# SKEMANYA AI — Android Prototype

A separate native Android prototype. It does not replace the existing Cloudflare dashboard or Worker.

## Current build scope
- Native Android chat shell branded SKEMANYA AI.
- Google LiteRT-LM Kotlin Android API: 0.18.1.
- CPU backend for the initial compatibility pass.
- **Temporary test engine:** Qwen2.5-1.5B-Instruct LiteRT-LM Q8. This is a third-party model, not the original SKEMANYA model.
- The test model is downloaded once to app-specific external storage; it is not bundled into the APK.
- Expected test-model size: 1,597,931,520 bytes (about 1.6 GB).

## Build
The GitHub Actions workflow in `.github/workflows/android-local-ai.yml` builds a debug APK and uploads it as the `skemanya-local-ai-debug` artifact. This is an installable prototype build, not a production release.

## Device notes
The target device is a realme 7, Android 12, 8 GB RAM. The model/runtime combination still needs a real-device test. Speed, heat, and memory behavior on this device are not guaranteed. CPU mode is chosen first to avoid assuming a compatible GPU driver.

The first test-model download needs internet and about 1.6 GB of free storage. Once downloaded, text inference is on-device and does not use a Gemini API key or provider request quota.

## Original SKEMANYA model
The original decoder-only Transformer is a separate workstream. It has not been trained or converted for Android yet. Do not describe this prototype as running original SKEMANYA weights until a verified model checkpoint is exported and loaded.
