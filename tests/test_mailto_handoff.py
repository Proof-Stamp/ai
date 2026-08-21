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


class MailtoHandoffTests(unittest.TestCase):
    def run_mailto(self, artifact: Path, receipt: Path):
        return subprocess.run(
            [sys.executable, str(MAILTO_SCRIPT), str(artifact), str(receipt)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
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

        body = query["body"][0]
        self.assertIn(f"File: {ARTIFACT.name}", body)
        self.assertIn(
            "SHA-256: 1e103f563ddc475aea7ccd5fe56210f47722b3bcffdd8db07c2cd515dea7783d",
            body,
        )
        self.assertIn("Size: 5120 bytes", body)
        self.assertIn("Hash verified locally: yes", body)
        self.assertIn("https://email.proofstamp.org/verify", body)
        self.assertIn("does not prove when the underlying AI conversation originally occurred", body)

        # The handoff contains fingerprint metadata, not captured session contents.
        self.assertNotIn("ExampleChat", body)
        self.assertNotIn("Prepare a project handoff", body)

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
