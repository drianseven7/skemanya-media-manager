"""Extract text from manually collected regulation PDFs into a review-only candidate area."""
import json
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError as exc:
    raise SystemExit("Dependensi pypdf belum terpasang. Jalankan pip install -r model/requirements.txt.") from exc

ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "dataset" / "official_regulations_candidate"
PROVENANCE = CANDIDATES / "provenance.jsonl"
TEXT_OUT = CANDIDATES / "extracted_text"
MIN_TEXT_CHARS = 1000


def clean_text(value):
    value = value.replace("\x00", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def extract_record(record):
    pdf_path = CANDIDATES / record["file"]
    if not pdf_path.is_file():
        raise RuntimeError(f"PDF provenance tidak ditemukan: {record['file']}")
    reader = PdfReader(str(pdf_path), strict=False)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = clean_text("\n\n".join(pages))
    if len(text) < MIN_TEXT_CHARS:
        return None, "text_too_short_or_scanned_pdf"
    letters = sum(ch.isalpha() for ch in text)
    if letters / max(1, len(text)) < 0.35:
        return None, "low_text_quality"
    return text, "candidate_text_extracted"


def main():
    if not PROVENANCE.is_file():
        raise SystemExit("provenance.jsonl belum ada. Jalankan collector terlebih dahulu.")
    TEXT_OUT.mkdir(parents=True, exist_ok=True)
    records = [json.loads(line) for line in PROVENANCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    for record in records:
        text, status = extract_record(record)
        result = {
            "file": record["file"],
            "source_url": record["source_url"],
            "sha256": record["sha256"],
            "status": status,
            "training_approved": record.get("training_approved") is True,
        }
        if text:
            out_name = Path(record["file"]).stem + ".txt"
            (TEXT_OUT / out_name).write_text(text + "\n", encoding="utf-8")
            result.update({"text_file": out_name, "characters": len(text)})
            print(f"EXTRACTED {out_name}: {len(text):,} chars (candidate only)")
        else:
            print(f"SKIPPED {record['file']}: {status}")
        results.append(result)
    (TEXT_OUT / "extraction_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Extraction complete. No OCR and no model training performed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
