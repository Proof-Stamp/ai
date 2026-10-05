import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "proofstamp" / "scripts"
EXAMPLE = ROOT / "examples" / "synthetic-session" / "example-session.proofstamp.json"


class ClaudeOptimizedFlowTests(unittest.TestCase):
    def test_stdlib_validator_accepts_synthetic_session(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_proofstamp.py"), str(EXAMPLE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("schema validation passed", result.stdout)

    def test_finalizer_validates_creates_receipt_verifies_and_builds_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "synthetic-proofstamp-test-2026-08-24.proofstamp.json"
            value = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            value["capture"]["completeness"]["status"] = "unknown"
            value["capture"]["completeness"]["basis"] = (
                "Synthetic ai_generated capture used to exercise conservative completeness handling."
            )
            value["capture"]["completeness"].pop("evidence_reference", None)
            artifact.write_text(json.dumps(value), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "finalize_proofstamp.py"), str(artifact)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual("passed", output["schema_validation"])
            self.assertEqual("passed", output["capture_trust_validation"])
            self.assertEqual(
                "consistency_checks_only_not_source_authentication",
                output["capture_trust_validation_scope"],
            )
            self.assertIs(True, output["hash_verified"])
            self.assertEqual("unknown", output["capture_completeness"])
            self.assertEqual("not independently confirmed", output["conversation_coverage"])
            self.assertIs(True, output["email_handoff_required"])
            self.assertTrue(output["mailto"].startswith("mailto:?subject="))
            self.assertTrue(output["email_text"].startswith("To:\nSubject: ProofStamp:"))
            self.assertIn("Conversation coverage", output["delivery_instruction"])
            self.assertIn("Email this ProofStamp", output["delivery_instruction"])
            receipt = artifact.with_name("synthetic-proofstamp-test-2026-08-24.proofstamp.receipt.json")
            self.assertTrue(receipt.is_file())

            validate_receipt = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_proofstamp.py"), str(receipt)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, validate_receipt.returncode, validate_receipt.stderr)

    def test_finalizer_rejects_ai_generated_complete_even_with_evidence_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "unsupported-complete.proofstamp.json"
            value = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            self.assertEqual("ai_generated", value["proofstamp"]["capture_method"])
            self.assertEqual("complete", value["capture"]["completeness"]["status"])
            self.assertTrue(value["capture"]["completeness"]["evidence_reference"])
            artifact.write_text(json.dumps(value), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "finalize_proofstamp.py"), str(artifact)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("capture trust validation failed", result.stderr)
            self.assertIn("ai_generated capture cannot claim completeness 'complete'", result.stderr)
            self.assertIn("stronger capture method", result.stderr)
            self.assertFalse(
                artifact.with_name("unsupported-complete.proofstamp.receipt.json").exists()
            )

    def test_validator_rejects_missing_required_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "invalid.proofstamp.json"
            value = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            del value["capture"]["completeness"]
            artifact.write_text(json.dumps(value), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_proofstamp.py"), str(artifact)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("missing required property 'completeness'", result.stderr)

    def test_finalizer_rejects_inconsistent_claims_without_creating_receipt(self):
        cases = {
            "redacted-complete": "redacted capture cannot claim completeness",
            "empty-scope": "non-empty declared scope",
            "missing-evidence": "affirmative evidence_reference",
            "duplicate-sequence": "unique and strictly increasing",
            "reversed-sequence": "unique and strictly increasing",
            "unsupported-signature": "no provider-signature verifier",
        }
        for case, expected_error in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                value = json.loads(EXAMPLE.read_text(encoding="utf-8"))
                value["proofstamp"]["capture_method"] = "api_capture"
                completeness = value["capture"]["completeness"]
                if case == "redacted-complete":
                    value["session"]["messages"][0]["content"] = "[REDACTED]"
                    value["capture"]["redactions"] = [{
                        "location": "session.messages[0].content",
                        "reason": "user_requested_secret_redaction",
                    }]
                elif case == "empty-scope":
                    value["capture"]["scope"] = []
                elif case == "missing-evidence":
                    completeness.pop("evidence_reference")
                elif case == "duplicate-sequence":
                    value["session"]["messages"][1]["sequence"] = 1
                elif case == "reversed-sequence":
                    value["session"]["messages"].reverse()
                elif case == "unsupported-signature":
                    value["proofstamp"]["capture_method"] = "provider_signed"
                    completeness["status"] = "unknown"

                artifact = Path(tmp) / "synthetic-review.proofstamp.json"
                artifact.write_text(json.dumps(value), encoding="utf-8")
                original = artifact.read_bytes()
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / "finalize_proofstamp.py"), str(artifact)],
                    cwd=ROOT, text=True, capture_output=True,
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn(expected_error, result.stderr)
                self.assertEqual(original, artifact.read_bytes())
                self.assertFalse((Path(tmp) / "synthetic-review.proofstamp.receipt.json").exists())

    def test_finalizer_accepts_host_complete_and_redacted_partial_with_explicit_boundary(self):
        for redacted in (False, True):
            with self.subTest(redacted=redacted), tempfile.TemporaryDirectory() as tmp:
                value = json.loads(EXAMPLE.read_text(encoding="utf-8"))
                value["proofstamp"]["capture_method"] = "api_capture"
                if redacted:
                    value["capture"]["completeness"]["status"] = "partial"
                    value["session"]["messages"][0]["content"] = "[REDACTED]"
                    value["capture"]["redactions"] = [{
                        "location": "session.messages[0].content",
                        "reason": "user_requested_secret_redaction",
                    }]
                artifact = Path(tmp) / "synthetic-valid.proofstamp.json"
                artifact.write_text(json.dumps(value), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / "finalize_proofstamp.py"), str(artifact)],
                    cwd=ROOT, text=True, capture_output=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                output = json.loads(result.stdout)
                self.assertTrue(output["hash_verified"])
                self.assertEqual("partial" if redacted else "complete", output["capture_completeness"])
                self.assertEqual(
                    "consistency_checks_only_not_source_authentication",
                    output["capture_trust_validation_scope"],
                )

    def test_validator_does_not_treat_zero_as_json_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "invalid-boolean-const.proofstamp.json"
            value = json.loads(EXAMPLE.read_text(encoding="utf-8"))
            value["attachments"] = [
                {
                    "id": "synthetic-attachment",
                    "filename": "synthetic.txt",
                    "content_included": 0,
                    "provenance": "user_provided",
                }
            ]
            artifact.write_text(json.dumps(value), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_proofstamp.py"), str(artifact)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("must equal False", result.stderr)


if __name__ == "__main__":
    unittest.main()
