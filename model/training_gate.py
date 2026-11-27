import json
from pathlib import Path


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
    return approval
