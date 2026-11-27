"""Download the pinned VQFat pretraining subset only after source-rights approval."""
import hashlib
import json
import sys
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
APPROVAL = DATASET / "VQFAT_APPROVAL.json"
OUTPUT = DATASET / "candidates" / "vqfat" / "cosmopedia_id.csv"
REVISION = "99ccc02"
URL = f"https://huggingface.co/datasets/vickyfatrian/vqfat-indo-corpus/resolve/{REVISION}/cosmopedia_id.csv?download=true"
MAX_BYTES = 700 * 1024 * 1024


def validate_approval(value):
    required_true = (
        value.get("publisher_permission_confirmed") is True
        and value.get("full_license_archived") is True
        and value.get("synthetic_provenance_confirmed") is True
        and value.get("commercial_training_allowed") is True
    )
    if not required_true:
        raise RuntimeError("Download diblokir: empat pemeriksaan hak sumber belum disetujui.")
    if value.get("revision") != REVISION:
        raise RuntimeError(f"Approval harus mengacu ke revision {REVISION}.")
    if not value.get("reviewer") or not value.get("review_date"):
        raise RuntimeError("Reviewer dan tanggal review wajib diisi.")
    date.fromisoformat(value["review_date"])
    digest = value.get("expected_sha256", "")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest.lower()):
        raise RuntimeError("expected_sha256 wajib berisi 64 karakter heksadesimal.")
    return digest.lower()


def download():
    if not APPROVAL.is_file():
        raise RuntimeError("Download diblokir: VQFAT_APPROVAL.json belum dibuat dari template setelah review hak.")
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    expected = validate_approval(approval)
    request = urllib.request.Request(URL, headers={"User-Agent": "SKEMANYA-Corpus-Intake/0.1"})
    digest = hashlib.sha256()
    total = 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".csv.part")
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as out:
            final = urlparse(response.geturl())
            host = (final.hostname or "").lower()
            allowed = host == "huggingface.co" or host.endswith(".huggingface.co") or host.endswith(".hf.co")
            if final.scheme != "https" or not allowed:
                raise RuntimeError("Redirect ke host yang tidak diizinkan.")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise RuntimeError("Ukuran dataset melewati batas 700 MiB.")
                digest.update(chunk)
                out.write(chunk)
        actual = digest.hexdigest()
        if actual != expected:
            raise RuntimeError(f"SHA-256 tidak cocok: expected {expected}, actual {actual}.")
        temporary.replace(OUTPUT)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    print(f"Candidate tersimpan: {OUTPUT} ({total:,} bytes; sha256={actual})")
    print("File tetap di folder candidates; belum menjadi data training.")


if __name__ == "__main__":
    try:
        download()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
