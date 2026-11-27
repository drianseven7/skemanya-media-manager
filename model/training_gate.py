import csv
import json
from datetime import date
from pathlib import Path


REQUIRED_MANIFEST_COLUMNS = {
    "source",
    "license",
    "commercial_use_allowed",
    "model_training_allowed",
    "privacy_review_passed",
    "reviewer",
    "review_date",
    "decision",
}


def _validate_manifest(approval_path: Path, manifest_value: str) -> Path:
    manifest_path = (approval_path.parent / manifest_value).resolve()
    root = approval_path.parent.resolve()
    if manifest_path != root and root not in manifest_path.parents:
        raise RuntimeError("Manifest sumber harus berada di dalam folder dataset proyek.")
    if not manifest_path.is_file():
        raise RuntimeError("Manifest sumber tidak ditemukan.")
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED_MANIFEST_COLUMNS.issubset(reader.fieldnames):
            raise RuntimeError("Kolom wajib manifest sumber belum lengkap.")
        rows = list(reader)
    if not rows:
        raise RuntimeError("Manifest sumber belum berisi baris pemeriksaan.")
    for number, row in enumerate(rows, start=2):
        required_true = (
            row.get("commercial_use_allowed", "").strip().lower() == "true"
            and row.get("model_training_allowed", "").strip().lower() == "true"
            and row.get("privacy_review_passed", "").strip().lower() == "true"
            and row.get("decision", "").strip().lower() == "approved"
        )
        if not required_true:
            raise RuntimeError(
                f"Manifest sumber baris {number} belum disetujui untuk seluruh penggunaan."
            )
        if not all(row.get(field, "").strip() for field in ("source", "license", "reviewer", "review_date")):
            raise RuntimeError(f"Metadata wajib kosong pada manifest sumber baris {number}.")
        try:
            date.fromisoformat(row["review_date"].strip())
        except ValueError as exc:
            raise RuntimeError(f"Tanggal review tidak valid pada baris {number}; gunakan YYYY-MM-DD.") from exc
    return manifest_path


def require_commercial_training_approval(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise RuntimeError(
            "TRAINING DIBLOKIR: TRAINING_APPROVAL.json belum tersedia."
        )
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"File persetujuan tidak valid: {exc}") from exc

    required = (
        approval.get("approved_for_training") is True
        and approval.get("approved_for_commercial_use") is True
        and bool(approval.get("reviewer"))
        and bool(approval.get("review_date"))
        and bool(approval.get("source_manifest"))
    )
    if not required:
        raise RuntimeError(
            "TRAINING DIBLOKIR: butuh persetujuan training dan komersial, "
            "reviewer, tanggal review, serta manifest sumber."
        )
    try:
        date.fromisoformat(str(approval["review_date"]))
    except ValueError as exc:
        raise RuntimeError("Tanggal persetujuan tidak valid; gunakan YYYY-MM-DD.") from exc
    _validate_manifest(path, str(approval["source_manifest"]))
    return approval
