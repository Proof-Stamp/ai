# Contributing to ProofStamp AI

Thanks for helping improve ProofStamp AI. This project deals with evidence, provenance, privacy, and cryptographic fingerprints, so correctness matters more than feature count.

## Before you contribute

Read these first:

- `README.md`
- `references/TRUST-MODEL.md`
- the schemas under `schemas/`
- `SECURITY.md` for vulnerability reporting

If your change alters what a ProofStamp claims, captures, hashes, verifies, or timestamps, treat it as a trust-model change, not a copy edit.

## Core rules

Contributions must preserve these rules:

1. Capture only information actually exposed to the capture process.
2. Never invent, reconstruct, or imply access to hidden system instructions, private reasoning, protected host state, or unavailable metadata.
3. Label important evidence with its provenance.
4. Record omissions, exclusions, and user-requested redactions explicitly.
5. Keep private session contents and attachment bytes out of the repository. Synthetic fixtures only.
6. Hash the exact bytes of the exported artifact with SHA-256.
7. Verify by reading the saved artifact back and recalculating its fingerprint.
8. Keep the session artifact separate from its detached receipt.
9. Do not describe a hash or timestamp as proof that underlying content is true, authentic, complete, or provider-signed unless independent evidence supports that claim.
10. Prefer explicit `unavailable` or `excluded` states over guesses.

## Contribution workflow

Do not commit substantive changes directly to `main`.

1. Create or use a focused branch such as `feat/...`, `fix/...`, `docs/...`, or `test/...`.
2. Keep the change narrow enough to review.
3. Add or update tests when behavior, schemas, hashing, verification, or serialization changes.
4. Update documentation when the public format or trust model changes.
5. Open a pull request against `main` and explain what claim or behavior changes.
6. Merge only after the relevant checks pass and the diff has been reviewed.

Small repository-administration changes may be committed directly by maintainers when no meaningful product, format, security, or trust behavior changes.

## Schema changes

The files under `schemas/` are public contracts.

When changing a schema:

- preserve backward compatibility within a published version unless fixing a clear defect
- add a new schema version for breaking changes
- update synthetic examples and tests
- explain any new provenance state, capture method, evidence field, or limitation
- do not weaken validation merely to make an example pass

JSON Schema cannot enforce every semantic invariant. Cross-field requirements, such as equality between an original fingerprint and a recalculated fingerprint, must also be enforced in implementation tests.

## Hashing and serialization

A ProofStamp fingerprint identifies exact bytes, not an abstract JSON object.

Contributors must not assume that semantically equivalent JSON has the same SHA-256. Whitespace, key ordering, encoding, and line endings can change the fingerprint.

The implementation should:

1. serialize the artifact
2. write it to the final file
3. read the saved bytes back
4. calculate SHA-256 from those bytes
5. read or hash again for verification
6. create the detached receipt only after the values match

Do not place the artifact's own SHA-256 inside the artifact being hashed.

## Privacy and fixtures

Never commit real AI session exports, credentials, API keys, private emails, connector data, proprietary documents, or user attachments.

Use synthetic data in `examples/` and `tests/fixtures/`. Test secrets should be obviously fake and nonfunctional.

If a change detects potentially sensitive data, detection should normally warn the user rather than silently altering evidence. Any user-approved redaction must be recorded in the artifact.

## Sources and attachments

A source list should contain sources actually consulted, not everything available to the AI.

Do not copy full third-party documents into ProofStamp artifacts merely to prove they were referenced. Prefer source metadata, references, and hashes when the source bytes are legitimately accessible.

Attachment contents are not embedded in the v1 session artifact by default. Record filename, media type, size, reference, and SHA-256 only when those values are legitimately available.

## AI-assisted contributions

AI-assisted code and documentation are welcome, but the contributor remains responsible for the submitted change.

AI tools must follow the same trust boundary as the product itself. They must not fabricate test results, repository state, platform behavior, source provenance, or inaccessible session metadata.

Before submitting AI-generated changes, inspect the diff, run the relevant tests, and remove unsupported claims.

See `AGENTS.md` for repository-level instructions intended for coding agents.

## Pull request expectations

A useful PR description should state:

- what changed
- why it changed
- whether the trust model or public format is affected
- tests performed
- compatibility implications
- any known limitations

Prefer small PRs. Changes to the trust model, schemas, skill instructions, hashing implementation, and timestamp handoff should be independently reviewable when practical.

## Security reports

Do not open a public issue for a vulnerability that could expose private session data, falsify verification, bypass provenance rules, or misrepresent evidence. Follow `SECURITY.md` instead.

## License

By contributing, you agree that your contribution may be distributed under the repository's Apache License 2.0.