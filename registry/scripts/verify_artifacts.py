#!/usr/bin/env python3
"""Verify locally retained evidence artifacts against the provenance register."""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> int:
    errors: list[str] = []
    verified = 0
    dataset_verified = 0
    with (ROOT / "data" / "source-artifacts.csv").open(encoding="utf-8-sig", newline="") as handle:
        artifacts = list(csv.DictReader(handle))
    for artifact in artifacts:
        state = artifact["retrieval_state"]
        local_path = artifact["local_path"].strip()
        recorded_hash = artifact["sha256"].strip().upper()
        if state == "retrieved":
            if not local_path or not recorded_hash:
                errors.append(f"{artifact['artifact_id']}: retrieved artifact lacks path or SHA-256")
                continue
            path = ROOT.parent / Path(local_path)
            if not path.is_file():
                errors.append(f"{artifact['artifact_id']}: cached file is missing at {path}")
                continue
            actual_hash = sha256(path)
            if actual_hash != recorded_hash:
                errors.append(
                    f"{artifact['artifact_id']}: SHA-256 mismatch; expected {recorded_hash}, got {actual_hash}"
                )
                continue
            verified += 1
        elif local_path or recorded_hash:
            errors.append(f"{artifact['artifact_id']}: non-retrieved artifact must not claim a path or checksum")
    with (ROOT / "data" / "source-datasets.csv").open(encoding="utf-8-sig", newline="") as handle:
        datasets = list(csv.DictReader(handle))
    for dataset in datasets:
        path = ROOT.parent / Path(dataset["local_path"])
        if not path.is_file():
            errors.append(f"{dataset['dataset_id']}: reference dataset is missing at {path}")
            continue
        actual_hash = sha256(path)
        recorded_hash = dataset["sha256"].strip().upper()
        if actual_hash != recorded_hash:
            errors.append(
                f"{dataset['dataset_id']}: SHA-256 mismatch; expected {recorded_hash}, got {actual_hash}"
            )
            continue
        with path.open(encoding="utf-8-sig", newline="") as dataset_handle:
            reader = csv.reader(dataset_handle)
            header = next(reader, [])
            row_count = sum(1 for _ in reader)
        if row_count != int(dataset["row_count"]) or len(header) != int(dataset["column_count"]):
            errors.append(
                f"{dataset['dataset_id']}: recorded shape {dataset['row_count']}x{dataset['column_count']} "
                f"does not match {row_count}x{len(header)}"
            )
            continue
        dataset_verified += 1
    if errors:
        print("Artifact verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"Artifact verification passed: {verified} cached evidence file(s) and "
        f"{dataset_verified} reference dataset(s) verified; "
        f"{len(artifacts) - verified} remote/blocked evidence record(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
