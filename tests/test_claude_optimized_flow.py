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


if __name__ == "__main__":
    unittest.main()
