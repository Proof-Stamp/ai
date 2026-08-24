#!/usr/bin/env python3
"""Validate, receipt, verify, and prepare email handoff for a ProofStamp session artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from create_mailto import CONVERSATION_COVERAGE, build_email_text, build_mailto
from create_receipt import build_receipt, default_receipt_path, write_json_atomic
from validate_proofstamp import RECEIPT_SCHEMA, SESSION_SCHEMA, validate_file
from verify_proofstamp import verify


def load_artifact(artifact_path: Path) -> dict:
    value = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("artifact root must be a JSON object")
    return value


def completeness_status(artifact_path: Path) -> str:
    value = load_artifact(artifact_path)
    return value["capture"]["completeness"]["status"]


def conversation_coverage(artifact_path: Path) -> str:
    return CONVERSATION_COVERAGE[completeness_status(artifact_path)]


def validate_capture_semantics(artifact_path: Path) -> list[str]:
    """Enforce trust rules that JSON Schema alone cannot express."""
    value = load_artifact(artifact_path)
    errors: list[str] = []

    proofstamp = value.get("proofstamp")
    capture = value.get("capture")
    if not isinstance(proofstamp, dict) or not isinstance(capture, dict):
        return errors

    completeness = capture.get("completeness")
    if not isinstance(completeness, dict):
        return errors

    if (
        proofstamp.get("capture_method") == "ai_generated"
        and completeness.get("status") == "complete"
    ):
        evidence_reference = completeness.get("evidence_reference")
        if not isinstance(evidence_reference, str) or not evidence_reference.strip():
            errors.append(
                "ai_generated capture cannot claim completeness 'complete' without an explicit "
                "capture.completeness.evidence_reference to separate host/API/export evidence; "
                "use 'unknown' when completeness cannot be established"
            )

    return errors


def finalize(artifact: Path, *, force: bool = False) -> dict:
    session_errors = validate_file(artifact, SESSION_SCHEMA)
    if session_errors:
        raise ValueError("session schema validation failed: " + "; ".join(session_errors))

    semantic_errors = validate_capture_semantics(artifact)
    if semantic_errors:
        raise ValueError("capture trust validation failed: " + "; ".join(semantic_errors))

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

    mailto = build_mailto(artifact, receipt_path)
    email_text = build_email_text(artifact, receipt_path)
    completeness = completeness_status(artifact)
    coverage = CONVERSATION_COVERAGE[completeness]

    return {
        "artifact": artifact.name,
        "receipt": receipt_path.name,
        "sha256": actual_hash,
        "bytes": actual_size,
        "schema_validation": "passed",
        "capture_trust_validation": "passed",
        "hash_verified": True,
        "capture_completeness": completeness,
        "conversation_coverage": coverage,
        "email_handoff_required": True,
        "mailto": mailto,
        "email_text": email_text,
        "delivery_instruction": (
            "Final response should show Conversation coverage using the returned conversation_coverage value, "
            "not the raw capture_completeness status. It must also include Email this ProofStamp using the "
            "returned mailto URI; if mailto cannot be rendered, include the returned email_text fallback."
        ),
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
