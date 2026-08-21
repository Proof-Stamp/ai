#!/usr/bin/env python3
"""Verify a ProofStamp session artifact against its detached receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be a JSON object")
    return value


def verify(artifact_path: Path, receipt_path: Path) -> list[str]:
    errors: list[str] = []
    artifact = load_json(artifact_path, "artifact")
    receipt = load_json(receipt_path, "receipt")

    proofstamp = artifact.get("proofstamp")
    if not isinstance(proofstamp, dict):
        errors.append("artifact is missing proofstamp metadata")
    else:
        if proofstamp.get("format") != "proofstamp-session":
            errors.append("artifact proofstamp.format is not 'proofstamp-session'")
        if proofstamp.get("format_version") != "1.0":
            errors.append("artifact proofstamp.format_version is not '1.0'")

    receipt_meta = receipt.get("proofstamp")
    if not isinstance(receipt_meta, dict):
        errors.append("receipt is missing proofstamp metadata")
    else:
        if receipt_meta.get("format") != "proofstamp-receipt":
            errors.append("receipt proofstamp.format is not 'proofstamp-receipt'")
        if receipt_meta.get("format_version") != "1.0":
            errors.append("receipt proofstamp.format_version is not '1.0'")

    actual_hash, actual_size = sha256_file(artifact_path)

    artifact_meta = receipt.get("artifact")
    if not isinstance(artifact_meta, dict):
        errors.append("receipt is missing artifact metadata")
    else:
        if artifact_meta.get("filename") != artifact_path.name:
            errors.append("receipt artifact filename does not match the selected artifact")
        if artifact_meta.get("size_bytes") != actual_size:
            errors.append("receipt artifact byte size does not match the selected artifact")
        if artifact_meta.get("format") != "proofstamp-session":
            errors.append("receipt artifact format is not 'proofstamp-session'")
        if artifact_meta.get("format_version") != "1.0":
            errors.append("receipt artifact format_version is not '1.0'")

    fingerprint = receipt.get("fingerprint")
    expected_hash = None
    if not isinstance(fingerprint, dict):
        errors.append("receipt is missing fingerprint metadata")
    else:
        if fingerprint.get("algorithm") != "SHA-256":
            errors.append("receipt fingerprint algorithm is not SHA-256")
        expected_hash = fingerprint.get("sha256")
        if expected_hash != actual_hash:
            errors.append("artifact SHA-256 does not match receipt fingerprint")

    verification = receipt.get("verification")
    if not isinstance(verification, dict):
        errors.append("receipt is missing verification metadata")
    else:
        if verification.get("verified") is not True:
            errors.append("receipt verification.verified is not true")
        recalculated = verification.get("recalculated_sha256")
        if recalculated != expected_hash:
            errors.append("receipt recalculated_sha256 does not equal receipt fingerprint")
        if recalculated != actual_hash:
            errors.append("receipt recalculated_sha256 does not match artifact bytes")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify a .proofstamp.json artifact against a detached receipt."
    )
    parser.add_argument("artifact", type=Path, help="Path to the session artifact")
    parser.add_argument("receipt", type=Path, help="Path to the detached receipt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if not args.artifact.is_file():
            raise ValueError(f"artifact does not exist or is not a file: {args.artifact}")
        if not args.receipt.is_file():
            raise ValueError(f"receipt does not exist or is not a file: {args.receipt}")
        errors = verify(args.artifact, args.receipt)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if errors:
        print("Verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    actual_hash, actual_size = sha256_file(args.artifact)
    print("Verification passed")
    print(f"SHA-256: {actual_hash}")
    print(f"Bytes: {actual_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
