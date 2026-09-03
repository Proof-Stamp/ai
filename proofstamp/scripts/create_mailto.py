#!/usr/bin/env python3
"""Create a required email handoff for a verified ProofStamp artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

from verify_proofstamp import load_json, sha256_file, verify


VERIFY_URL = "https://email.proofstamp.org/verify"
VALID_COMPLETENESS = {"complete", "partial", "unknown"}
CONVERSATION_COVERAGE = {
    "complete": "confirmed for recorded scope",
    "partial": "partial",
    "unknown": "not independently confirmed",
}


def load_receipt(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"receipt is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("receipt root must be a JSON object")
    return value


def build_email_content(artifact_path: Path, receipt_path: Path) -> tuple[str, str]:
    errors, verified_hash, verified_size = verify(artifact_path, receipt_path)
    if errors:
        raise ValueError("ProofStamp verification failed: " + "; ".join(errors))

    receipt = load_receipt(receipt_path)
    artifact = load_json(artifact_path, "artifact")
    actual_hash, actual_size = sha256_file(artifact_path)
    if actual_hash != verified_hash or actual_size != verified_size:
        raise ValueError("artifact bytes changed during email handoff creation")

    receipt_hash = receipt.get("fingerprint", {}).get("sha256")
    receipt_size = receipt.get("artifact", {}).get("size_bytes")
    if receipt_hash != actual_hash or receipt_size != actual_size:
        raise ValueError("receipt no longer matches the selected artifact")

    capture = artifact.get("capture")
    completeness = None
    if isinstance(capture, dict):
        completeness_value = capture.get("completeness")
        if isinstance(completeness_value, dict):
            completeness = completeness_value.get("status")
    if completeness not in VALID_COMPLETENESS:
        raise ValueError("artifact is missing a valid capture completeness status")

    subject = f"ProofStamp: {artifact_path.name}"
    body = "\n".join(
        [
            "ProofStamp͘",
            "",
            f"File: {artifact_path.name}",
            f"SHA-256: {actual_hash}",
            f"Size: {actual_size} bytes",
            "Hash verified locally: yes",
            f"Conversation coverage: {CONVERSATION_COVERAGE[completeness]}",
            "",
            "Keep the original .proofstamp.json file and its detached .proofstamp.receipt.json receipt.",
            "",
            "A matching SHA-256 later confirms exact-byte integrity only. It does not prove truth, authenticity, or when the underlying AI conversation originally occurred.",
            "",
            f"Check this file later: {VERIFY_URL}",
        ]
    )
    return subject, body


def build_mailto(artifact_path: Path, receipt_path: Path) -> str:
    subject, body = build_email_content(artifact_path, receipt_path)
    return f"mailto:?subject={quote(subject, safe='')}&body={quote(body, safe='')}"


def build_email_text(artifact_path: Path, receipt_path: Path) -> str:
    subject, body = build_email_content(artifact_path, receipt_path)
    return f"To:\nSubject: {subject}\n\n{body}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the required email handoff from a verified ProofStamp artifact and receipt."
    )
    parser.add_argument("artifact", type=Path, help="Path to the .proofstamp.json artifact")
    parser.add_argument("receipt", type=Path, help="Path to the detached receipt")
    parser.add_argument(
        "--text",
        action="store_true",
        help="Output pre-filled email text with a blank recipient instead of a mailto URI",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if not args.artifact.is_file():
            raise ValueError(f"artifact does not exist or is not a file: {args.artifact}")
        if not args.receipt.is_file():
            raise ValueError(f"receipt does not exist or is not a file: {args.receipt}")
        output = (
            build_email_text(args.artifact, args.receipt)
            if args.text
            else build_mailto(args.artifact, args.receipt)
        )
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
