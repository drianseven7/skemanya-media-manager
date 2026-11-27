"""Validate corpus text against its retained per-record attribution manifest."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "dataset" / "raw"
TEXT = RAW / "wikipedia_id_ccbysa.txt"
MANIFEST = RAW / "wikipedia_id_ccbysa_attribution.jsonl"
REQUIRED = ("title", "source_url", "source_revision_id", "retrieved_at", "license", "source")


def main():
    if not TEXT.exists() or not MANIFEST.exists():
        raise SystemExit("Korpus/manifest belum ada. Jalankan download_wikipedia_corpus.py.")

    text_records = [
        item.strip()
        for item in TEXT.read_text(encoding="utf-8").split("\n\n")
        if item.strip()
    ]
    manifest_records = [
        json.loads(line)
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    errors = []
    if len(text_records) != len(manifest_records):
        errors.append(
            f"Jumlah teks ({len(text_records)}) tidak sama dengan manifest ({len(manifest_records)})."
        )

    seen = set()
    for index, row in enumerate(manifest_records, start=1):
        missing = [key for key in REQUIRED if not row.get(key)]
        if missing:
            errors.append(f"Record {index}: field atribusi kosong: {', '.join(missing)}")
        if row.get("license") != "cc-by-sa-4.0":
            errors.append(f"Record {index}: lisensi tidak sesuai.")
        if row.get("source") != "wikipedia_id":
            errors.append(f"Record {index}: sumber tidak sesuai.")
        url = str(row.get("source_url", ""))
        if not url.startswith("https://id.wikipedia.org/wiki/"):
            errors.append(f"Record {index}: URL sumber tidak valid.")
        key = (row.get("source_url"), row.get("source_revision_id"))
        if key in seen:
            errors.append(f"Record {index}: atribusi duplikat.")
        seen.add(key)

    if errors:
        for error in errors[:30]:
            print("ERROR:", error)
        raise SystemExit(f"Validasi gagal: {len(errors)} masalah.")

    print(f"Validasi lolos: {len(text_records)} teks dengan atribusi lengkap.")
    print("Lisensi dataset: CC BY-SA 4.0. Simpan atribusi dan tinjau kewajiban lisensi.")


if __name__ == "__main__":
    main()
