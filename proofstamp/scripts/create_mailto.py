#!/usr/bin/env python3
"""Create a pre-filled mailto link for a verified ProofStamp artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

from verify_proofstamp import sha256_file, verify


VERIFY_URL = "https://email.proofstamp.org/verify"


def load_receipt(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"receipt is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("receipt root must be a JSON object")
    return value


def build_mailto(artifact_path: Path, receipt_path: Path) -> str:
    errors, verified_hash, verified_size = verify(artifact_path, receipt_path)
    if errors:
        raise ValueError("ProofStamp verification failed: " + "; ".join(errors))

    receipt = load_receipt(receipt_path)
    actual_hash, actual_size = sha256_file(artifact_path)
    if actual_hash != verified_hash or actual_size != verified_size:
        raise ValueError("artifact bytes changed during mailto creation")

    receipt_hash = receipt.get("fingerprint", {}).get("sha256")
    receipt_size = receipt.get("artifact", {}).get("size_bytes")
    if receipt_hash != actual_hash or receipt_size != actual_size:
        raise ValueError("receipt no longer matches the selected artifact")

    subject = f"ProofStamp: {artifact_path.name}"
    body = "\n".join(
        [
            "PROOFSTAMP",
            "",
            f"File: {artifact_path.name}",
            f"SHA-256: {actual_hash}",
            f"Size: {actual_size} bytes",
            "Hash verified locally: yes",
            "",
            "Keep the original .proofstamp.json file and its detached .proofstamp.receipt.json receipt.",
            "",
            "A matching SHA-256 later shows that a file matches these exact bytes. This email does not prove when the underlying AI conversation originally occurred.",
            "",
            f"Check this file later: {VERIFY_URL}",
        ]
    )

    return f"mailto:?subject={quote(subject, safe='')}&body={quote(body, safe='')}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a mailto link from a verified ProofStamp artifact and receipt."
    )
    parser.add_argument("artifact", type=Path, help="Path to the .proofstamp.json artifact")
    parser.add_argument("receipt", type=Path, help="Path to the detached receipt")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if not args.artifact.is_file():
            raise ValueError(f"artifact does not exist or is not a file: {args.artifact}")
        if not args.receipt.is_file():
            raise ValueError(f"receipt does not exist or is not a file: {args.receipt}")
        mailto = build_mailto(args.artifact, args.receipt)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(mailto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
