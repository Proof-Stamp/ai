# ProofStamp AI

ProofStamp AI is an open skill for creating a portable, inspectable record of an AI session, hashing the exact exported bytes with SHA-256, verifying that fingerprint, and preparing the record for external timestamp evidence.

The intended user command is simple:

> ProofStamp this session.

## Project status

Early development. The session format, trust model, privacy rules, and skill workflow are being defined before the first public release.

## Core principles

- Capture only information the AI or host actually exposes.
- Never invent unavailable system, harness, model, or source metadata.
- Record provenance and omissions explicitly.
- Keep session contents private by default.
- Hash the exact exported file bytes with SHA-256.
- Verify the hash independently before presenting it as complete.
- Treat external timestamps as evidence about the fingerprint, not proof that the underlying content is true or complete.
- Keep the format open, inspectable, and portable across AI platforms.

## Planned v1 flow

1. Capture the accessible session record.
2. Label important fields with their provenance.
3. Disclose unavailable, excluded, or redacted information.
4. Export a `.proofstamp.json` artifact.
5. Hash the exact file bytes with SHA-256.
6. Re-read and verify the fingerprint.
7. Create a detached receipt.
8. Let the user download the artifact and timestamp its fingerprint through ProofStamp via Email.

## Security and privacy

Do not commit real session exports, credentials, private transcripts, or user data to this repository. Synthetic examples only.

See `SECURITY.md` once added for vulnerability reporting guidance.

## License

Apache License 2.0.

Copyright 2026 ProofStamp.org.
