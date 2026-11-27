# Indo4B dataset review — pending rights clearance

Status: **DO NOT INGEST INTO A COMMERCIAL TRAINING RUN YET**

## Why it is a candidate
- SEACrowd describes Indo4B as an Indonesian self-supervised pretraining corpus of about 3.6 billion words and 250 million sentences.
- The upstream IndoNLU project describes a 23 GB uncompressed / 5.6 GB compressed download and says Twitter data is excluded because of Twitter Developer Policy restrictions.

## License conflict requiring resolution
- The current SEACrowd dataset card labels the dataset CC0.
- The NusaCrowd paper's dataset table lists Indo4B (Wilie et al., 2020) as CC-BY-NC-SA 4.0.
- These statements conflict. A repository metadata label alone is not enough to resolve rights in a multi-source corpus.

## Decision
Do not download, ingest, or use Indo4B for any commercial-intended model training until the original dataset maintainers or rights holders clarify the applicable license for the exact downloadable release and its component sources in writing.

If clearance is obtained:
1. Record the exact source URL, version/commit, date, file hashes, license evidence, and maintainer response.
2. Preserve all source exclusions and restrictions, including the excluded Twitter data.
3. Keep the corpus and attribution/rights manifest together.
4. Run language, quality, duplication, and personal-data checks before training.

## Sources reviewed
- SEACrowd dataset card: https://huggingface.co/datasets/SEACrowd/indo4b
- SEACrowd license file: https://huggingface.co/datasets/SEACrowd/indo4b/blob/main/LICENSE
- NusaCrowd paper: https://aclanthology.org/2023.findings-acl.868v2.pdf
- Original IndoNLU repository: https://github.com/IndoNLP/indonlu

This is a technical rights-risk note, not legal advice.
