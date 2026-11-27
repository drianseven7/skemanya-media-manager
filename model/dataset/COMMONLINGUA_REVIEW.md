# CommonLingua-Train review — candidate, not yet approved

Status: **PROMISING FOR A FILTERED INDONESIAN SUBSET; DO NOT INGEST YET**

## Why it is worth auditing
- Dataset: https://huggingface.co/datasets/PleIAs/CommonLingua-Train
- Dataset card describes 2,755,443 paragraphs across 351 language labels, with text, language, source, identifier, title, collection, license, open_type, creator, and date fields.
- The dataset card says it aggregates open-licensed and public-domain sources and explicitly instructs downstream users to retain per-row license, creator, and identifier metadata.
- This is better provenance structure than a corpus with only a repository-level license label.

## Important limitation
CommonLingua-Train was created for language identification, not Indonesian language-model pretraining. Its Indonesian subset may be much smaller than the full dataset, and paragraphs may be truncated to 512 bytes. The full 1.2 GB dataset must not be treated as 1.2 GB of Indonesian training text.

## Proposed conservative filter
Before any download or training run, inspect the actual row-level metadata and calculate counts/bytes for Indonesian rows (lang=ind) by open_type, license, and source.

For the first commercial-intended research subset:
- Include only rows explicitly marked public_domain or cc_by.
- Exclude cc_by_sa, cc_by_nc, cc_by_nc_sa, unknown, missing, and ambiguous rights categories until separately reviewed.
- Exclude rows without a usable source/identifier and creator where attribution is required.
- Keep the original license, open_type, creator, identifier, source, collection, and date fields in a sidecar manifest.
- Preserve the dataset version/commit, download date, file hashes, filtering code, and row counts.
- Run Indonesian-language quality checks, duplicate checks, personal-data checks, and source-specific restrictions.
- Obtain legal review before commercial release; a dataset card is evidence, not a blanket legal guarantee.

## Required audit before approval
1. Query the dataset viewer/API for lang=ind and record the exact number of rows.
2. Produce a grouped count and byte total by open_type, license, and source.
3. Inspect representative records from every proposed source/license group.
4. Confirm the source license permits the intended model-training use and preserve attribution requirements.
5. Add a deterministic downloader/filter with a machine-readable audit report only after the above checks pass.

## Current decision
This candidate is not approved for training yet. No CommonLingua data has been downloaded or added to the training corpus. The next safe engineering step is to build a metadata-only audit tool that reports the Indonesian subset and its license breakdown without writing training text.

## Sources reviewed
- Dataset card and schema: https://huggingface.co/datasets/PleIAs/CommonLingua-Train
- Dataset README and per-row license guidance: https://huggingface.co/datasets/PleIAs/CommonLingua-Train/blob/main/README.md
- Dataset files: https://huggingface.co/datasets/PleIAs/CommonLingua-Train/tree/main

This is a technical rights-risk note, not legal advice.