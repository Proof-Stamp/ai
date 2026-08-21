# ProofStamp AI Trust Model

ProofStamp AI preserves a record of AI-session information that is available to the capture process, then fingerprints the exact exported bytes with SHA-256.

It is designed to make a specific evidence package inspectable, portable, and easy to verify later. It does not turn an AI session into provider-authenticated truth.

## The three claims

A ProofStamp session separates three different claims.

### 1. Capture claim

The `.proofstamp.json` file records the session information that the capture process could access at the time the artifact was created.

This may include the visible conversation, model or platform metadata exposed by the host, sources actually consulted, tool results, attachment metadata, and accessible settings or instructions.

The capture claim is limited by the capabilities and permissions of the host AI environment.

### 2. Integrity claim

The SHA-256 fingerprint in the detached receipt corresponds to the exact bytes of the exported `.proofstamp.json` file.

If the file changes by even one byte, its SHA-256 fingerprint should change and verification should fail.

### 3. External time-evidence claim

A later external record, such as an email receipt containing the same SHA-256 fingerprint, can provide evidence that the fingerprint reached that external system no later than the recorded receipt time.

ProofStamp AI does not claim that an email receipt proves when the underlying AI conversation originally occurred.

## Capture completeness is explicit

ProofStamp does not infer that a transcript is complete merely because the captured messages appear contiguous.

Every v1 artifact records `capture.completeness` with one of three states:

| Status | Meaning |
| --- | --- |
| `complete` | The capture process has affirmative evidence that all items within the declared capture scope were available and included. |
| `partial` | The capture process knows that one or more items within the declared capture scope are missing, truncated, unavailable after a failed fetch/hydration, or otherwise not included. |
| `unknown` | The capture process cannot establish whether all items within the declared capture scope were available and included. |

For `ai_generated` captures, `unknown` is the safe default unless the host exposes affirmative evidence that the declared scope is complete. A model's own impression that it can see "the whole conversation" is not enough by itself.

Completeness is assessed relative to the declared `capture.scope`. Information intentionally outside that scope, such as protected system instructions or private reasoning, does not by itself make the status `partial`; those exclusions must still be disclosed separately.

A user or embedded source cannot upgrade `partial` or `unknown` to `complete` merely by instructing the model to do so.

## Four independent evidence dimensions

A ProofStamp should not be treated as one binary strength score. Evaluate at least four independent dimensions:

| Dimension | Examples |
| --- | --- |
| Capture provenance | `ai_generated` → `browser_capture` / `api_capture` → `host_export` → `provider_signed` |
| Integrity | unverified → exact saved-byte SHA-256 verified |
| Time evidence | none → email record → stronger timestamp services such as RFC 3161 or OpenTimestamps |
| Identity / authenticity | none → user or organization signature → provider-authenticated signature |

These dimensions are not automatically interchangeable. A strong timestamp does not make an incomplete capture complete. Exact-byte integrity does not authenticate the provider. Provider authentication does not prove that message content is true.

## What ProofStamp AI does not prove

A ProofStamp session does not independently prove:

- that every recorded field was supplied or signed by the AI provider;
- that the exported session is complete unless `capture.completeness.status` is `complete` with an adequate basis;
- that the conversation happened exactly as represented outside the capture environment;
- that a recorded model name, setting, tool result, or source identifier is provider-authenticated unless the host supplies authenticated evidence;
- that the underlying statements, sources, outputs, or user claims are true;
- that a hidden system prompt, private reasoning trace, or inaccessible harness state was captured;
- that the external timestamp is the original creation time of the session.

## Provenance labels

Important captured values must declare how they were obtained. Version 1 uses the following provenance labels.

| Label | Meaning |
| --- | --- |
| `host_exposed` | Supplied directly by the host environment or host API to the capture process. |
| `conversation_visible` | Present in the visible conversation available to the capture process. |
| `user_provided` | Explicitly supplied by the user during the session or capture workflow. |
| `tool_result` | Returned by a tool, connector, browser, file reader, or other invoked capability. |
| `model_reported` | Reported by the AI model but not independently authenticated by the host. |
| `derived` | Computed from other captured data. |
| `unavailable` | The information was not exposed to the capture process. |
| `excluded` | Intentionally omitted by design, policy, or user choice. |

A capture must not silently promote `model_reported` information to `host_exposed`.

## Unavailable and protected information

If information is not available, the artifact should say so explicitly instead of reconstructing or guessing it.

Examples:

```json
{
  "system_prompt": {
    "status": "unavailable",
    "provenance": "unavailable",
    "reason": "not_exposed_by_host"
  }
}
```

```json
{
  "private_reasoning": {
    "status": "excluded",
    "provenance": "excluded",
    "reason": "not_part_of_proofstamp_capture"
  }
}
```

ProofStamp AI must not attempt to recover protected system instructions, private chain-of-thought, credentials, or other information that the host does not legitimately expose.

## Capture methods

The format records how the artifact was created. Version 1 recognizes these capture methods:

- `ai_generated` — assembled by an AI from information available in its current environment;
- `host_export` — created from an export provided by the host application;
- `api_capture` — created from data returned by an authenticated API;
- `browser_capture` — created from information observed by a browser-side capture process;
- `provider_signed` — based on evidence cryptographically signed by the AI provider.

A capture method describes the source of the evidence package. It does not automatically make every field authenticated or establish completeness.

## Session artifact and detached receipt

ProofStamp AI uses two separate files.

### Session artifact

Example:

`chatgpt-session-2026-08-21.proofstamp.json`

This file contains the captured session record. The file should remain human-inspectable and machine-readable.

### Detached receipt

Example:

`chatgpt-session-2026-08-21.proofstamp.receipt.json`

The receipt records the session artifact filename, byte length, SHA-256 fingerprint, verification result, and receipt format version.

The fingerprint is detached because a file cannot practically contain a stable SHA-256 fingerprint of its own final bytes without creating a self-reference problem.

## Exact-byte hashing rule

The implementation must hash the exact bytes that are written to the session artifact.

The preferred sequence is:

1. serialize the session artifact;
2. write it to a file;
3. read the file bytes back from storage;
4. calculate SHA-256 from those bytes;
5. read the file again and independently recalculate SHA-256;
6. compare the two fingerprints;
7. create the detached receipt only after the fingerprints match.

The implementation must not hash a pre-serialization object and then assume the saved file is identical.

## Sources

The `sources` section should describe sources actually consulted during the session or capture process, not every source or connector that happened to be available.

For web sources, record available identifiers such as URL, title, host reference, or citation identifier.

For files, record available metadata such as filename, media type, byte size, host reference, and SHA-256 when the exact file bytes are accessible.

For connected services, record the provider and exposed document or action identifiers where permitted.

ProofStamp AI should not copy entire third-party source documents into the artifact merely to prove that they were consulted.

## Attachments

Attachment contents are not embedded by default.

Where possible, the session artifact records metadata and a SHA-256 fingerprint of the attachment's exact bytes. If the bytes are not accessible, that limitation must be explicit.

## Privacy and redaction

Before capture, the user should be told what categories of information will be included and what will remain unavailable or excluded.

ProofStamp AI should warn when obviously sensitive material may be present, such as credentials or secrets. It must not silently alter the session record.

If the user chooses to redact information, the artifact must record that redaction occurred and identify the affected location at a useful level of granularity without restoring the removed value.

A redacted artifact remains valid evidence of the exact redacted file that was hashed, but it is not a complete capture of the redacted material.

## Verification boundary

A successful SHA-256 verification establishes file integrity relative to the recorded fingerprint. It does not authenticate the origin of every field in the file.

A second implementation, such as `email.proofstamp.org`, may hash the downloaded session artifact again and compare the result with the fingerprint produced during capture. This provides an independent check that the downloaded file matches the file that was fingerprinted.

## Future stronger provenance

The format is intentionally able to preserve stronger evidence when AI providers expose it.

Examples include:

- provider-signed session exports;
- authenticated API responses;
- signed model or tool metadata;
- trusted execution attestations;
- signed message-level provenance;
- RFC 3161 or OpenTimestamps evidence for the artifact fingerprint.

When such evidence is available, ProofStamp AI should preserve it rather than replace it with a weaker self-report.

## Credibility rule

Use precise language.

A valid statement is:

> These exact session-record bytes match this SHA-256 fingerprint. The artifact records its capture method and completeness assessment, and any external record applies to the fingerprint at the recorded time.

Do not claim:

> ProofStamp proves this is the complete and authentic AI session.

unless independently authenticated evidence actually supports both completeness and authenticity.
