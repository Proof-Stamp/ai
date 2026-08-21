import copy
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SESSION_SCHEMA_PATH = ROOT / "schemas" / "proofstamp-session-v1.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "schemas" / "proofstamp-receipt-v1.schema.json"
SECURITY_FIXTURE_PATH = (
    ROOT / "tests" / "security" / "fixtures" / "prompt-injection-session.proofstamp.json"
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate(schema, instance):
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


def receipt_semantics_are_valid(receipt):
    return (
        receipt["verification"]["verified"] is True
        and receipt["fingerprint"]["sha256"]
        == receipt["verification"]["recalculated_sha256"]
    )


class SchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session_schema = load_json(SESSION_SCHEMA_PATH)
        cls.receipt_schema = load_json(RECEIPT_SCHEMA_PATH)
        cls.fixture = load_json(SECURITY_FIXTURE_PATH)

    def test_prompt_injection_fixture_is_schema_valid(self):
        validate(self.session_schema, self.fixture)

    def test_unavailable_status_cannot_claim_excluded_provenance(self):
        invalid = copy.deepcopy(self.fixture)
        invalid["environment"]["system_prompt"]["provenance"] = "excluded"
        with self.assertRaises(ValidationError):
            validate(self.session_schema, invalid)

    def test_captured_value_cannot_use_unavailable_provenance(self):
        invalid = copy.deepcopy(self.fixture)
        invalid["environment"]["model"]["provenance"] = "unavailable"
        with self.assertRaises(ValidationError):
            validate(self.session_schema, invalid)

    def test_attachment_content_cannot_be_embedded_in_v1(self):
        invalid = copy.deepcopy(self.fixture)
        invalid["attachments"] = [
            {
                "id": "attachment-1",
                "filename": "synthetic.txt",
                "content_included": True,
                "provenance": "user_provided",
            }
        ]
        with self.assertRaises(ValidationError):
            validate(self.session_schema, invalid)

    def test_detached_receipt_validates_and_matches_exact_fixture_bytes(self):
        artifact_bytes = SECURITY_FIXTURE_PATH.read_bytes()
        digest = hashlib.sha256(artifact_bytes).hexdigest()
        receipt = {
            "proofstamp": {
                "format": "proofstamp-receipt",
                "format_version": "1.0",
            },
            "artifact": {
                "filename": SECURITY_FIXTURE_PATH.name,
                "size_bytes": len(artifact_bytes),
                "format": "proofstamp-session",
                "format_version": "1.0",
            },
            "fingerprint": {"algorithm": "SHA-256", "sha256": digest},
            "verification": {
                "verified": True,
                "recalculated_sha256": hashlib.sha256(
                    SECURITY_FIXTURE_PATH.read_bytes()
                ).hexdigest(),
                "method": "read saved fixture bytes twice and recalculate SHA-256",
            },
            "created_at": {
                "value": "2026-08-21T13:00:01Z",
                "provenance": "derived",
            },
            "limitations": [
                "This test receipt is synthetic and is not an external timestamp."
            ],
        }
        validate(self.receipt_schema, receipt)
        self.assertTrue(receipt_semantics_are_valid(receipt))

    def test_receipt_cross_field_mismatch_fails_semantic_check(self):
        digest = "a" * 64
        receipt = {
            "proofstamp": {
                "format": "proofstamp-receipt",
                "format_version": "1.0",
            },
            "artifact": {
                "filename": "synthetic.proofstamp.json",
                "size_bytes": 1,
                "format": "proofstamp-session",
                "format_version": "1.0",
            },
            "fingerprint": {"algorithm": "SHA-256", "sha256": digest},
            "verification": {
                "verified": True,
                "recalculated_sha256": "b" * 64,
                "method": "synthetic mismatch",
            },
            "created_at": {
                "value": "2026-08-21T13:00:01Z",
                "provenance": "derived",
            },
            "limitations": ["Synthetic mismatch fixture."],
        }
        validate(self.receipt_schema, receipt)
        self.assertFalse(receipt_semantics_are_valid(receipt))


if __name__ == "__main__":
    unittest.main()
