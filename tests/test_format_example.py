import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples" / "synthetic-session"
ARTIFACT = EXAMPLE_DIR / "example-session.proofstamp.json"
RECEIPT = EXAMPLE_DIR / "example-session.proofstamp.receipt.json"
SESSION_SCHEMA = ROOT / "schemas" / "proofstamp-session-v1.schema.json"
RECEIPT_SCHEMA = ROOT / "schemas" / "proofstamp-receipt-v1.schema.json"
CREATE_SCRIPT = ROOT / "scripts" / "create_receipt.py"
VERIFY_SCRIPT = ROOT / "scripts" / "verify_proofstamp.py"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class FormatExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = load_json(ARTIFACT)
        cls.receipt = load_json(RECEIPT)
        cls.session_schema = load_json(SESSION_SCHEMA)
        cls.receipt_schema = load_json(RECEIPT_SCHEMA)

    def test_checked_in_artifact_validates(self):
        validator = Draft202012Validator(
            self.session_schema,
            format_checker=FormatChecker(),
        )
        errors = sorted(validator.iter_errors(self.artifact), key=lambda error: list(error.path))
        self.assertEqual([], errors, "\n".join(error.message for error in errors))

    def test_checked_in_receipt_validates(self):
        validator = Draft202012Validator(
            self.receipt_schema,
            format_checker=FormatChecker(),
        )
        errors = sorted(validator.iter_errors(self.receipt), key=lambda error: list(error.path))
        self.assertEqual([], errors, "\n".join(error.message for error in errors))

    def test_checked_in_receipt_matches_exact_artifact_bytes(self):
        artifact_bytes = ARTIFACT.read_bytes()
        actual_hash = hashlib.sha256(artifact_bytes).hexdigest()

        self.assertEqual(len(artifact_bytes), self.receipt["artifact"]["size_bytes"])
        self.assertEqual(ARTIFACT.name, self.receipt["artifact"]["filename"])
        self.assertEqual(actual_hash, self.receipt["fingerprint"]["sha256"])
        self.assertEqual(actual_hash, self.receipt["verification"]["recalculated_sha256"])
        self.assertTrue(self.receipt["verification"]["verified"])

    def test_verifier_accepts_checked_in_example(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT), str(ARTIFACT), str(RECEIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Verification passed", result.stdout)

    def test_creator_generates_receipt_that_verifies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_copy = Path(temp_dir) / "session.proofstamp.json"
            receipt_copy = Path(temp_dir) / "session.proofstamp.receipt.json"
            artifact_copy.write_bytes(ARTIFACT.read_bytes())

            create_result = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_SCRIPT),
                    str(artifact_copy),
                    "--output",
                    str(receipt_copy),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, create_result.returncode, create_result.stderr)

            generated = load_json(receipt_copy)
            validator = Draft202012Validator(
                self.receipt_schema,
                format_checker=FormatChecker(),
            )
            errors = sorted(
                validator.iter_errors(generated),
                key=lambda error: list(error.path),
            )
            self.assertEqual([], errors, "\n".join(error.message for error in errors))

            verify_result = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY_SCRIPT),
                    str(artifact_copy),
                    str(receipt_copy),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, verify_result.returncode, verify_result.stderr)

    def test_one_byte_change_breaks_verification(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_copy = Path(temp_dir) / ARTIFACT.name
            receipt_copy = Path(temp_dir) / RECEIPT.name
            artifact_copy.write_bytes(ARTIFACT.read_bytes())
            receipt_copy.write_bytes(RECEIPT.read_bytes())

            mutated = bytearray(artifact_copy.read_bytes())
            mutated[0] ^= 1
            artifact_copy.write_bytes(mutated)

            result = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY_SCRIPT),
                    str(artifact_copy),
                    str(receipt_copy),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("Verification failed", result.stderr)

    def test_artifact_does_not_self_embed_its_receipt_hash(self):
        artifact_text = ARTIFACT.read_text(encoding="utf-8")
        receipt_hash = self.receipt["fingerprint"]["sha256"]
        self.assertNotIn(receipt_hash, artifact_text)


if __name__ == "__main__":
    unittest.main()
