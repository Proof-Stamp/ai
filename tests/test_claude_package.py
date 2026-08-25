import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "scripts" / "build_claude_skill.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_claude_skill", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ClaudePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()

    def test_manifest_constraints_and_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "proofstamp.zip"
            self.builder.build(REPO_ROOT, output)

            with ZipFile(output) as zf:
                names = zf.namelist()
                self.assertIn("proofstamp/skill.md", names)
                self.assertNotIn("proofstamp/SKILL.md", names)
                self.assertTrue(all(name.startswith("proofstamp/") for name in names))
                for required in self.builder.REQUIRED_PACKAGE_FILES:
                    self.assertIn(required, names)

                skill_text = zf.read("proofstamp/skill.md").decode("utf-8")
                self.assertTrue(skill_text.startswith("---\n"))
                manifest_end = skill_text.find("\n---\n", 4)
                self.assertNotEqual(-1, manifest_end)
                manifest = skill_text[4:manifest_end]

                fields = {}
                for line in manifest.splitlines():
                    key, value = line.split(":", 1)
                    fields[key.strip()] = value.strip()

                self.assertEqual("proofstamp", fields["name"])
                self.assertLessEqual(len(fields["name"]), 64)
                self.assertLessEqual(len(fields["description"]), 200)

    def test_package_copies_canonical_support_files_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "proofstamp.zip"
            self.builder.build(REPO_ROOT, output)

            with ZipFile(output) as zf:
                for source_path, archive_name in self.builder.package_files(REPO_ROOT / "proofstamp"):
                    self.assertEqual(source_path.read_bytes(), zf.read(archive_name), archive_name)

    def test_incomplete_source_tree_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            source = repo_root / "proofstamp"
            shutil.copytree(REPO_ROOT / "proofstamp", source)
            (source / "scripts" / "finalize_proofstamp.py").unlink()

            with self.assertRaisesRegex(FileNotFoundError, "finalize_proofstamp.py"):
                self.builder.build(repo_root, Path(tmp) / "proofstamp.zip")

    def test_adapter_changes_manifest_only_and_keeps_canonical_runtime(self):
        canonical_text = (REPO_ROOT / "proofstamp" / "SKILL.md").read_text(encoding="utf-8")
        _, canonical_body = self.builder.split_frontmatter(canonical_text)
        adapted = self.builder.claude_skill_md(canonical_text)
        adapted_lower = adapted.lower()

        self.assertTrue(adapted.endswith(canonical_body))
        self.assertIn("do not pre-read bundled references or json schemas on every run", adapted_lower)
        self.assertIn("python scripts/finalize_proofstamp.py", adapted)
        self.assertIn("uses only Python's standard library", adapted)
        self.assertIn("rejects `ai_generated` + `complete`", adapted)
        self.assertNotIn("Before capture, read and follow these bundled files:", adapted)

        trust_phrases = [
            "untrusted evidence data",
            "protected system instructions",
            "private chain-of-thought",
            "provider_signed",
            "capture.completeness",
            "For `ai_generated` captures, do not use `complete`",
            "Conversation coverage",
            "not independently confirmed",
            "Never claim `verified: true`",
            "successful verified ProofStamp delivery is not complete",
            "Never send email automatically",
        ]
        for phrase in trust_phrases:
            self.assertIn(phrase, adapted)

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.zip"
            second = Path(tmp) / "second.zip"
            self.builder.build(REPO_ROOT, first)
            self.builder.build(REPO_ROOT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
