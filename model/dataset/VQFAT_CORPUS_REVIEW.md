# VQFat Indonesian Corpus review — conditional hold

Review date: 2026-11-27  
Dataset: https://huggingface.co/datasets/vickyfatrian/vqfat-indo-corpus  
Reviewed revision: `99ccc02` (dataset card revision shown on Hugging Face)  
Files listed: `cosmopedia_id.csv` (~582 MB), `aurora_prompt_dataset_combined.csv` (~7.65 MB)

## What the publisher says
The dataset card labels the dataset C-UDA and explicitly says the license permits AI/ML training, commercial applications, modifications, and derivatives, with attribution to Vicky Fatrian and citation of IndoMMLU for the Aurora subset. It describes `cosmopedia_id` as synthetic Indonesian text adapted from the Cosmopedia concept, and `aurora_prompt` as educational QA derived from IndoMMLU/Bospedia.

## Preliminary assessment
- `cosmopedia_id`: strongest current candidate for a small Indonesian-first pretraining experiment. It is the only subset considered here for potential pretraining.
- `aurora_prompt`: do not ingest yet. Its stated source chain includes IndoMMLU and Bospedia; the source-level permission and redistribution rights need independent verification.
- The C-UDA terms are summarized in the dataset card, but this review has not verified a separate canonical license text or obtained a direct rights-holder confirmation.
- A dataset-level license declaration does not by itself prove that every underlying source is covered by the publisher's grant.

## Decision
**CONDITIONAL HOLD — no download or training yet.**

Before approving `cosmopedia_id`, obtain and archive:
1. The full C-UDA license text/version applicable to revision `99ccc02`.
2. Written confirmation from the dataset publisher that they control or have permission to license the full `cosmopedia_id` text for commercial model training and distribution of resulting model weights.
3. A clear statement of whether the data is wholly synthetic and what source material, prompts, or teacher outputs were used to create it.
4. Any attribution/notice obligations and whether model weights or generated outputs carry restrictions.
5. A fixed revision identifier and SHA-256 for the downloaded file.

Until those checks are complete, keep the candidate outside `dataset/raw/`, the tokenizer corpus, and every training job. Do not use the Aurora subset as training data under this review.

## Sources
- Dataset card and license summary: https://huggingface.co/datasets/vickyfatrian/vqfat-indo-corpus
- File list and reported sizes: https://huggingface.co/datasets/vickyfatrian/vqfat-indo-corpus/tree/main
- Dataset card reports version 1.1 dated 2026-03-06 and revision `99ccc02`.

This is a technical intake review, not legal advice or a final rights determination.
