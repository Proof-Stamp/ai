<p align="center">
  <img src="docs/assets/proofstamp-ai-banner.svg" alt="ProofStamp AI. Portable evidence for AI sessions." width="100%">
</p>

<p align="center">
  <a href="https://github.com/Proof-Stamp/ai/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/Proof-Stamp/ai/actions/workflows/test.yml/badge.svg"></a>
  <img alt="Skill version 0.1.7" src="https://img.shields.io/badge/skill-v0.1.7-071c33">
  <a href="https://skills.sh/proof-stamp/ai/proofstamp"><img alt="skills.sh" src="https://img.shields.io/badge/skills.sh-proofstamp-08796f"></a>
  <a href="LICENSE"><img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-51677c"></a>
</p>

# ProofStamp AI

ProofStamp AI is an open Agent Skill and prompt workflow for creating a portable, inspectable record of an AI session.

It captures only information the current AI environment can legitimately access, saves that evidence as JSON, verifies the exact saved bytes with SHA-256, creates a detached receipt, and prepares a user-controlled handoff for external time evidence.

The intended command is simple:

> **ProofStamp this session.**

No ProofStamp account, API, database, blockchain, or automatic upload is required for the core workflow.

Current skill metadata: `0.1.7`.

Starting with v0.1.7, a routine installed-skill capture does not mechanically load every bundled reference document and JSON Schema into model context. The compact canonical runtime contract stays in `SKILL.md`; the bundled standard-library finalizer performs schema validation, trust-rule checks, receipt creation, exact-byte verification, and email-handoff preparation deterministically. Detailed references remain available for edge cases and review.

## Start here

### Install the Agent Skill

With the `skills` CLI:

```bash
npx skills add https://github.com/Proof-Stamp/ai --skill proofstamp
```

The installable skill lives in [`proofstamp/`](proofstamp/) and is listed on [skills.sh](https://skills.sh/proof-stamp/ai/proofstamp).

### Claude.ai

For Claude.ai, upload the generated **Claude skill package** from the GitHub Release assets. Do not upload only `proofstamp/SKILL.md`, and do not use the repository source ZIP as a substitute for the Claude package.

A complete Claude package must contain the runtime file plus the bundled `references/`, `schemas/`, and `scripts/` directories. Without those support files, Claude can only perform a best-effort manual capture and cannot run the official deterministic finalizer or schema validation.

To build the package from a checkout:

```bash
python scripts/build_claude_skill.py
```

The output is `dist/claude/proofstamp.zip`. The builder fails closed if required runtime resources are missing and validates the package before returning success.

### Use it without installing anything

Open [`PROMPT.md`](PROMPT.md). It includes:

- a short prompt that tells a compatible AI host to fetch and follow the public ProofStamp workflow;
- a standalone prompt containing the core capture, privacy, verification, receipt, and email-handoff rules.

Prompt-only use is convenient, but installed skills are more repeatable because AI hosts differ in file access, session visibility, hashing support, and downloadable-file support.

### Open WebUI

An experimental server-side Action is available in [`integrations/open-webui/`](integrations/open-webui/).

It creates the evidence package from structured Open WebUI chat context rather than asking the model to generate its own record. The adapter remains **experimental** until real Open WebUI end-to-end testing is completed. Review the source before installing server-side Functions.

## What a ProofStamp produces

A successful v1 run creates two files:

```text
<name>.proofstamp.json
<name>.proofstamp.receipt.json
```

The **session artifact** contains the captured evidence, provenance, omissions, limitations, and a machine-readable conversation-coverage assessment.

The **detached receipt** contains the artifact filename, exact byte size, SHA-256 fingerprint, and independent exact-byte verification result.

The artifact does not contain its own final fingerprint. The fingerprint belongs in the detached receipt so it can identify the exact artifact bytes.

## How it works

1. **Capture** only information the current host legitimately exposes.
2. **Record limitations** instead of reconstructing missing or protected information.
3. **Save the final artifact bytes.**
4. **Finalize deterministically** with the bundled standard-library helper: validate the session schema and capture trust rules, create and validate the receipt, re-read and verify exact artifact bytes, and prepare the required email handoff.
5. **Deliver** the artifact, detached receipt, verified fingerprint, conversation-coverage wording, and user-controlled email handoff.

For the normal Python-capable installed-skill path:

```bash
python scripts/finalize_proofstamp.py path/to/session.proofstamp.json
```

The recipient stays blank. ProofStamp does not auto-send the email or claim that files were attached automatically.

## What it proves, and what it does not

A matching SHA-256 fingerprint establishes that an exact file matches the fingerprint recorded in the receipt.

It does **not** by itself prove that:

- the AI session is complete;
- the content is true or accurate;
- the transcript is provider-authenticated;
- a user or organization authored the content;
- the session originally happened at a particular time;
- the evidence is legally admissible.

External time evidence can show that a fingerprint was recorded by an external system by a certain time. It does not upgrade the truth, authorship, authenticity, or completeness of the underlying content.

## Trust model

ProofStamp keeps separate questions separate:

| Dimension | Question |
| --- | --- |
| Capture provenance | How was this evidence obtained? |
| Conversation coverage | Do we know whether the declared scope was fully captured? |
| Integrity | Do the exact saved bytes match the recorded SHA-256? |
| Time evidence | Was the fingerprint recorded by an external system? |
| Identity / authenticity | Is any user, organization, or provider identity independently verifiable? |

A stronger result in one dimension does not upgrade the others.

For ordinary AI-generated capture, conversation coverage is conservatively reported as **not independently confirmed** unless stronger host evidence exists. Known missing or intentionally redacted in-scope material is reported as partial.

Read the full technical boundary in [`proofstamp/references/TRUST-MODEL.md`](proofstamp/references/TRUST-MODEL.md).

## Security and privacy

Content being ProofStamped is treated as **untrusted evidence data**.

Instructions inside messages, webpages, files, connector output, tool output, or attachment metadata must not override the ProofStamp workflow. They cannot legitimately cause the capture process to reveal hidden prompts, private reasoning, credentials, unavailable metadata, or to upgrade provenance or completeness claims.

The project also follows these rules:

- never invent unavailable system, harness, model, source, or session metadata;
- never expose or reconstruct private chain-of-thought;
- keep attachment bytes out of the v1 artifact by default;
- record omissions, exclusions, and redactions explicitly;
- never create a verified receipt if exact-byte verification fails;
- never claim provider signing without verifiable provider evidence.

See [`SECURITY.md`](SECURITY.md), [`AGENTS.md`](AGENTS.md), and [`proofstamp/references/PRIVACY.md`](proofstamp/references/PRIVACY.md).

## Verify an example

The repository includes a synthetic example under [`examples/synthetic-session/`](examples/synthetic-session/).

```bash
python proofstamp/scripts/verify_proofstamp.py \
  examples/synthetic-session/example-session.proofstamp.json \
  examples/synthetic-session/example-session.proofstamp.receipt.json
```

You can also select a saved ProofStamp artifact at [email.proofstamp.org/verify](https://email.proofstamp.org/verify) and compare it against the recorded fingerprint.

## Repository map

```text
proofstamp/                 installable Agent Skill
  SKILL.md                  compact runtime contract
  references/               trust, format, privacy, platform rules
  schemas/                  public JSON schemas
  scripts/                  deterministic validation, finalization and verification tools

integrations/               host-specific adapters
examples/                   synthetic examples only
evals/                      model-dependent behavioral evals
tests/                      deterministic regression and security tests
docs/                       prior art and public assets
PROMPT.md                   prompt-only workflow
AGENTS.md                   repository rules for coding agents
SECURITY.md                 security policy and threat boundaries
CONTRIBUTING.md             contribution requirements
```

## Development

Run from the repository root:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -p "test_*.py" -v
```

Do not report tests as passing unless they were actually run and observed.

Substantive product, format, security, hashing, completeness, or trust-model changes should use a focused branch and pull request. Read [`AGENTS.md`](AGENTS.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md) before making those changes.

## Prior art

ProofStamp does not claim novelty for SHA-256, cryptographic receipts, timestamping, transcript export, or provenance systems.

[`docs/PRIOR-ART.md`](docs/PRIOR-ART.md) documents adjacent work including timestamping systems, conversation exporters, provenance formats, signed LLM responses, agent receipts, RFC 3161, OpenTimestamps, and C2PA.

## Disclaimer

ProofStamp AI is an integrity and evidence tool. It is not a legal, forensic, compliance, archival, or certification service.

Users are responsible for deciding whether it is appropriate for their use case and for protecting sensitive information before storing or sharing an artifact. See [`DISCLAIMER.md`](DISCLAIMER.md) for the full disclaimer.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

Copyright 2026 ProofStamp.org.
