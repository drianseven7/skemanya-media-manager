#!/usr/bin/env python3
"""Metadata-only audit of Indonesian CommonLingua rows and license categories."""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET = "PleIAs/CommonLingua-Train"
BASE = "https://datasets-server.huggingface.co"
USER_AGENT = "SKEMANYA-Corpus-Audit/0.3 (metadata-only; no training ingestion)"


def get_json(endpoint: str, params: dict) -> dict:
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Dataset API HTTP {exc.code}: {body[:1000]}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Dataset API unavailable: {exc}") from exc


def main() -> int:
    splits_payload = get_json("splits", {"dataset": DATASET})
    train_split = next((x for x in splits_payload.get("splits", []) if x.get("split") == "train"), None)
    if not train_split:
        raise RuntimeError("Split train tidak ditemukan.")
    config, split = train_split["config"], train_split["split"]
    stats = get_json("statistics", {"dataset": DATASET, "config": config, "split": split})
    if stats.get("partial") is True:
        raise RuntimeError("Statistik dataset parsial; audit dihentikan.")
    columns = {x["column_name"]: x for x in stats.get("statistics", [])}

    def frequencies(column):
        values = columns.get(column, {}).get("column_statistics", {}).get("frequencies")
        if not isinstance(values, dict):
            raise RuntimeError(f"Frequency table tidak tersedia untuk kolom {column}.")
        return values

    languages = frequencies("lang")
    licenses = frequencies("license")
    open_types = frequencies("open_type")
    sources = frequencies("source")
    ind_rows = int(languages.get("ind", 0))

    def count_filtered(column, value):
        # Fetch one row only: num_rows_total gives the exact count for this predicate.
        escaped = str(value).replace("'", "''")
        where = f'"lang"=\'ind\' AND "{column}"=\'{escaped}\''
        result = get_json("filter", {
            "dataset": DATASET, "config": config, "split": split,
            "where": where, "offset": 0, "length": 1,
        })
        if result.get("partial") is True:
            raise RuntimeError(f"Filter parsial untuk {column}={value!r}.")
        count = result.get("num_rows_total")
        if count is None:
            raise RuntimeError(f"API tidak memberi num_rows_total untuk {column}={value!r}.")
        sample_sources = sorted({r.get("row", {}).get("source") for r in result.get("rows", []) if r.get("row", {}).get("source")})
        return str(value), int(count), sample_sources

    tasks = [("license", value) for value in licenses]
    tasks += [("open_type", value) for value in open_types]
    results = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(count_filtered, col, value): (col, value) for col, value in tasks}
        for future in as_completed(futures):
            col, value = futures[future]
            key, count, samples = future.result()
            results.setdefault(col, {})[key] = count
            if col == "license":
                results.setdefault("sample_sources_by_license", {})[key] = samples

    report = {
        "dataset": DATASET, "config": config, "split": split,
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_rows_in_statistics": stats.get("num_examples"),
        "statistics_partial": stats.get("partial"),
        "indonesian_rows": ind_rows,
        "unique_language_values": len(languages),
        "global_license_values": dict(sorted(licenses.items(), key=lambda x: (-x[1], x[0]))),
        "global_open_type_values": dict(sorted(open_types.items(), key=lambda x: (-x[1], x[0]))),
        "global_source_values": dict(sorted(sources.items(), key=lambda x: (-x[1], x[0]))),
        "indonesian_counts_by_license": dict(sorted(results.get("license", {}).items(), key=lambda x: (-x[1], x[0]))),
        "indonesian_counts_by_open_type": dict(sorted(results.get("open_type", {}).items(), key=lambda x: (-x[1], x[0]))),
        "sample_sources_by_license": results.get("sample_sources_by_license", {}),
        "indonesian_count_check": sum(results.get("license", {}).values()) == ind_rows,
        "limitations": [
            "License and open_type counts are exact per Indonesian language filter; source examples are only one-row samples per license.",
            "No paragraph text is saved or ingested.",
            "Counts do not replace source-level license review, attribution review, or legal approval.",
        ],
        "ingestion_performed": False, "training_performed": False,
    }
    if not report["indonesian_count_check"]:
        raise RuntimeError("Jumlah per-lisensi tidak sama dengan total baris Indonesian; audit tidak lengkap.")
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
