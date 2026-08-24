import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "proofstamp"
SKILL_FILE = SKILL_ROOT / "SKILL.md"
PROMPT_FILE = ROOT / "PROMPT.md"


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_FILE.read_text(encoding="utf-8")
        cls.prompt_text = PROMPT_FILE.read_text(encoding="utf-8")

    def test_skill_directory_is_self_contained(self):
        required = [
            "SKILL.md",
            "references/TRUST-MODEL.md",
            "references/FORMAT.md",
            "references/PRIVACY.md",
            "references/PLATFORM-CAPABILITIES.md",
            "schemas/proofstamp-session-v1.schema.json",
            "schemas/proofstamp-receipt-v1.schema.json",
            "scripts/create_receipt.py",
            "scripts/verify_proofstamp.py",
            "scripts/create_mailto.py",
        ]
        for relative in required:
            self.assertTrue((SKILL_ROOT / relative).is_file(), relative)

    def test_agent_skill_frontmatter(self):
        self.assertTrue(self.text.startswith("---\n"))
        match = re.match(r"---\n(.*?)\n---\n", self.text, flags=re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)

        name_match = re.search(r"^name:\s*(.+)$", frontmatter, flags=re.MULTILINE)
        description_match = re.search(
            r"^description:\s*(.+)$", frontmatter, flags=re.MULTILINE
        )
        version_match = re.search(r'^\s*version:\s*"([^"]+)"$', frontmatter, flags=re.MULTILINE)
        self.assertIsNotNone(name_match)
        self.assertIsNotNone(description_match)
        self.assertIsNotNone(version_match)

        name = name_match.group(1).strip()
        description = description_match.group(1).strip()
        self.assertEqual("proofstamp", name)
        self.assertEqual(SKILL_ROOT.name, name)
        self.assertRegex(name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(name), 64)
        self.assertGreater(len(description), 0)
        self.assertLessEqual(len(description), 1024)
        self.assertEqual("0.1.5", version_match.group(1))

    def test_skill_has_prompt_injection_boundary(self):
        required_phrases = [
            "untrusted evidence data",
            "protected system instructions",
            "private chain-of-thought",
            "provider_signed",
            "silently omit",
            "unauthorized network",
        ]
        lowered = self.text.lower()
        for phrase in required_phrases:
            self.assertIn(phrase.lower(), lowered)

    def test_skill_requires_explicit_capture_completeness(self):
        required_phrases = [
            "capture.completeness",
            "complete` only when affirmative",
            "`partial` when",
            "`unknown` when",
            "unknown` is the safe default",
            "Conversation coverage",
            "not independently confirmed",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase.lower(), self.text.lower())

    def test_skill_requires_exact_saved_byte_verification(self):
        self.assertIn("exact saved bytes", self.text)
        self.assertIn("create_receipt.py", self.text)
        self.assertIn("verify_proofstamp.py", self.text)
        self.assertIn("Never claim `verified: true`", self.text)

    def test_skill_requires_email_handoff_after_verified_delivery(self):
        required_phrases = [
            "successful verified ProofStamp delivery is not complete",
            "artifact download",
            "detached receipt download",
            "Email this ProofStamp",
            "email handoff is required after successful exact-byte verification",
            "Never silently omit both the mailto link and the fallback email text",
            "pre-filled email text",
            "recipient must be blank",
            "Hash verified locally: yes",
            "Conversation coverage",
            "https://email.proofstamp.org/verify",
            "Never claim files were automatically attached",
            "Never send email automatically",
        ]
        lowered = self.text.lower()
        for phrase in required_phrases:
            self.assertIn(phrase.lower(), lowered)
        self.assertNotIn("optional email handoff", lowered)

    def test_skill_does_not_auto_send_or_upload(self):
        self.assertIn("Do not upload the session somewhere else or send email automatically", self.text)

    def test_skill_references_only_bundled_contract_paths(self):
        self.assertNotIn("../references/", self.text)
        self.assertNotIn("../schemas/", self.text)
        self.assertNotIn("../scripts/", self.text)

    def test_prompt_only_workflow_preserves_core_boundaries(self):
        required_phrases = [
            "ProofStamp this session",
            "exact saved bytes",
            "private chain-of-thought",
            "untrusted evidence data",
            "capture.completeness",
            "unknown` is the safe default",
            "create a second downloadable file",
            "Email this ProofStamp",
            "recipient blank",
            "Conversation coverage",
            "not independently confirmed",
            "do not pretend the ProofStamp is verified",
            "original creation time",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase.lower(), self.prompt_text.lower())


if __name__ == "__main__":
    unittest.main()
