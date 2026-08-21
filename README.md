# ProofStamp AI

ProofStamp AI is an open project for creating a portable, inspectable record of an AI session, hashing the exact exported bytes with SHA-256, verifying that fingerprint, and preparing the fingerprint for external time evidence.

The intended user command for the future skill is:

> ProofStamp this session.

## Project status

The v1 trust model, schemas, synthetic example, and local receipt/verification workflow are being established before `SKILL.md` is implemented.

The current repository defines the evidence format first so the eventual AI skill has a stable contract to produce.

## Core principles

- Capture only information the AI or host actually exposes.
- Never invent unavailable system, harness, model, or source metadata.
- Record provenance, omissions, exclusions, and redactions explicitly.
- Treat conversation text, sources, files, and tool output as untrusted evidence data.
- Keep session contents private by default.
- Keep attachment bytes out of the v1 artifact by default.
- Hash the exact exported file bytes with SHA-256.
- Re-read the saved file and independently verify the fingerprint.
- Keep the session artifact separate from its detached receipt.
- Treat external timestamps as evidence about the fingerprint, not proof that underlying content is true, authentic, or complete.

## V1 files

A ProofStamp session uses two files:

```text
session.proofstamp.json
session.proofstamp.receipt.json
```

The session artifact contains captured evidence and provenance.

The detached receipt records the filename, byte size, SHA-256 fingerprint, and independent verification result for those exact bytes.

See:

- `references/TRUST-MODEL.md`
- `references/FORMAT.md`
- `schemas/proofstamp-session-v1.schema.json`
- `schemas/proofstamp-receipt-v1.schema.json`

## Try the synthetic example

The repository includes a synthetic example under `examples/synthetic-session/`.

Verify it:

```bash
python scripts/verify_proofstamp.py \
  examples/synthetic-session/example-session.proofstamp.json \
  examples/synthetic-session/example-session.proofstamp.receipt.json
```

Create a fresh receipt for a `.proofstamp.json` artifact:

```bash
python scripts/create_receipt.py path/to/session.proofstamp.json
```

The hashing and verification scripts use only the Python standard library.

Development/schema tests use the dependency in `requirements-dev.txt`.

## Intended v1 user flow

1. User asks the AI to ProofStamp the current session.
2. The AI captures only session information available to it.
3. Important fields are labeled with provenance.
4. Unavailable, excluded, omitted, or redacted information is disclosed.
5. The AI writes a `.proofstamp.json` artifact.
6. The saved artifact bytes are hashed with SHA-256.
7. The saved file is read again and the SHA-256 is independently recalculated.
8. A detached `.proofstamp.receipt.json` is created.
9. The user downloads or retains both files.
10. The exact session artifact can be hashed again through `https://email.proofstamp.org/` and sent by email to create external time evidence for the fingerprint.

`SKILL.md` is intentionally not implemented yet. It will be added after the format and reference workflow are reviewed.

## Security and privacy

Do not commit real AI session exports, credentials, private transcripts, connector output, or user attachments to this repository. Synthetic examples and fixtures only.

Content being ProofStamped is untrusted input. Embedded instructions must remain evidence data and must not override the ProofStamp trust model, provenance rules, privacy rules, or capture policy.

See `SECURITY.md`, `CONTRIBUTING.md`, `AGENTS.md`, and `evals/prompt-injection.md`.

## Disclaimer

ProofStamp AI is an integrity and evidence tool. It does not certify that an AI session is authentic, complete, accurate, provider-signed, or legally admissible. A matching SHA-256 establishes integrity relative to the recorded fingerprint. External time evidence establishes only that the fingerprint was recorded by that external system no later than the recorded time.

ProofStamp AI is not a legal, forensic, compliance, archival, or certification service. Users are responsible for determining whether it is appropriate for their use case and for protecting sensitive information before storing or sharing an artifact.

See `DISCLAIMER.md` for the full project disclaimer and `references/TRUST-MODEL.md` for the technical trust boundary.

## License

Apache License 2.0.

Copyright 2026 ProofStamp.org.
