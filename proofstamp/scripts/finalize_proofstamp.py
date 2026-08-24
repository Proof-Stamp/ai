#!/usr/bin/env python3
"""Validate, receipt, verify, and prepare email handoff for a ProofStamp session artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from create_mailto import build_email_text, build_mailto
from create_receipt import build_receipt, default_receipt_path, write_json_atomic
from validate_proofstamp import RECEIPT_SCHEMA, SESSION_SCHEMA, validate_file
from verify_proofstamp import verify


def completeness_status(artifact_path: Path) -> str:
    value = json.loads(artifact_path.read_text(encoding="utf-8"))
    return value["capture"]["completeness"]["status"]


def finalize(artifact: Path, *, force: bool = False) -> dict:
    session_errors = validate_file(artifact, SESSION_SCHEMA)
    if session_errors:
        raise ValueError("session schema validation failed: " + "; ".join(session_errors))

    receipt_path = default_receipt_path(artifact)
    if receipt_path.exists() and not force:
        raise ValueError(f"receipt already exists: {receipt_path}; use --force to replace it")

    receipt = build_receipt(artifact)
    write_json_atomic(receipt_path, receipt)

    receipt_errors = validate_file(receipt_path, RECEIPT_SCHEMA)
    if receipt_errors:
        receipt_path.unlink(missing_ok=True)
        raise ValueError("receipt schema validation failed: " + "; ".join(receipt_errors))

    verification_errors, actual_hash, actual_size = verify(artifact, receipt_path)
    if verification_errors:
        receipt_path.unlink(missing_ok=True)
        raise ValueError("exact-byte verification failed: " + "; ".join(verification_errors))

    return {
        "artifact": artifact.name,
        "receipt": receipt_path.name,
        "sha256": actual_hash,
        "bytes": actual_size,
        "schema_validation": "passed",
        "hash_verified": True,
        "capture_completeness": completeness_status(artifact),
        "mailto": build_mailto(artifact, receipt_path),
        "email_text": build_email_text(artifact, receipt_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Path to the .proofstamp.json artifact")
    parser.add_argument("--force", action="store_true", help="Replace an existing detached receipt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if not args.artifact.is_file():
            raise ValueError(f"artifact does not exist or is not a file: {args.artifact}")
        result = finalize(args.artifact, force=args.force)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
