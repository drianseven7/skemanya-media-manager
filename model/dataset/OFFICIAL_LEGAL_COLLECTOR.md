# Official legal-text candidate collector

This is a cautious, manual, metadata-first collector and text extractor. It is **not** a web crawler, legal opinion, rights approval, or training pipeline.

## What it does
- Reads only rows in `official_regulations_manifest.csv` explicitly marked `collection_approved=true`.
- Accepts HTTPS URLs only from allowlisted official domains: JDIH ANRI, Database Peraturan BPK, and peraturan.go.id.
- Re-checks redirect destinations, limits each PDF to 30 MB, verifies the PDF signature, and records SHA-256 plus provenance.
- Extracts embedded PDF text using pypdf; it does not run OCR.
- Skips files with too little extractable text or poor text quality.
- Saves PDFs, text, and extraction report as review-only candidates.

## What it does not do
- It does not crawl portals or guess PDF URLs.
- It does not OCR scanned PDFs, create an approved training corpus, or start training.
- It does not treat free public download as permission for every downstream use.
- It does not treat `collection_approved` as `training_approved`.

## How to use
1. Review a specific regulation and its official source page.
2. Add its direct PDF URL and complete metadata to the CSV.
3. Set `official_status_checked=true` and `collection_approved=true` only after a human has verified the official document and its current status.
4. Leave `training_approved=false` until separate source-rights and commercial-use review is complete.
5. Open GitHub Actions → **SKEMANYA collect approved legal candidates**. The workflow runs on relevant changes to the Android branch; manual dispatch is also configured.
6. Download the resulting artifact and review its provenance and extraction report.

## Corpus size audit
Run `python model/audit_corpus.py` to count text files, words, bytes, and exact duplicates. This tool deliberately does not infer copyright permission or approve training.

All collected/extracted text remains outside the training corpus. The existing training approval gate remains mandatory.
