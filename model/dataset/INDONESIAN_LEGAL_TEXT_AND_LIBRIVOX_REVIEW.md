# Candidate Corpus Review: Indonesian Public Legal Texts and LibriVox

Review date: 2026-11-27
Status: candidate research only. No data downloaded or added to training.

## Candidate A — Indonesian laws and regulations

Primary legal basis:
- Law No. 28 of 2014 on Copyright, Article 42(b), states that laws and regulations are not subject to copyright.
- Official text reference: https://jdih.bpk.go.id/File/Download/f9117084-0837-4ee8-80ff-23c1bd573815/uu%20no%2028%20tahun%202014.pdf
- WIPO Lex reference: https://www.wipo.int/wipolex/en/legislation/details/15600

Potential official discovery portal:
- JDIH ANRI: https://jdih.anri.go.id/
- Portal advertises free access to legal documents, regulations, decisions, articles, monographs, and historical documents.

Decision: **PROMISING CANDIDATE — NOT YET APPROVED FOR INGESTION.**

Scope should initially be limited to the official promulgated text of Indonesian statutes and regulations. Do not automatically include:
- explanatory notes, editorial commentary, annotations, legal articles, books, journal papers, or third-party summaries;
- scans or compilations where the publisher adds original protected material;
- unofficial translations;
- personal data or attachments that require separate privacy review.

Before ingestion:
1. Retrieve documents only from an official government JDIH or official gazette source.
2. Record issuing institution, regulation type/number/year, official source URL, publication date, current status, retrieval timestamp, and file hash.
3. Extract only the actual normative text; separate annexes and explanatory notes for individual review.
4. Check amendments, revocations, duplicates, OCR quality, and encoding.
5. Retain provenance for every document and the source URL in generated training records.
6. Have a qualified Indonesian copyright reviewer confirm the intended use and the treatment of source-site terms and database/compilation rights.

Important: Article 42 is a promising statutory basis for the text of laws and regulations. It is not a blanket permission for every file hosted by a government portal or every editorial/compiled element on a page.

Suggested domain coverage:
- constitutional and administrative law
- public information and government services
- education and research
- health and public health policy
- economics, taxation, and business regulation
- technology, telecommunications, and data protection
- environment, disaster management, and infrastructure

## Candidate B — LibriVox Indonesia transcripts

Dataset: https://huggingface.co/datasets/SEACrowd/librivox_indonesia
Additional release description: https://mozilladatacollective.com/datasets/cmwcnachv003007o1frm0lclz

Observed declaration:
- CC0 dataset license.
- About 8 hours across seven Indonesian languages, including Indonesian, Javanese, Sundanese, Balinese, Acehnese, Minangkabau, and Buginese.
- Audio and aligned text are intended for speech recognition; source books are described as public-domain audiobooks.

Decision: **LIMITED CANDIDATE — VERIFY TEXT/RELEASE PROVENANCE.**

Potential use:
- Consider only Indonesian-language transcript rows for text pretraining after verifying the exact source book, public-domain status, dataset version, and transcript release terms.
- Keep other regional languages in separate partitions; do not silently mix them into Indonesian-only training.
- Audio may be useful for a future speech feature but is out of scope for the current text-only model.
- This corpus is small and literary/older in style; it cannot serve as the primary general-purpose pretraining corpus.

## Current decision

Neither source is approved by this note. Do not create TRAINING_APPROVAL.json or begin pretraining based on this review alone. Complete the source-level rights manifest and quality/privacy checks first.

No paid services, subscriptions, or infrastructure are authorized.
