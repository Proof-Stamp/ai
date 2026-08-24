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

REQUIRED_CONTRACT_OLD = """## Required contract

Before capture, read and follow these bundled files:

1. `references/TRUST-MODEL.md`
2. `references/FORMAT.md`
3. `references/PRIVACY.md`
4. `references/PLATFORM-CAPABILITIES.md`
5. `schemas/proofstamp-session-v1.schema.json`
6. `schemas/proofstamp-receipt-v1.schema.json`

The trust model and schemas are authoritative. If this file conflicts with them, use the stricter interpretation and disclose the conflict rather than inventing a workaround.
"""

REQUIRED_CONTRACT_CLAUDE = """## Required contract

The bundled trust model and schemas remain authoritative:

1. `references/TRUST-MODEL.md`
2. `references/FORMAT.md`
3. `references/PRIVACY.md`
4. `references/PLATFORM-CAPABILITIES.md`
5. `schemas/proofstamp-session-v1.schema.json`
6. `schemas/proofstamp-receipt-v1.schema.json`

For a routine Claude.ai ProofStamp, do **not** mechanically open every bundled reference or schema before starting. This `skill.md` contains the operating contract. Consult a specific reference only when a capability, privacy, format, or trust question is ambiguous. The bundled standard-library finalizer validates the completed artifact against the actual v1 schemas before creating a receipt.

If this file conflicts with the trust model or schemas, use the stricter interpretation and disclose the conflict rather than inventing a workaround.
"""

HASHING_OLD = """Preferred method when Python 3 is available:

```bash
python scripts/create_receipt.py path/to/session.proofstamp.json
python scripts/verify_proofstamp.py \\
  path/to/session.proofstamp.json \\
  path/to/session.proofstamp.receipt.json
```

The creation script reads the saved artifact twice before creating the receipt. The verification script hashes the saved artifact again and compares filename, size, fingerprint, and receipt fields.
"""

HASHING_CLAUDE = """Preferred Claude.ai method when Python 3 is available:

```bash
python scripts/finalize_proofstamp.py path/to/session.proofstamp.json
```

Run this **once after the final artifact has been written**. It validates the session against the bundled v1 JSON Schema using only Python's standard library, reads and hashes the exact saved artifact bytes twice before creating the receipt, validates the receipt schema, independently verifies the saved artifact against the receipt, and returns the verified SHA-256, byte size, completeness status, `mailto:` URI, and fallback email text.

Do not separately run `create_receipt.py`, `verify_proofstamp.py`, or `create_mailto.py` after a successful finalizer run. Those lower-level scripts remain available for debugging or hosts that cannot use the finalizer.
"""

EMAIL_OLD = """Preferred method when Python 3 is available:

```bash
python scripts/create_mailto.py \\
  path/to/session.proofstamp.json \\
  path/to/session.proofstamp.receipt.json
```

Render the resulting URI as a clickable link labeled:
"""

EMAIL_CLAUDE = """When the bundled finalizer succeeds, use the `mailto` value it already returned. Do not run another command merely to recreate the same handoff.

Render that URI as a clickable link labeled:
"""


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


def adapt_claude_body(body: str) -> str:
    replacements = [
        (REQUIRED_CONTRACT_OLD, REQUIRED_CONTRACT_CLAUDE),
        (HASHING_OLD, HASHING_CLAUDE),
        (EMAIL_OLD, EMAIL_CLAUDE),
    ]
    adapted = body
    for old, new in replacements:
        if adapted.count(old) != 1:
            raise ValueError("canonical SKILL.md changed: Claude adapter replacement anchor not found exactly once")
        adapted = adapted.replace(old, new, 1)
    return adapted


def claude_skill_md(canonical_text: str) -> str:
    frontmatter, body = split_frontmatter(canonical_text)
    version = canonical_version(frontmatter)
    manifest = (
        "---\n"
        f"name: {CLAUDE_NAME}\n"
        f"description: {CLAUDE_DESCRIPTION}\n"
        "---\n"
        f"<!-- Generated from canonical ProofStamp skill version {version}. Claude adapter changes execution mechanics only; trust boundaries remain canonical. -->\n\n"
    )
    return manifest + adapt_claude_body(body)


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
