"""Report corpus size and exact duplicates; this does not approve data rights."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DIR = ROOT / "dataset" / "raw"


def audit(directory: Path):
    files = sorted(directory.rglob("*.txt")) if directory.exists() else []
    seen = {}
    rows = []
    total_bytes = total_chars = total_words = 0
    duplicates = []
    for path in files:
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        digest = hashlib.sha256(data).hexdigest()
        total_bytes += len(data)
        total_chars += len(text)
        total_words += len(text.split())
        if digest in seen:
            duplicates.append({"file": str(path), "duplicate_of": seen[digest], "sha256": digest})
        else:
            seen[digest] = str(path)
        rows.append({
            "file": str(path),
            "bytes": len(data),
            "characters": len(text),
            "words": len(text.split()),
            "sha256": digest,
        })
    return {
        "directory": str(directory),
        "file_count": len(files),
        "unique_file_count": len(seen),
        "duplicate_count": len(duplicates),
        "total_bytes": total_bytes,
        "total_characters": total_chars,
        "approx_words": total_words,
        "files": rows,
        "duplicates": duplicates,
        "rights_status": "not_assessed_by_this_tool",
        "training_status": "not_approved_by_this_tool",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--output", type=Path, default=ROOT / "dataset" / "corpus_audit.json")
    args = parser.parse_args()
    result = audit(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "file_count", "unique_file_count", "duplicate_count", "total_bytes",
        "total_characters", "approx_words", "rights_status", "training_status"
    )}, indent=2))


if __name__ == "__main__":
    main()
