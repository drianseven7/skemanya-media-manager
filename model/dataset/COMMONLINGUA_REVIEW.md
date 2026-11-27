# CommonLingua-Train review — candidate, not approved

Status: **AUDIT IN PROGRESS; DO NOT INGEST INTO TRAINING**

## Why it is worth auditing
- Dataset: https://huggingface.co/datasets/PleIAs/CommonLingua-Train
- The dataset card exposes per-row `lang`, `source`, `identifier`, `license`, `open_type`, and `creator` metadata.
- It aggregates Wikipedia and other open-licensed/public-domain sources, but its license field is per-source and not one blanket license.
- The card asks downstream users to preserve per-row license, creator, and identifier metadata.

## Verified metadata-only result (2026-11-27)
- Hugging Face precomputed statistics report **2,482,568 rows** in the train split.
- The `lang=ind` count is **29,247 rows** (ISO 639-3 Indonesian).
- The train split has 351 language labels, 120 source labels, 14 license labels, and 2 `open_type` labels.
- The global license distribution is heavily dominated by CC-BY-SA, but that is an all-language aggregate and must not be treated as the Indonesian license breakdown.
- The actual `open_type` labels observed in global statistics are `Web` and `Open_Culture`; these are not license names. Do not use `open_type` as a substitute for `license`.
- Metadata-only audit artifact: GitHub Actions run https://github.com/drianseven7/skemanya-media-manager/actions/runs/45965522606 (artifact `commonlingua-indonesian-metadata-audit`).

## Important limitation
CommonLingua-Train was built for language identification, not Indonesian language-model pretraining. Its Indonesian subset is only 29,247 paragraphs in the train split. The text may be truncated to 512 bytes. It is a candidate source, not enough by itself to train a capable general-purpose assistant.

## Required conservative review
- Count Indonesian rows by exact per-row `license` value and `open_type`; do not infer Indonesian rights from all-language marginal counts.
- Inspect representative Indonesian records and source identifiers for every license/source combination.
- Exclude non-commercial, unknown, missing, ambiguous, or otherwise incompatible rights categories from commercial-intended training.
- Preserve original `license`, `open_type`, `creator`, `identifier`, `source`, `collection`, and `date` fields in a sidecar manifest.
- Preserve dataset revision, download date, file hashes, filtering code, and row counts.
- Run duplicate, personal-data, and content-quality checks.
- Obtain appropriate rights review before commercial release; a dataset card is evidence, not a blanket legal guarantee.

## Current decision
No CommonLingua text has been downloaded or added to the training corpus. The metadata-only audit does not approve any data for training. The next audit adds exact Indonesian counts per license and open_type. Source-level sampling and rights review must still follow.

## Sources
- Dataset card and schema: https://huggingface.co/datasets/PleIAs/CommonLingua-Train
- Hugging Face Dataset Viewer statistics documentation: https://huggingface.co/docs/dataset-viewer/en/statistics
- Hugging Face Dataset Viewer filter documentation: https://huggingface.co/docs/dataset-viewer/en/filter

This is a technical rights-risk note, not legal advice.
