# SKEMANYA AI — Android Local Runtime

This is a separate native Android companion app. It does not replace the existing Cloudflare dashboard or Worker.

## Runtime
- Google LiteRT-LM Kotlin Android API: 0.18.1
- CPU backend for the first compatibility pass
- Qwen2.5-1.5B-Instruct, LiteRT-LM Q8 model
- The model is downloaded once to app-specific external storage; it is not bundled into the APK.
- Expected model size: 1,597,931,520 bytes (about 1.6 GB).

## Build
The GitHub Actions workflow in `.github/workflows/android-local-ai.yml` builds a debug APK and uploads it as an artifact.

## Device notes
The target device in this project is a realme 7, Android 12, 8 GB RAM. The model/runtime combination still needs a real-device test. The published model benchmarks are from a much newer flagship device, so speed, heat, and memory behavior on realme 7 are not guaranteed. CPU mode is chosen first to avoid assuming the phone has a compatible OpenCL GPU driver.

The first model download needs internet and about 1.6 GB of free space. Once downloaded, text inference is on-device and does not use a Gemini API key or provider request quota.
