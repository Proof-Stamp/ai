#!/usr/bin/env python3
"""Create a detached ProofStamp receipt for an existing session artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ARTIFACT_SUFFIX = ".proofstamp.json"
RECEIPT_SUFFIX = ".proofstamp.receipt.json"


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def load_artifact_header(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"artifact is not valid UTF-8 JSON: {exc}") from exc

    proofstamp = data.get("proofstamp")
    if not isinstance(proofstamp, dict):
        raise ValueError("artifact is missing proofstamp metadata")
    if proofstamp.get("format") != "proofstamp-session":
        raise ValueError("artifact proofstamp.format must be 'proofstamp-session'")
    if proofstamp.get("format_version") != "1.0":
        raise ValueError("artifact proofstamp.format_version must be '1.0'")
    return data


def default_receipt_path(artifact: Path) -> Path:
    name = artifact.name
    if not name.endswith(ARTIFACT_SUFFIX):
        raise ValueError(f"artifact filename must end with {ARTIFACT_SUFFIX}")
    stem = name[: -len(ARTIFACT_SUFFIX)]
    return artifact.with_name(stem + RECEIPT_SUFFIX)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json_atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        temp_name = handle.name
    os.replace(temp_name, path)


def build_receipt(artifact: Path) -> dict:
    load_artifact_header(artifact)

    first_hash, first_size = sha256_file(artifact)
    second_hash, second_size = sha256_file(artifact)

    if first_hash != second_hash or first_size != second_size:
        raise RuntimeError(
            "independent verification failed: artifact bytes changed between reads"
        )

    return {
        "proofstamp": {
            "format": "proofstamp-receipt",
            "format_version": "1.0",
        },
        "artifact": {
            "filename": artifact.name,
            "size_bytes": first_size,
            "format": "proofstamp-session",
            "format_version": "1.0",
        },
        "fingerprint": {
            "algorithm": "SHA-256",
            "sha256": first_hash,
        },
        "verification": {
            "verified": True,
            "recalculated_sha256": second_hash,
            "method": "Read the saved artifact bytes twice and compare both SHA-256 calculations.",
        },
        "created_at": {
            "value": utc_now(),
            "provenance": "derived",
        },
        "limitations": [
            "This receipt identifies the exact bytes of the referenced session artifact. It does not authenticate the AI provider or prove session completeness.",
            "The receipt creation time is a local generation time and is not external timestamp evidence.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a detached receipt for a .proofstamp.json session artifact."
    )
    parser.add_argument("artifact", type=Path, help="Path to the session artifact")
    parser.add_argument(
        "--output",
        type=Path,
        help="Receipt output path. Defaults to <name>.proofstamp.receipt.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing receipt file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact = args.artifact

    try:
        if not artifact.is_file():
            raise ValueError(f"artifact does not exist or is not a file: {artifact}")
        output = args.output or default_receipt_path(artifact)
        if output.exists() and not args.force:
            raise ValueError(f"receipt already exists: {output}; use --force to replace it")

        receipt = build_receipt(artifact)
        write_json_atomic(output, receipt)
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Receipt: {output}")
    print(f"SHA-256: {receipt['fingerprint']['sha256']}")
    print(f"Bytes: {receipt['artifact']['size_bytes']}")
    print("Verified: yes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
