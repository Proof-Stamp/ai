import importlib.util
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

    def test_adapter_preserves_canonical_skill_body(self):
        canonical_text = (REPO_ROOT / "proofstamp" / "SKILL.md").read_text(encoding="utf-8")
        _, canonical_body = self.builder.split_frontmatter(canonical_text)
        adapted = self.builder.claude_skill_md(canonical_text)
        adapter_end = adapted.find("\n---\n", 4)
        adapted_body = adapted[adapter_end + 5 :]
        marker_end = adapted_body.find("\n\n")
        adapted_body = adapted_body[marker_end + 2 :]
        self.assertEqual(canonical_body, adapted_body)

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.zip"
            second = Path(tmp) / "second.zip"
            self.builder.build(REPO_ROOT, first)
            self.builder.build(REPO_ROOT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
