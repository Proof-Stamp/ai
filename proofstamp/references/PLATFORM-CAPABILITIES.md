# Platform capability guidance

ProofStamp is designed to run across AI hosts with different capabilities. The skill must adapt to what the current environment actually exposes and must not invent stronger evidence when a capability is missing.

## Verified platform profiles

Platform-specific profiles supplement these generic rules. They record capabilities verified against current host documentation and must never override stricter trust-model or runtime capability checks.

- [ChatGPT](platforms/chatgpt.md) — consumer ChatGPT capture, completeness, file persistence, exact-byte hashing, shared-link evidence, and provider-authentication limits. Last verified: 2026-08-24.
- [Claude.ai](platforms/claude.md) — consumer Claude capture, custom Skills, code/file execution, shared-chat snapshot evidence, attachment/MCP limits, packaging differences, and provider-authentication limits. Last verified: 2026-08-24.

## Capability classes

### A. Full local artifact + hash capability

The host can:

- access conversation content needed for capture;
- create a downloadable file;
- read the exact saved bytes;
- compute SHA-256 or run the bundled Python scripts.

This environment can complete the normal v1 integrity workflow and create a verified detached receipt.

This does **not** automatically establish that the session capture is complete. Completeness is a separate capability/evidence question.

### B. Artifact creation but no exact-byte verification

The host can create a file but cannot reliably read back or hash the exact saved bytes.

It may create a session artifact, but it must not create a receipt with `verification.verified: true` and must not say the hash was verified.

Tell the user that local exact-byte verification is unavailable in this host. The downloaded artifact may still be hashed independently with an external/local SHA-256 tool or through `https://email.proofstamp.org/`.

### C. No downloadable file capability

If the host cannot create a stable downloadable artifact, it cannot complete the ProofStamp exact-byte workflow.

Do not present a Markdown code block or pasted JSON as equivalent to a verified `.proofstamp.json` file because copying, encoding, whitespace, or line endings can change the bytes.

Explain the capability limitation instead.

## Conversation visibility and completeness

Hosts may expose:

- the complete visible conversation together with affirmative metadata that establishes completeness;
- the currently available context without any completeness signal;
- only the current context window;
- a summarized or truncated history;
- message IDs or timestamps;
- no stable session identifier.

Record only what is actually available.

Set `capture.completeness` as follows:

- `complete` only when affirmative host/API/export/capture evidence supports that every item inside the declared `capture.scope` was available and included;
- `partial` when the host or capture process makes it known that in-scope history is missing, truncated, failed to hydrate, or otherwise omitted;
- `unknown` when the capture process cannot establish whether all in-scope material was available and included.

For `ai_generated` capture, `unknown` is the safe default unless an independent host signal supports `complete`. The model's own impression that it can see the whole conversation is not sufficient.

If earlier visible history is unavailable to the capture process, disclose the missing material in `capture.omissions` and `limitations` as well as using `partial` when that absence is known.

Do not use memory, inference, or a reconstructed summary to represent inaccessible messages as exact transcript content.

## Provider, model, client, and harness metadata

Treat metadata according to its actual source:

- host/API supplied value: `host_exposed`;
- model saying what it believes it is: `model_reported`;
- user assertion: `user_provided`;
- tool/connector result: `tool_result`.

If the host does not expose a client name, harness name, UI setting, session ID, timestamp, or similar field, use `unavailable` where the schema requires a value or omit optional fields.

## System instructions

Some hosts may expose reproducible instructions to the capture process, while protected system or developer instructions may not be allowed to be reproduced.

Only include instructions that are legitimately exposed and permitted to be reproduced. Never infer protected instructions from behavior.

If protected instructions cannot be included, mark the system prompt unavailable and disclose the omission.

Protected system instructions and private reasoning can be intentionally outside the declared capture scope. Their exclusion does not by itself force `capture.completeness.status` to `partial`, but the exclusions must remain explicit.

## Sources and tools

A tool being installed or visible is not evidence that it was used.

Record only sources actually consulted during the session. When the host exposes tool call identifiers, source URLs, document references, or citations, preserve those references with the appropriate provenance.

Do not invoke extra sources during ProofStamp capture merely to make the source list look more complete.

## Attachments

If exact attachment bytes are accessible through an authorized file capability, their SHA-256 may be computed and recorded.

If only filename or metadata is available, record that metadata and set `hash_status` to `unavailable` or `unverified` as appropriate.

Never follow a captured filename as a filesystem path unless the host has separately provided that exact attachment as an authorized file resource.

## Hashing capability

Preferred implementation:

```bash
python scripts/create_receipt.py session.proofstamp.json
python scripts/verify_proofstamp.py \
  session.proofstamp.json \
  session.proofstamp.receipt.json
```

Python 3 is not a requirement of the format itself. A host may use another local SHA-256 implementation if it can prove it is hashing the exact saved bytes and independently recalculates the result.

## External network capability

The core ProofStamp capture does not require network access.

Do not upload the session or call external timestamp services automatically. The optional email handoff is a user-controlled next step.

## Capability disclosure

The artifact and final response should make capability limits visible. Prefer statements such as:

- `Capture completeness: unknown; the host exposed the current conversation context but no affirmative completeness signal.`
- `Capture completeness: partial; visible conversation available from message 12 onward and earlier history is unavailable.`
- `Attachment bytes unavailable; no attachment fingerprint recorded.`
- `Model name is model-reported, not host-authenticated.`
- `Exact-byte hashing unavailable in this host; no verified receipt created.`

Do not turn a host limitation into a stronger claim.
