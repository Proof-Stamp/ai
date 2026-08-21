# Prior Art and Adjacent Systems

Research snapshot: **2026-08-21**.

ProofStamp AI does not claim novelty for cryptographic hashing, timestamping, signed receipts, transcript export, provenance metadata, or tamper-evident logs. This document records adjacent systems and research that informed the v0.1.2 release hardening.

This is a technical landscape review, not legal advice, patent clearance, or trademark clearance. The list is not exhaustive.

## 1. Sigill: AI evidence capture and timestamping

Sigill publishes tools and engineering guidance for tamper-evident AI evidence, including browser/API-oriented capture, canonicalized evidence envelopes, timestamping, and sequence hardening.

Relevant material:

- https://sigill.ai/blog/2026-04-27-hardening-ai-evidence
- https://sigill.ai/blog/2026-04-25-timestamped-claude-agent
- https://sigill.ai/blog

The April 27 hardening article makes two points directly relevant to ProofStamp:

1. timestamping individual turns does not by itself establish that the model input was complete;
2. independently stamped individual entries do not by themselves establish sequence integrity if entries can be deleted or reordered.

Sigill recommends recording fuller model input when available and, for stronger continuous logs, hash-chaining entries and periodically anchoring the chain head or using Merkle roots.

### ProofStamp design consequence

ProofStamp v1 now records `capture.completeness` explicitly instead of treating apparent transcript continuity as proof of completeness.

ProofStamp does **not** add a message hash chain to the v1 snapshot format. A finalized `.proofstamp.json` is already committed as one exact byte sequence by its detached SHA-256 receipt. Hash chains become materially useful if ProofStamp later supports continuous, append-only capture before a final snapshot exists.

## 2. VCT: Verifiable Conversation Transcript

Paper:

- Ruilin Xing et al., **VCT: A Verifiable Transcript System for LLM Conversations**, arXiv:2606.23003
- https://arxiv.org/abs/2606.23003

VCT addresses non-linear LLM conversation history, including regenerated responses, branches, deletion, and multi-device state. It uses branch-level hash chains, session Merkle roots, account-level roots, and joint user/server signatures.

### ProofStamp design consequence

VCT demonstrates why provider/server participation can support substantially stronger transcript authenticity and consistency claims than a post-hoc AI-generated snapshot.

ProofStamp keeps `provider_signed` as a distinct capture method and does not describe `ai_generated` evidence as equivalent to provider-authenticated evidence.

## 3. llm_sign: provider-signed request/response evidence

Repository:

- https://github.com/kexinoh/llm_sign

`llm_sign` is designed to let an LLM provider cryptographically sign request/response evidence so a relay cannot silently rewrite the response, substitute a model, or fabricate a provider response without detection. Its design binds signatures to provider TLS certificate identity or another trusted provider key.

### ProofStamp design consequence

ProofStamp's SHA-256 receipt establishes integrity of the exported ProofStamp artifact. It does **not** authenticate the LLM provider. Provider signatures are a separate evidence dimension and should be preserved when available.

## 4. Signed content and agent receipts

Examples:

- https://github.com/Gareth1953/provenance-receipts
- https://github.com/vouch-protocol/vouch
- https://github.com/arian-gogani/nobulex

These projects explore signed receipts, agent identity, action provenance, hash chains, or verifiable credentials. A particularly useful pattern is separating cryptographically verified facts from caller-attested metadata. A signature can prove who signed a receipt and that its signed bytes were not changed, while metadata such as the claimed model may still be only caller-attested unless independently verified.

### ProofStamp design consequence

ProofStamp keeps field-level provenance separate from exact-byte integrity. A valid receipt must not silently upgrade `model_reported` or `user_provided` metadata into provider-authenticated metadata.

## 5. Conversation exporters

Example:

- https://github.com/maks-bond/chatgpt-conversation-exporter

Conversation exporters can sometimes access message IDs, timestamps, attachment labels, or conversation metadata not present in the currently mounted page. Some also explicitly report when complete export could not be achieved.

### ProofStamp design consequence

ProofStamp recognizes multiple capture methods:

- `ai_generated`
- `browser_capture`
- `api_capture`
- `host_export`
- `provider_signed`

The current Agent Skill primarily implements `ai_generated`. Future browser/API/host integrations can strengthen capture provenance and may provide affirmative completeness evidence unavailable to the model alone.

## 6. RFC 3161 trusted timestamping

Standard:

- RFC 3161, Internet X.509 Public Key Infrastructure Time-Stamp Protocol
- https://www.rfc-editor.org/info/rfc3161/
- updated by RFC 5816: https://www.rfc-editor.org/rfc/rfc5816.html

RFC 3161 defines a Time Stamping Authority protocol in which a timestamp token is signed over a hash representation of the datum. The standard is designed to support evidence that data existed before a particular time.

### ProofStamp design consequence

The email workflow is intentionally described as **external time evidence**, not as equivalent to a trusted RFC 3161 timestamp token. RFC 3161 support is a plausible future adapter for stronger time evidence attached to the same ProofStamp fingerprint.

## 7. OpenTimestamps

Project:

- https://opentimestamps.org/

OpenTimestamps defines a timestamp proof format and supports independent verification of proofs anchored through Bitcoin. The user's file can be hashed locally before the timestamp proof is created.

### ProofStamp design consequence

OpenTimestamps is another plausible optional adapter for stronger external time evidence. Adding it would not change the capture provenance or completeness of the underlying session artifact.

## 8. C2PA / Content Credentials

Specification:

- https://c2pa.org/
- https://spec.c2pa.org/

C2PA defines cryptographically bound provenance for digital assets. Its architecture distinguishes verifiable provenance/assertions from the broader human judgment of whether an asset is trustworthy.

### ProofStamp design consequence

ProofStamp follows the same general discipline: cryptographic integrity and provenance signals should be stated precisely, without turning them into unsupported claims that the content is true, trustworthy, or complete.

## 9. Other projects using the name "ProofStamp"

The name is not unique on GitHub or the wider web. Examples found during the 2026-08-21 review include:

- https://github.com/IEEE-VIT/ProofStamp — a creator-focused digital-evidence project using hashes, signatures, RFC 3161 timestamps, and other evidence mechanisms;
- https://chromewebstore.google.com/detail/proofstamp-timestamped-ev/fpoagkmhedndoeoekabbjbofpfgmhdhn — a browser evidence-capture extension;
- https://proofstamp.io/ — a separate organization using `PROOFstamp` as a certification mark for agentic-AI security products.

This does not establish infringement or ownership and is not a substitute for trademark review. It is a release-planning risk that should be evaluated separately before substantial promotion or commercial branding investment.

## 10. ProofStamp AI's intended niche

The current project is deliberately narrower than many of the systems above.

Its intended contribution is a **low-friction, portable session-snapshot workflow** that can operate as an Agent Skill or even a prompt, while making the evidence boundary explicit:

- record only what the current capture process can legitimately access;
- disclose whether capture completeness is `complete`, `partial`, or `unknown`;
- preserve field-level provenance;
- hash the exact exported bytes rather than an abstract in-memory object;
- verify those saved bytes independently before issuing a detached receipt;
- support a normal-user email handoff without requiring a wallet, provider integration, or browser extension;
- avoid claiming provider authenticity or completeness that the evidence does not support.

## 11. Evidence-strength model adopted for release

For review and future tooling, treat these as independent dimensions rather than one score:

| Dimension | Representative progression |
| --- | --- |
| Capture provenance | `ai_generated` → `browser_capture` / `api_capture` → `host_export` → `provider_signed` |
| Capture completeness | `unknown` / `partial` → `complete` with affirmative basis |
| Integrity | unverified → exact saved-byte SHA-256 verified |
| Time evidence | none → email record → RFC 3161 / OpenTimestamps or other independently verifiable timestamp evidence |
| Identity/authenticity | none → user/org signature → provider-authenticated signature |

No dimension automatically upgrades another.
