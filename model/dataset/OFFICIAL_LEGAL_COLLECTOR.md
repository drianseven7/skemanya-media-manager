# Official legal-text candidate collector

This is a cautious, manual, metadata-first collector. It is **not** a web crawler, legal opinion, training pipeline, or license approval.

## What it does
- Reads only rows in `official_regulations_manifest.csv` explicitly marked `collection_approved=true`.
- Accepts HTTPS URLs only from the allowlisted official domains: JDIH ANRI, Database Peraturan BPK, and peraturan.go.id.
- Re-checks redirect destinations, limits each PDF to 30 MB, verifies the PDF signature, and records SHA-256 plus provenance.
- Saves files under `official_regulations_candidate/` as candidate documents only.

## What it does not do
- It does not crawl portals or guess PDF URLs.
- It does not extract PDF text, OCR scans, create a training corpus, or start training.
- It does not treat free public download as permission for every downstream use.
- It does not treat `collection_approved` as `training_approved`.

## How to use
1. Review a specific regulation and its official source page.
2. Add its direct PDF URL and complete metadata to the CSV.
3. Set `official_status_checked=true` and `collection_approved=true` only after a human has verified the official document and its current status.
4. Leave `training_approved=false` until separate source-rights and commercial-use review is complete.
5. In GitHub, open Actions → **SKEMANYA collect approved legal candidates** → Run workflow.
6. Download the resulting artifact and review its provenance.

The collector intentionally does not put any document into the model's training path. The existing training approval gate remains mandatory.
