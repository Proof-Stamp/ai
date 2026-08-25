#!/usr/bin/env python3
"""Build a deterministic Claude.ai custom Skill ZIP from the canonical ProofStamp skill."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

CLAUDE_NAME = "proofstamp"
CLAUDE_DESCRIPTION = (
    "Preserve an AI session as a portable evidence record, verify exact saved bytes with SHA-256, "
    "create a detached receipt, and prepare a user-controlled email ProofStamp."
)
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("canonical SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("canonical SKILL.md frontmatter is not terminated")
    return text[4:end], text[end + 5 :]


def canonical_version(frontmatter: str) -> str:
    match = re.search(r'^\s*version:\s*["\']?([^"\'\n]+)', frontmatter, flags=re.MULTILINE)
    if not match:
        raise ValueError("canonical SKILL.md is missing metadata.version")
    return match.group(1).strip()


def claude_skill_md(canonical_text: str) -> str:
    """Replace only manifest frontmatter; keep the canonical runtime body byte-for-byte."""
    frontmatter, body = split_frontmatter(canonical_text)
    version = canonical_version(frontmatter)
    manifest = (
        "---\n"
        f"name: {CLAUDE_NAME}\n"
        f"description: {CLAUDE_DESCRIPTION}\n"
        "---\n"
        f"<!-- Generated from canonical ProofStamp skill version {version}. Claude packaging changes manifest mechanics only; runtime trust and execution rules remain canonical. -->\n\n"
    )
    return manifest + body


def package_files(source_dir: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source_dir)
        if rel.as_posix() == "SKILL.md":
            continue
        files.append((path, f"proofstamp/{rel.as_posix()}"))
    return files


def write_member(zf: ZipFile, archive_name: str, data: bytes) -> None:
    info = ZipInfo(archive_name, FIXED_ZIP_TIME)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, data)


def build(repo_root: Path, output: Path) -> Path:
    source_dir = repo_root / "proofstamp"
    canonical = source_dir / "SKILL.md"
    if not canonical.is_file():
        raise FileNotFoundError(f"missing canonical skill: {canonical}")
    if len(CLAUDE_NAME) > 64:
        raise ValueError("Claude skill name exceeds 64 characters")
    if len(CLAUDE_DESCRIPTION) > 200:
        raise ValueError("Claude skill description exceeds 200 characters")

    skill_text = claude_skill_md(canonical.read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        write_member(zf, "proofstamp/skill.md", skill_text.encode("utf-8"))
        for source_path, archive_name in package_files(source_dir):
            write_member(zf, archive_name, source_path.read_bytes())

    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/claude/proofstamp.zip"),
        help="ZIP output path (default: dist/claude/proofstamp.zip)",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output = args.output if args.output.is_absolute() else repo_root / args.output
    built = build(repo_root, output)
    print(built)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
