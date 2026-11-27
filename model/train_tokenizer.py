from pathlib import Path
import sentencepiece as spm

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "dataset" / "processed" / "corpus.txt"
OUT = ROOT / "artifacts"
VOCAB_SIZE = 8000


def main() -> None:
    if not CORPUS.exists():
        raise SystemExit("Corpus belum ada. Jalankan prepare_data.py terlebih dahulu.")
    OUT.mkdir(parents=True, exist_ok=True)
    spm.SentencePieceTrainer.train(
        input=str(CORPUS),
        model_prefix=str(OUT / "skemanya_id"),
        vocab_size=VOCAB_SIZE,
        model_type="bpe",
        character_coverage=0.9995,
        pad_id=0,
        unk_id=1,
        bos_id=2,
        eos_id=3,
        hard_vocab_limit=False,
    )
    print(f"Tokenizer tersimpan di: {OUT}")


if __name__ == "__main__":
    main()
