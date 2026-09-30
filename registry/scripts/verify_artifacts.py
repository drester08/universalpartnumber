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
    if errors:
        print("Artifact verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Artifact verification passed: {verified} cached file(s) verified; {len(artifacts) - verified} remote/blocked record(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
