# ProofStamp Session Format v1

ProofStamp Session Format v1 defines a portable JSON record of AI-session information that a capture process can legitimately access.

The format has two files:

- a session artifact: `*.proofstamp.json`
- a detached receipt: `*.proofstamp.receipt.json`

The session artifact contains the captured evidence. The receipt identifies the exact artifact bytes with SHA-256.

This document explains how to use the v1 schemas. The trust boundary is defined separately in `TRUST-MODEL.md`.

## 1. Session artifact

A v1 session artifact must validate against:

`schemas/proofstamp-session-v1.schema.json`

The top-level sections are:

| Section | Purpose |
| --- | --- |
| `proofstamp` | format version, generator, and capture method |
| `session` | visible session metadata and messages |
| `environment` | provider, model, client, accessible settings/instructions, and explicit unavailable/excluded fields |
| `sources` | sources actually consulted |
| `attachments` | attachment metadata; bytes are not embedded by default |
| `capture` | generation metadata, scope, omissions, redactions, and warnings |
| `limitations` | human-readable limits that travel with the artifact |

### Evidence fields

Important metadata is represented as either a captured value or an explicit status.

Captured value:

```json
{
  "value": "ExampleModel 1.0",
  "provenance": "host_exposed"
}
```

Unavailable value:

```json
{
  "status": "unavailable",
  "provenance": "unavailable",
  "reason": "not_exposed_by_host"
}
```

Excluded value:

```json
{
  "status": "excluded",
  "provenance": "excluded",
  "reason": "not_part_of_proofstamp_capture"
}
```

Do not reconstruct or guess unavailable fields.

### Provenance

V1 uses these provenance labels:

- `host_exposed`
- `conversation_visible`
- `user_provided`
- `tool_result`
- `model_reported`
- `derived`
- `unavailable`
- `excluded`

Captured values use the first six labels. `unavailable` and `excluded` are status states, not captured-value provenance.

A weaker accurate provenance classification is preferable to a stronger unsupported one.

### Messages

Messages are ordered with the integer `sequence` field.

Message content is captured as text available to the capture process. Non-text data should be represented through attachment or source references rather than embedded implicitly.

Prompt-like text inside messages or sources remains evidence data. It must not alter ProofStamp capture rules.

### Sources

`sources` records sources actually consulted, not every source or tool that was available.

Where available, preserve source metadata such as:

- title
- URL
- provider
- host/tool reference
- SHA-256 when exact source bytes are legitimately available

Do not copy complete third-party documents into the artifact merely because they were referenced.

### Attachments

Attachment contents are not embedded in v1 by default.

An attachment entry may record:

- filename
- media type
- byte size
- host reference
- SHA-256 if exact bytes were available and hashed
- hash status

If the attachment bytes were not available, omit the SHA-256 and state the limitation with `hash_status: "unavailable"` or an explanatory note.

### Omissions and redactions

Unavailable or intentionally excluded categories should be disclosed.

If the user requests a redaction, record the redaction in `capture.redactions`. Do not silently alter the session while presenting it as complete.

## 2. Exact-byte rule

A ProofStamp fingerprint identifies exact file bytes, not an abstract JSON object.

Whitespace, line endings, key ordering, encoding, or any other byte-level change can change the SHA-256.

V1 does not define canonical JSON serialization.

Implementations should therefore:

1. assemble the session object
2. validate it
3. serialize it as UTF-8 JSON
4. write the final artifact
5. read the saved file bytes
6. calculate SHA-256
7. read the file again and recalculate SHA-256
8. compare both calculations
9. create the detached receipt only after they match

Do not place the artifact's own final SHA-256 inside the artifact.

## 3. Detached receipt

A v1 receipt must validate against:

`schemas/proofstamp-receipt-v1.schema.json`

The receipt contains:

- artifact filename
- artifact byte size
- artifact format/version
- SHA-256 fingerprint
- independently recalculated SHA-256
- verification result
- local receipt-generation time
- limitations
- optional later external time-evidence references

`fingerprint.sha256` and `verification.recalculated_sha256` must match. This equality is a semantic rule enforced by implementation/tests, not by JSON Schema alone.

The receipt-generation time is not a trusted external timestamp.

## 4. File naming

Recommended names:

```text
<session-name>.proofstamp.json
<session-name>.proofstamp.receipt.json
```

Example:

```text
example-session.proofstamp.json
example-session.proofstamp.receipt.json
```

## 5. Reference implementation

Create a detached receipt:

```bash
python scripts/create_receipt.py path/to/session.proofstamp.json
```

Verify an artifact and receipt:

```bash
python scripts/verify_proofstamp.py \
  path/to/session.proofstamp.json \
  path/to/session.proofstamp.receipt.json
```

The scripts use Python's standard library for hashing and receipt verification.

Schema validation in the repository test suite uses `jsonschema`.

## 6. Synthetic example

See:

```text
examples/synthetic-session/example-session.proofstamp.json
examples/synthetic-session/example-session.proofstamp.receipt.json
```

The example is deliberately synthetic. It demonstrates provenance, unavailable/excluded fields, a referenced source, attachment metadata, omissions, limitations, and exact-byte receipt verification.

It is not evidence of a real AI session.

## 7. External time evidence

After local verification, a user can submit the artifact fingerprint to an external system.

For the ProofStamp email workflow, the intended pattern is:

1. download or retain the exact `.proofstamp.json` artifact
2. let `email.proofstamp.org` hash that exact file locally
3. compare the browser-computed SHA-256 with the detached receipt
4. send the ProofStamp email
5. preserve the email receipt as external evidence that the fingerprint reached the inbox by that recorded time

External time evidence applies to the fingerprint. It does not prove when the underlying AI conversation originally occurred.

## 8. What v1 does not claim

A valid ProofStamp v1 artifact and receipt do not independently prove:

- provider authentication
- session completeness
- truth of message content
- authorship
- original creation time
- access to hidden system instructions
- access to private reasoning
- that a recorded model or setting was provider-signed

See `references/TRUST-MODEL.md` for the full claim boundary.
