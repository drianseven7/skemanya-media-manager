# CommonLingua-Train review — candidate, not approved

Status: **METADATA AUDIT COMPLETE; RIGHTS REVIEW REQUIRED; DO NOT INGEST**

## Dataset and audit findings
- Dataset: https://huggingface.co/datasets/PleIAs/CommonLingua-Train
- Audited split: `default/train`.
- Hugging Face precomputed statistics report **2,482,568 rows** and **29,247 Indonesian rows** (`lang=ind`).
- The metadata-only filter classified **19,247 Indonesian rows as CC-BY-SA**.
- **10,000 Indonesian rows remain unclassified** by the per-license filter. This may reflect missing or unindexed license metadata; it is not permission to use those rows.
- The same 19,247/10,000 split appears in the `open_type` count, but `open_type` values describe `Web` and `Open_Culture`, not legal licenses.
- Global license counts are dominated by CC-BY-SA, but those global counts must not be mistaken for Indonesian-only counts.
- Metadata audit artifact: https://github.com/drianseven7/skemanya-media-manager/actions/runs/45965984880 (artifact `commonlingua-indonesian-metadata-audit`).

## Interpretation and limitations
- The dataset has 351 language labels, 120 source labels, 14 license labels, and 2 `open_type` labels in its train split.
- The dataset is designed for language identification, not language-model pretraining. The Indonesian subset is small for pretraining a useful general-purpose assistant; text may be truncated to 512 bytes.
- The filter audit does not enumerate every Indonesian source/license combination. It samples at most one source label for each license category.
- No paragraph text was saved or ingested by this audit.
- The 10,000 unclassified rows must be excluded unless their source-level rights can be established independently.
- CC-BY-SA is not automatically non-commercial: it permits commercial reuse subject to attribution and ShareAlike conditions. Whether and how those obligations apply to model training, weights, and downstream outputs needs qualified rights review before commercial release.

## Required next steps before ingestion
1. Retrieve a complete Indonesian-only metadata inventory, including text-independent row identifiers, source, license, open_type, creator, collection, and date where available.
2. Resolve all 10,000 unclassified rows or exclude them.
3. Inspect representative records for every source/license combination, not only one sample per license.
4. Preserve source revision, dataset revision, row identifiers, attribution, license, download date, file hashes, and filtering code in a sidecar manifest.
5. Run duplicate, privacy, quality, and contamination checks.
6. Obtain documented rights approval before training intended for commercial use.

## Current decision
No CommonLingua text has been downloaded or added to the training corpus. The metadata audit is not legal approval. The training script remains blocked until `dataset/TRAINING_APPROVAL.json` is completed with documented approval for training and commercial use.

## Sources
- Dataset card and schema: https://huggingface.co/datasets/PleIAs/CommonLingua-Train
- Hugging Face Dataset Viewer filter documentation: https://huggingface.co/docs/dataset-viewer/en/filter
- Hugging Face Dataset Viewer statistics documentation: https://huggingface.co/docs/dataset-viewer/en/statistics

This is a technical rights-risk note, not legal advice.
