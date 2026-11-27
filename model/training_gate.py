import csv
import hashlib
import json
from datetime import date
from pathlib import Path, PurePosixPath

REQUIRED_MANIFEST_COLUMNS = {
    "source", "license", "commercial_use_allowed", "model_training_allowed",
    "privacy_review_passed", "reviewer", "review_date", "decision",
    "dataset_file", "sha256",
}


def _validate_manifest(approval_path: Path, manifest_value: str) -> Path:
    dataset_root = approval_path.parent.resolve()
    manifest_path = (dataset_root / manifest_value).resolve()
    if manifest_path != dataset_root and dataset_root not in manifest_path.parents:
        raise RuntimeError("Manifest sumber harus berada di dalam folder dataset proyek.")
    if not manifest_path.is_file():
        raise RuntimeError("Manifest sumber tidak ditemukan.")

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED_MANIFEST_COLUMNS.issubset(reader.fieldnames):
            raise RuntimeError("Kolom wajib manifest sumber belum lengkap, termasuk file dan SHA-256.")
        rows = list(reader)
    if not rows:
        raise RuntimeError("Manifest sumber belum berisi baris pemeriksaan.")

    approved_files = set()
    raw_root = (dataset_root / "raw").resolve()
    for number, row in enumerate(rows, start=2):
        required_true = (
            row.get("commercial_use_allowed", "").strip().lower() == "true"
            and row.get("model_training_allowed", "").strip().lower() == "true"
            and row.get("privacy_review_passed", "").strip().lower() == "true"
            and row.get("decision", "").strip().lower() == "approved"
        )
        if not required_true:
            raise RuntimeError(f"Manifest sumber baris {number} belum disetujui untuk penggunaan yang dicatat.")
        if not all(row.get(field, "").strip() for field in (
            "source", "license", "reviewer", "review_date", "dataset_file", "sha256"
        )):
            raise RuntimeError(f"Metadata wajib kosong pada manifest sumber baris {number}.")
        try:
            date.fromisoformat(row["review_date"].strip())
        except ValueError as exc:
            raise RuntimeError(f"Tanggal review tidak valid pada baris {number}; gunakan YYYY-MM-DD.") from exc

        relative = PurePosixPath(row["dataset_file"].strip())
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "raw":
            raise RuntimeError(f"Baris {number}: dataset_file harus menunjuk ke file di dataset/raw/.")
        data_path = (dataset_root / Path(*relative.parts)).resolve()
        if raw_root not in data_path.parents or not data_path.is_file():
            raise RuntimeError(f"Baris {number}: file korpus tidak ditemukan atau berada di luar dataset/raw/.")
        expected = row["sha256"].strip().lower()
        if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
            raise RuntimeError(f"Baris {number}: SHA-256 tidak valid.")
        actual = hashlib.sha256(data_path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Baris {number}: SHA-256 file korpus tidak cocok.")
        approved_files.add(data_path)

    actual_files = {p.resolve() for p in raw_root.rglob("*.txt")} if raw_root.exists() else set()
    unreviewed = actual_files - approved_files
    if unreviewed:
        names = ", ".join(str(p.relative_to(dataset_root)) for p in sorted(unreviewed))
        raise RuntimeError(f"TRAINING DIBLOKIR: ada file .txt tanpa review sumber: {names}")
    return manifest_path


def require_commercial_training_approval(path: Path) -> dict:
    """Validate a scoped training approval and every raw corpus file.

    Internal prototype training is allowed when explicitly approved, but it does
    not authorize commercial distribution or publication of derived weights.
    """
    path = Path(path)
    if not path.is_file():
        raise RuntimeError("TRAINING DIBLOKIR: TRAINING_APPROVAL.json belum tersedia.")
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"File persetujuan tidak valid: {exc}") from exc

    if approval.get("approved_for_training") is not True:
        raise RuntimeError("TRAINING DIBLOKIR: persetujuan training belum diberikan.")
    if not all(approval.get(field) for field in ("reviewer", "review_date", "source_manifest")):
        raise RuntimeError("TRAINING DIBLOKIR: reviewer, tanggal, dan manifest sumber wajib diisi.")
    try:
        date.fromisoformat(str(approval["review_date"]))
    except ValueError as exc:
        raise RuntimeError("Tanggal persetujuan tidak valid; gunakan YYYY-MM-DD.") from exc

    scope = approval.get("training_scope")
    commercial = approval.get("approved_for_commercial_use") is True
    if scope == "internal_prototype_only" and commercial:
        raise RuntimeError("Persetujuan internal tidak boleh sekaligus mengklaim izin distribusi komersial.")
    if scope == "commercial_release" and not commercial:
        raise RuntimeError("Distribusi komersial belum disetujui.")
    if scope not in {"internal_prototype_only", "commercial_release"}:
        raise RuntimeError("training_scope harus internal_prototype_only atau commercial_release.")

    _validate_manifest(path, str(approval["source_manifest"]))
    return approval
