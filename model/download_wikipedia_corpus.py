"""Download the rights-cleared Indonesian Wikipedia subset for a small prototype.

The upstream dataset is CC BY-SA 4.0. Review attribution and ShareAlike obligations
before commercial distribution. This script does not fetch news publisher text.
"""
from pathlib import Path
from urllib.request import Request, urlopen
import json

ROOT = Path(__file__).resolve().parent
URL = (
    "https://huggingface.co/datasets/apricitea/bahasa-indonesia-corpus/"
    "resolve/main/data/bahasa_wikipedia_ccbysa.jsonl"
)
RAW = ROOT / "dataset" / "raw"
OUT_TEXT = RAW / "wikipedia_id_ccbysa.txt"
OUT_ATTRIBUTION = RAW / "wikipedia_id_ccbysa_attribution.jsonl"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    request = Request(URL, headers={"User-Agent": "SKEMANYA-Model-Research/0.1"})
    with urlopen(request, timeout=60) as response:
        lines = response.read().decode("utf-8").splitlines()

    texts, attribution = [], []
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("source") != "wikipedia_id":
            continue
        if row.get("license") != "cc-by-sa-4.0":
            continue
        if row.get("rights_reviewed") is not True:
            continue
        text = str(row.get("text", "")).strip()
        if len(text) < 80:
            continue
        texts.append(text)
        attribution.append({
            "title": row.get("title"),
            "source_url": row.get("source_url"),
            "source_revision_id": row.get("source_revision_id"),
            "retrieved_at": row.get("retrieved_at"),
            "license": row.get("license"),
            "source": row.get("source"),
        })

    if not texts:
        raise SystemExit(
            "Tidak ada record yang lolos filter hak penggunaan. "
            "Periksa URL dan skema dataset terbaru; tidak ada data yang ditulis."
        )

    OUT_TEXT.write_text("\\n\\n".join(texts) + "\\n", encoding="utf-8")
    OUT_ATTRIBUTION.write_text(
        "\\n".join(json.dumps(x, ensure_ascii=False) for x in attribution) + "\\n",
        encoding="utf-8",
    )
    print(f"Record lolos filter: {len(texts)}")
    print(f"Teks: {OUT_TEXT}")
    print(f"Atribusi: {OUT_ATTRIBUTION}")
    print("Lisensi: CC BY-SA 4.0 — periksa kewajiban atribusi dan ShareAlike.")


if __name__ == "__main__":
    main()
