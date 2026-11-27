"""Collect manually approved official regulation PDFs as candidates; never trains on them."""
import csv
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "dataset" / "official_regulations_manifest.csv"
OUTPUT = ROOT / "dataset" / "official_regulations_candidate"
ALLOWED_HOSTS = {"peraturan.bpk.go.id", "jdih.anri.go.id", "peraturan.go.id", "www.peraturan.go.id"}
MAX_BYTES = 30 * 1024 * 1024
REQUIRED = {
    "source_url", "institution", "document_type", "document_number", "year",
    "title", "official_status_checked", "collection_approved", "training_approved",
    "reviewer", "review_date", "notes",
}


def validate_url(url):
    parsed = urllib.parse.urlparse(url.strip())
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("URL harus HTTPS dan berasal dari domain resmi yang diizinkan.")
    if parsed.username or parsed.password:
        raise ValueError("URL dengan kredensial tidak diizinkan.")
    return parsed


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def safe_name(value):
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned[:80] or "regulation"


def collect():
    if not MANIFEST.is_file():
        raise RuntimeError(f"Manifest tidak ditemukan: {MANIFEST}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise RuntimeError("Kolom manifest tidak lengkap.")
        rows = list(reader)

    records = []
    opener = urllib.request.build_opener(SafeRedirect())
    for line, row in enumerate(rows, start=2):
        if row.get("collection_approved", "").strip().lower() != "true":
            print(f"SKIP baris {line}: collection_approved bukan true")
            continue
        if row.get("official_status_checked", "").strip().lower() != "true":
            raise RuntimeError(f"Baris {line}: status dokumen resmi belum diperiksa.")
        if not all(row.get(k, "").strip() for k in ("institution", "document_type", "document_number", "year", "title", "reviewer", "review_date")):
            raise RuntimeError(f"Baris {line}: metadata wajib kosong.")
        validate_url(row["source_url"])
        request = urllib.request.Request(
            row["source_url"].strip(),
            headers={"User-Agent": "SKEMANYA-Research-Corpus/0.1 (manual-curated; contact: repository maintainer)"},
        )
        try:
            with opener.open(request, timeout=30) as response:
                final_url = response.geturl()
                validate_url(final_url)
                content_type = response.headers.get("Content-Type", "").lower()
                if "pdf" not in content_type and not final_url.lower().endswith(".pdf"):
                    raise RuntimeError(f"Baris {line}: respons bukan PDF ({content_type}).")
                data = response.read(MAX_BYTES + 1)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Baris {line}: unduhan gagal: {exc}") from exc
        if len(data) > MAX_BYTES:
            raise RuntimeError(f"Baris {line}: PDF melebihi batas {MAX_BYTES} byte.")
        if not data.startswith(b"%PDF-"):
            raise RuntimeError(f"Baris {line}: konten tidak memiliki signature PDF.")
        digest = hashlib.sha256(data).hexdigest()
        filename = f"{safe_name(row['document_type'])}-{safe_name(row['document_number'])}-{row['year']}-{digest[:12]}.pdf"
        (OUTPUT / filename).write_bytes(data)
        record = {
            "file": filename,
            "sha256": digest,
            "bytes": len(data),
            "source_url": row["source_url"].strip(),
            "final_url": final_url,
            "institution": row["institution"].strip(),
            "document_type": row["document_type"].strip(),
            "document_number": row["document_number"].strip(),
            "year": row["year"].strip(),
            "title": row["title"].strip(),
            "official_status_checked": True,
            "collection_reviewer": row["reviewer"].strip(),
            "collection_review_date": row["review_date"].strip(),
            "training_approved": row.get("training_approved", "").strip().lower() == "true",
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "stage": "candidate_only_not_training_data",
        }
        records.append(record)
        print(f"COLLECTED {filename} ({len(data)} bytes) — candidate only")

    manifest_out = OUTPUT / "provenance.jsonl"
    manifest_out.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in records), encoding="utf-8")
    print(f"Done: {len(records)} PDF candidate(s). No text extraction and no training performed.")
    return len(records)


if __name__ == "__main__":
    try:
        collect()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
