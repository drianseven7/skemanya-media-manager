from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "dataset" / "raw"
OUT_DIR = ROOT / "dataset" / "processed"
OUT_FILE = OUT_DIR / "corpus.txt"


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(RAW_DIR.rglob("*.txt"))
    seen = set()
    documents = []

    for path in files:
        # Exclude the generated processed corpus if it is ever placed under RAW_DIR.
        if path == OUT_FILE:
            continue
        text = normalize(path.read_text(encoding="utf-8", errors="replace"))
        if len(text) < 80:
            continue
        fingerprint = hash(text)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        documents.append(text)

    if not documents:
        raise SystemExit(
            "Belum ada korpus. Masukkan file .txt yang dimiliki/dilisensikan "
            "ke model/dataset/raw/ terlebih dahulu."
        )

    OUT_FILE.write_text("\n\n".join(documents) + "\n", encoding="utf-8")
    print(f"Dokumen diproses: {len(documents)}")
    print(f"Karakter korpus: {sum(map(len, documents)):,}")
    print(f"Output: {OUT_FILE}")


if __name__ == "__main__":
    main()
