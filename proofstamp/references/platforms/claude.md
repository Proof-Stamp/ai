# Claude.ai capability profile

Last verified: 2026-08-24

This profile supplements `../PLATFORM-CAPABILITIES.md`. It describes consumer Claude.ai behavior relevant to ProofStamp and does not override runtime capability checks or the ProofStamp trust model.

## Recommended ProofStamp use

For normal Claude.ai users, the preferred recurring-use path is a custom Skill uploaded in Claude under `Customize > Skills`, with Code execution and file creation enabled.

Anthropic documents custom Skills as available to Free, Pro, Max, Team, and Enterprise users when code execution is enabled. Individual users can upload a ZIP containing the skill directory and enable it from the Skills UI.

A user can then invoke ProofStamp with a short request such as:

`ProofStamp this session.`

For one-off use, the generic prompt-only ProofStamp workflow remains valid when Claude can access the pinned instructions and has the required file/hash capabilities.

## Capture method

For a normal Claude.ai conversation captured by Claude itself, use:

`capture_method: "ai_generated"`

unless a distinct host export, API capture, or provider-authenticated format is actually being used.

Do not classify an ordinary Claude-generated transcript as `provider_signed`.

## Conversation visibility and completeness

Default to:

`capture.completeness.status: "unknown"`

for ordinary AI-generated capture.

Claude may have access to the messages needed to answer in the current conversation, but the model's own impression that it can see the full chat is not affirmative host evidence that every in-scope message was available and included.

Use `complete` only when separate host/API/export evidence establishes completeness for the declared capture scope. Use `partial` when known in-scope material is unavailable, truncated, or omitted.

Do not reconstruct inaccessible messages from memory or summaries.

## Shared-chat snapshot as optional supporting evidence

Claude supports shareable chat snapshots. Anthropic states that a shared snapshot contains all messages sent before the chat was shared, including artifacts. Messages sent after the share event remain private until a new snapshot is created.

This can be useful as optional supporting host evidence for conversation completeness up to the sharing point.

Important limits:

- anyone with a public share link can view the snapshot on individual plans;
- Team and Enterprise sharing may be restricted to organization members;
- attached files themselves are not included in the shared snapshot;
- raw MCP tool-call data is not included in the shared snapshot;
- a shared snapshot is supporting provenance, not a cryptographic provider signature over the ProofStamp artifact;
- creating a share link has privacy consequences and must never be done automatically during ProofStamp capture.

If a user separately creates a shared snapshot and ProofStamp records that evidence, preserve the share reference with the weakest accurate provenance and disclose what the snapshot excludes.

## File creation and code execution

Anthropic documents Code execution and file creation as available to Claude users on web, desktop, and mobile, subject to plan/workspace settings.

This means Claude may be able to create downloadable ProofStamp artifacts and execute code needed for local hashing.

However, ProofStamp must still check the current runtime before claiming exact-byte verification. The relevant questions are whether the active environment can:

1. write the final `.proofstamp.json` file;
2. identify and read back the exact saved bytes;
3. compute SHA-256 over those saved bytes;
4. independently recalculate the digest;
5. create and verify the detached receipt.

If any required step is unavailable, downgrade according to `../PLATFORM-CAPABILITIES.md` and do not claim `Hash verified: yes`.

## Custom Skill packaging

Anthropic's current Claude Help Center documentation for consumer custom Skills describes a skill directory containing a lowercase `skill.md` file with required `name` and `description` YAML metadata, packaged as a ZIP whose single top-level entry is the skill directory.

The Help Center states:

- `name`: maximum 64 characters;
- `description`: maximum 200 characters for the consumer custom-Skill authoring flow;
- the folder name should match the skill name;
- the ZIP should contain the skill folder as its root;
- custom Skills can include supporting resources and executable scripts.

Anthropic's platform/API documentation separately uses uppercase `SKILL.md` and documents different API-side description limits. Do not assume one package shape is portable across every Anthropic surface. A Claude.ai distribution build should be validated specifically against the consumer upload flow before release.

The canonical ProofStamp source should remain platform-neutral. Prefer a generated Claude adapter package rather than weakening or renaming the canonical Agent Skill contract globally.

## Sources and tool results

Record only sources actually consulted during the session.

If Claude exposes citations, URLs, tool results, or MCP-derived content to the capture process, preserve only the fields legitimately available and label provenance accurately.

Do not infer that raw MCP results are part of a shared-chat snapshot. Anthropic explicitly documents that raw MCP tool-call data stays hidden from shared snapshots.

## Attachments

If exact attachment bytes are available through the authorized Claude file/code environment, ProofStamp may hash those bytes and record the attachment fingerprint.

If only attachment metadata or conversation-visible references are available, record only those fields and mark attachment hashing unavailable or unverified as appropriate.

A Claude shared-chat snapshot does not include the attached file itself, so the share snapshot alone must not be treated as evidence of exact attachment bytes.

## Provider, model, and session metadata

Use `host_exposed` only for values independently exposed by the host or an authenticated API/export.

A model self-report remains `model_reported`. A user's statement remains `user_provided`.

Do not invent stable session IDs, message IDs, timestamps, model identifiers, or UI settings that Claude does not expose to the capture process.

## Provider authentication

Normal Claude.ai ProofStamp capture is not provider-signed.

A verified SHA-256 receipt proves exact-byte identity of the saved ProofStamp artifact after creation. It does not prove that Anthropic authenticated the transcript, that Claude's answers are true, or that the underlying conversation originally occurred at a particular time.

## Email handoff

After successful exact-byte verification, use the normal ProofStamp user-controlled email handoff.

Do not send email automatically. Do not upload the conversation automatically. Do not create a share link automatically.

## Verification sources

Primary Anthropic documentation consulted:

- https://support.claude.com/en/articles/12512180-use-skills-in-claude
- https://support.claude.com/en/articles/12512198-how-to-create-custom-skills
- https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude
- https://support.claude.com/en/articles/10593882-share-and-unshare-chats
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

Because host features and packaging rules can change, re-verify this profile before changing ProofStamp's trust claims or publishing a new Claude distribution package.
