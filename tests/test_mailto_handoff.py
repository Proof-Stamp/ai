import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "examples" / "synthetic-session" / "example-session.proofstamp.json"
RECEIPT = ROOT / "examples" / "synthetic-session" / "example-session.proofstamp.receipt.json"
MAILTO_SCRIPT = ROOT / "proofstamp" / "scripts" / "create_mailto.py"
RECEIPT_SCRIPT = ROOT / "proofstamp" / "scripts" / "create_receipt.py"

COVERAGE_LABELS = {
    "complete": "confirmed for recorded scope",
    "partial": "partial",
    "unknown": "not independently confirmed",
}


class MailtoHandoffTests(unittest.TestCase):
    def run_mailto(self, artifact: Path, receipt: Path, *extra_args: str):
        return subprocess.run(
            [
                sys.executable,
                str(MAILTO_SCRIPT),
                str(artifact),
                str(receipt),
                *extra_args,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def create_receipt(self, artifact: Path) -> Path:
        result = subprocess.run(
            [sys.executable, str(RECEIPT_SCRIPT), str(artifact)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return artifact.with_name(
            artifact.name.removesuffix(".proofstamp.json")
            + ".proofstamp.receipt.json"
        )

    def test_verified_example_creates_prefilled_mailto(self):
        result = self.run_mailto(ARTIFACT, RECEIPT)
        self.assertEqual(0, result.returncode, result.stderr)

        link = result.stdout.strip()
        parsed = urlparse(link)
        self.assertEqual("mailto", parsed.scheme)
        self.assertEqual("", parsed.path)

        query = parse_qs(parsed.query, strict_parsing=True)
        self.assertEqual([f"ProofStamp: {ARTIFACT.name}"], query["subject"])

        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        expected_hash = receipt["fingerprint"]["sha256"]
        expected_size = receipt["artifact"]["size_bytes"]

        body = query["body"][0]
        self.assertIn(f"File: {ARTIFACT.name}", body)
        self.assertIn(f"SHA-256: {expected_hash}", body)
        self.assertIn(f"Size: {expected_size} bytes", body)
        self.assertIn("Hash verified locally: yes", body)
        self.assertIn("Conversation coverage: confirmed for recorded scope", body)
        self.assertIn("https://email.proofstamp.org/verify", body)
        self.assertIn("does not prove truth, authenticity", body)

        # The handoff contains fingerprint metadata, not captured session contents.
        self.assertNotIn("ExampleChat", body)
        self.assertNotIn("Prepare a project handoff", body)

    def test_prefilled_text_fallback_has_blank_recipient_and_required_fields(self):
        result = self.run_mailto(ARTIFACT, RECEIPT, "--text")
        self.assertEqual(0, result.returncode, result.stderr)

        text = result.stdout
        self.assertTrue(text.startswith("To:\nSubject: ProofStamp:"))
        self.assertIn(f"File: {ARTIFACT.name}", text)
        self.assertIn("SHA-256:", text)
        self.assertIn("Size:", text)
        self.assertIn("Hash verified locally: yes", text)
        self.assertIn("Conversation coverage: confirmed for recorded scope", text)
        self.assertIn("https://email.proofstamp.org/verify", text)
        self.assertIn("does not prove truth, authenticity", text)

    def test_mailto_translates_each_capture_completeness_status_for_people(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for status, label in COVERAGE_LABELS.items():
                with self.subTest(status=status):
                    artifact_copy = Path(temp_dir) / f"{status}.proofstamp.json"
                    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
                    data["capture"]["completeness"]["status"] = status
                    artifact_copy.write_text(
                        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    receipt_copy = self.create_receipt(artifact_copy)

                    result = self.run_mailto(artifact_copy, receipt_copy)
                    self.assertEqual(0, result.returncode, result.stderr)
                    body = parse_qs(
                        urlparse(result.stdout.strip()).query,
                        strict_parsing=True,
                    )["body"][0]
                    self.assertIn(f"Conversation coverage: {label}", body)
                    self.assertNotIn("Capture completeness:", body)

    def test_invalid_capture_completeness_refuses_handoff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_copy = Path(temp_dir) / "invalid.proofstamp.json"
            data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
            data["capture"]["completeness"]["status"] = "bogus"
            artifact_copy.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            receipt_copy = self.create_receipt(artifact_copy)

            result = self.run_mailto(artifact_copy, receipt_copy)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("capture completeness", result.stderr.lower())
            self.assertEqual("", result.stdout.strip())

    def test_mutated_artifact_refuses_mailto(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_copy = Path(temp_dir) / ARTIFACT.name
            receipt_copy = Path(temp_dir) / RECEIPT.name
            shutil.copyfile(ARTIFACT, artifact_copy)
            shutil.copyfile(RECEIPT, receipt_copy)

            original = bytearray(artifact_copy.read_bytes())
            position = original.index(b"ExampleChat")
            original[position] = ord("X")
            artifact_copy.write_bytes(original)

            result = self.run_mailto(artifact_copy, receipt_copy)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("verification failed", result.stderr.lower())
            self.assertEqual("", result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
