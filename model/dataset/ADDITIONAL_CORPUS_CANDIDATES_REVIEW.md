# Additional Indonesian Corpus Candidates — Rights Review

Status: research only. No text from these candidates has been downloaded, copied into the training corpus, or used for training.

Reviewed: 2026-11-27

## 1. Lyon28/Corpus-Indonesia

Dataset page: https://huggingface.co/datasets/Lyon28/Corpus-Indonesia

Observed metadata:
- Hugging Face labels the dataset `apache-2.0`.
- Dataset Viewer reports one train split with approximately 19.5 million rows.
- The visible examples contain long, encyclopedic paragraphs about Indonesia.

Decision: **HOLD — source provenance and license scope not established.**

The repository-level Apache-2.0 label is not, by itself, proof that every underlying text record is original or that the uploader has authority to license it. Before any use:
1. Inspect the dataset card, repository history, source URLs, and any upstream collection method.
2. Determine whether the texts are original, synthetic, public-domain, or derived from third-party copyrighted material.
3. Confirm that Apache-2.0 applies to the text records themselves, not only scripts or packaging.
4. Check factual quality, duplication, synthetic repetition, and privacy.
5. Record a source-level decision in `source_rights_review_template.csv`.

Do not download or ingest this dataset until the above checks are documented.

## 2. MEA Ecosystem Pustaka

Dataset page: https://huggingface.co/datasets/meaecosystem/pustaka

License file: https://huggingface.co/datasets/meaecosystem/pustaka/blob/main/LICENSE.md

Observed declarations in the repository's own license file:
- The curation/pipeline layer is offered under MEA Ecosystem Open License v1.0, with attribution and notice requirements.
- Raw text subsets retain their respective upstream terms.
- The license file identifies mixed sources, including Wikipedia ID (CC BY-SA/GFDL), CC-News/Common Crawl, Kaskus WebText (research-only source terms to be checked), Indo4B (declared CC0 through SEACrowd), and a separate Common Crawl WET-derived Indonesian corpus declared CC0 by the dataset maintainer.
- The same file warns that some subsets retain non-commercial or other upstream restrictions and says commercial users must check each subset.

Decision: **HOLD — subset-level allowlist required.**

Do not treat the top-level MEA-OL label as blanket permission for all raw text. A future review must isolate the exact subset and release version, inspect upstream terms, preserve required attribution, and exclude any subset with unresolved or non-commercial source terms. The maintainer's CC0 declaration for the direct Common Crawl WET subset is a candidate for further review, not an independent legal determination.

## Training gate

Neither candidate is approved by this document. Keep `dataset/TRAINING_APPROVAL.json` absent or unapproved until a qualified rights review and completed source manifest explicitly approve every included source for model training and intended commercial use.

No paid infrastructure or subscription is authorized by this review.
