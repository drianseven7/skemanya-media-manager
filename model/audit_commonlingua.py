#!/usr/bin/env python3
"""Fast metadata-only audit using Hugging Face precomputed split statistics.

No paragraph text is downloaded or saved. This reports marginal counts by
language, source, license and open_type; it does not provide cross-tab counts
or legal approval of any source.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET = "PleIAs/CommonLingua-Train"
BASE = "https://datasets-server.huggingface.co"
USER_AGENT = "SKEMANYA-Corpus-Audit/0.2 (metadata-only; no training ingestion)"


def get_json(endpoint: str, params: dict) -> dict:
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Dataset API HTTP {exc.code}: {body[:1200]}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Dataset API unavailable: {exc}") from exc


def main() -> int:
    splits_payload = get_json("splits", {"dataset": DATASET})
    available = splits_payload.get("splits", [])
    train_split = next((item for item in available if item.get("split") == "train"), None)
    if not train_split:
        raise RuntimeError("Split train tidak ditemukan; audit dihentikan.")

    config = train_split["config"]
    split = train_split["split"]
    payload = get_json(
        "statistics",
        {"dataset": DATASET, "config": config, "split": split},
    )
    if payload.get("partial") is True:
        raise RuntimeError("Statistik hanya mencakup sebagian data (partial=true).")
    columns = {
        item.get("column_name"): item
        for item in payload.get("statistics", [])
    }

    def frequencies(column: str) -> dict:
        item = columns.get(column)
        if not item:
            raise RuntimeError(f"Kolom statistik {column!r} tidak tersedia.")
        stats = item.get("column_statistics", {})
        values = stats.get("frequencies")
        if not isinstance(values, dict):
            raise RuntimeError(
                f"Kolom {column!r} tidak menyediakan frequency table; "
                "audit tidak akan menebak atau mengunduh korpus penuh."
            )
        return dict(sorted(values.items(), key=lambda pair: (-pair[1], pair[0])))

    language_counts = frequencies("lang")
    license_counts = frequencies("license")
    open_type_counts = frequencies("open_type")
    source_counts = frequencies("source")
    indonesian_rows = language_counts.get("ind", 0)

    report = {
        "dataset": DATASET,
        "config": config,
        "split": split,
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_rows_in_statistics": payload.get("num_examples"),
        "statistics_partial": payload.get("partial"),
        "indonesian_iso_639_3": "ind",
        "indonesian_rows": indonesian_rows,
        "unique_language_values": len(language_counts),
        "unique_source_values": len(source_counts),
        "unique_license_values": len(license_counts),
        "unique_open_type_values": len(open_type_counts),
        "counts_by_language": language_counts,
        "counts_by_license_all_languages": license_counts,
        "counts_by_open_type_all_languages": open_type_counts,
        "counts_by_source_all_languages": source_counts,
        "candidate_eligible_rows": None,
        "candidate_eligible_bytes": None,
        "cross_tab_available": False,
        "limitations": [
            "Counts by license, open_type and source are marginal across all languages, not Indonesian-only cross-tabs.",
            "No row text was downloaded or saved.",
            "Do not infer Indonesian license eligibility by multiplying marginal proportions.",
            "Every Indonesian source/license combination still requires row-level sampling and rights review.",
        ],
        "ingestion_performed": False,
        "training_performed": False,
    }

    output = os.environ.get("AUDIT_OUTPUT", "commonlingua_indonesian_audit.json")
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Audit report saved: {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"AUDIT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
