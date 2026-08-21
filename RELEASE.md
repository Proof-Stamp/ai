# Release preparation

Target: **`v0.1.2` pre-release**

This is the first planned public ProofStamp AI pre-release after prior-art review and capture-completeness hardening.

## Release blockers

Do not tag or publish the release until all checked items below are complete.

- [ ] Release-hardening PR is merged to `main`.
- [ ] GitHub Actions `tests` passes on the final PR head and on merged `main`.
- [ ] Synthetic `.proofstamp.json` and detached receipt verify against exact checked-in bytes.
- [ ] Prompt-injection fixture confirms captured instructions cannot upgrade provenance or capture completeness.
- [ ] Run the model-dependent cases in `evals/prompt-injection.md` on at least one supported AI host and record the result.
- [ ] Run `PROMPT.md` from a fresh conversation with no prior ProofStamp context and confirm it produces a valid artifact/receipt or fails narrowly when host capabilities are missing.
- [ ] Run the installed `proofstamp/` skill from a fresh conversation and confirm the final response reports `Capture completeness` explicitly.
- [ ] Decide whether the known `ProofStamp` naming collisions require additional trademark/legal review before substantial promotion. See `docs/PRIOR-ART.md`.
- [ ] Confirm `main` branch protection still requires the `tests` status check.

## Proposed tag

```text
v0.1.2
```

The Agent Skill metadata in `proofstamp/SKILL.md` must match `0.1.2` before tagging.

## Proposed release title

```text
ProofStamp AI v0.1.2 — first public pre-release
```

## Proposed release notes

ProofStamp AI v0.1.2 is the first public pre-release of an open session-evidence workflow for AI conversations.

### Included

- installable `proofstamp` Agent Skill;
- prompt-only workflow for hosts where users do not want to install a skill;
- portable `.proofstamp.json` session format and detached receipt schema;
- explicit field-level provenance and unavailable/excluded states;
- explicit `capture.completeness` status: `complete`, `partial`, or `unknown`;
- safe default of `unknown` for AI-generated captures unless affirmative host evidence supports completeness;
- exact saved-byte SHA-256 hashing and independent re-verification;
- synthetic example and deterministic verification scripts;
- user-controlled `mailto:` handoff after successful verification;
- prompt-injection security fixtures and behavioral eval cases;
- trust model, privacy rules, disclaimer, and prior-art review.

### What v0.1.2 does not claim

ProofStamp does not automatically prove that a conversation is complete, provider-authenticated, true, legally admissible, or originally created at a particular time.

A valid exact-byte receipt proves that the selected artifact bytes match the recorded SHA-256. Capture provenance, completeness, external time evidence, and provider identity are separate evidence dimensions.

### Current capture strength

The first skill implementation primarily uses `capture_method: ai_generated`. Browser/API/host-export/provider-signed integrations are future stronger capture paths.

### External time evidence

The current normal-user handoff supports email-based evidence for the fingerprint. RFC 3161 and OpenTimestamps are documented as potential stronger timestamp adapters, not implemented in this release.

### Compatibility

Agent Skill hosts must expose the current conversation and support creation of a stable downloadable file. Exact-byte verified receipts additionally require the host to read back the saved file bytes and compute SHA-256.

If those capabilities are unavailable, the skill must disclose the limitation rather than fabricate a verified ProofStamp.

## Tagging procedure after blockers are cleared

1. Merge the release-hardening PR.
2. Confirm `main` CI is green.
3. Create annotated tag `v0.1.2` from the exact tested `main` commit.
4. Publish a GitHub **pre-release** using the release notes above.
5. Replace prompt examples that reference `main` with the immutable `v0.1.2` URL where reproducibility matters.
6. Perform one post-release install/prompt smoke test from the tag.

## Post-release priorities

- record platform-specific behavioral eval results;
- explore browser/API capture for stronger completeness evidence;
- evaluate optional RFC 3161 and OpenTimestamps adapters;
- investigate provider-signed transcript compatibility;
- decide on naming/trademark risk before broader commercial promotion.
