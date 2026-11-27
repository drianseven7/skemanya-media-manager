#!/usr/bin/env python3
"""Metadata-only audit of Indonesian rows in PleIAs/CommonLingua-Train.

The script queries the Hugging Face dataset viewer API, counts provenance and
license groups, and computes byte totals in memory. It does NOT save paragraph
text, create a training corpus, or approve any row for training.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATASET = "PleIAs/CommonLingua-Train"
BASE = "https://datasets-server.huggingface.co"
LANGUAGE = "ind"  # ISO 639-3 Indonesian
PAGE_SIZE = 100
MAX_PAGES = 1000
USER_AGENT = "SKEMANYA-Corpus-Audit/0.1 (metadata-only; no training ingestion)"
APPROVED_OPEN_TYPES = {"public_domain", "cc_by"}


def get_json(endpoint: str, params: dict) -> dict:
    url = f"{BASE}/{endpoint}?{urlencode(params)}"
    last_error = None
    for attempt in range(5):
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"Dataset API returned HTTP {exc.code}: {url}") from exc
        except (URLError, TimeoutError) as exc:
            last_error = exc
        time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"Dataset API unavailable after retries: {last_error}")


def key(value) -> str:
    if value is None or str(value).strip() == "":
        return "[MISSING]"
    return str(value).strip()


def main() -> int:
    splits_payload = get_json("splits", {"dataset": DATASET})
    available = splits_payload.get("splits", [])
    train_split = next((s for s in available if s.get("split") == "train"), None)
    if not train_split:
        raise RuntimeError(
            "Train split tidak ditemukan. Periksa perubahan config/split dataset; "
            "audit dihentikan tanpa mengambil data training."
        )

    config = train_split["config"]
    split = train_split["split"]
    totals = Counter()
    by_license = Counter()
    by_open_type = Counter()
    by_source = Counter()
    by_source_license = Counter()
    missing = Counter()
    bytes_by_open_type = Counter()
    bytes_by_license = Counter()
    eligible_rows = 0
    eligible_bytes = 0
    offset = 0
    pages = 0
    api_total = None

    while pages < MAX_PAGES:
        payload = get_json(
            "filter",
            {
                "dataset": DATASET,
                "config": config,
                "split": split,
                "where": f"lang='{LANGUAGE}'",
                "offset": offset,
                "length": PAGE_SIZE,
            },
        )
        rows = payload.get("rows", [])
        if api_total is None:
            api_total = payload.get("num_rows_total")
        if not rows:
            break

        for wrapped in rows:
            row = wrapped.get("row", wrapped)
            totals["rows"] += 1
            license_name = key(row.get("license"))
            open_type = key(row.get("open_type"))
            source = key(row.get("source"))
            by_license[license_name] += 1
            by_open_type[open_type] += 1
            by_source[source] += 1
            by_source_license[f"{source} | {license_name} | {open_type}"] += 1

            for field in ("text", "license", "open_type", "source", "identifier", "creator"):
                if key(row.get(field)) == "[MISSING]":
                    missing[field] += 1

            text_value = row.get("text")
            byte_count = len(text_value.encode("utf-8")) if isinstance(text_value, str) else 0
            bytes_by_open_type[open_type] += byte_count
            bytes_by_license[license_name] += byte_count

            # Conservative candidate filter only. This is not legal approval.
            if open_type in APPROVED_OPEN_TYPES and source != "[MISSING]" and license_name != "[MISSING]":
                eligible_rows += 1
                eligible_bytes += byte_count

        offset += len(rows)
        pages += 1
        if api_total is not None and offset >= api_total:
            break
        if len(rows) < PAGE_SIZE:
            break

    if pages >= MAX_PAGES and api_total is not None and offset < api_total:
        raise RuntimeError(
            f"Safety limit reached: {offset} rows audited but API reports {api_total}. "
            "No partial report written."
        )

    report = {
        "dataset": DATASET,
        "config": config,
        "split": split,
        "language": LANGUAGE,
        "language_name": "Indonesian",
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "api_reported_matching_rows": api_total,
        "rows_audited": totals["rows"],
        "pages_fetched": pages,
        "text_bytes_in_memory_only": sum(bytes_by_license.values()),
        "candidate_filter": {
            "open_type_in": sorted(APPROVED_OPEN_TYPES),
            "requires_source": True,
            "requires_license": True,
            "candidate_rows_not_approved": eligible_rows,
            "candidate_text_bytes_not_saved": eligible_bytes,
            "warning": "Candidate counts only; source-level license terms and attribution still require manual review.",
        },
        "missing_metadata_counts": dict(sorted(missing.items())),
        "counts_by_license": dict(sorted(by_license.items())),
        "counts_by_open_type": dict(sorted(by_open_type.items())),
        "counts_by_source": dict(sorted(by_source.items())),
        "counts_by_source_license_open_type": dict(sorted(by_source_license.items())),
        "text_bytes_by_license": dict(sorted(bytes_by_license.items())),
        "text_bytes_by_open_type": dict(sorted(bytes_by_open_type.items())),
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
