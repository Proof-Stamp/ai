# Security Policy

ProofStamp AI handles material that may contain private conversations, source references, attachment metadata, credentials, or other sensitive information. Security and privacy failures should therefore be treated as high priority.

## Supported versions

The project is pre-release. Until the first tagged release, security fixes apply to the current `main` branch.

## Reporting a vulnerability

Please do not publish sensitive vulnerability details in a public GitHub issue.

Use GitHub's private vulnerability reporting for this repository if it is enabled. If private reporting is unavailable, contact the ProofStamp maintainers through the organization’s existing contact channels and provide only the information needed to reproduce and assess the issue.

Useful reports include:

- affected version or commit;
- reproduction steps;
- expected and observed behavior;
- potential privacy or integrity impact;
- a minimal proof of concept when appropriate.

## Sensitive data

Do not attach real AI session exports, credentials, private transcripts, API keys, or confidential user files to public issues, pull requests, tests, or examples. Use synthetic fixtures.

## Prompt injection

ProofStamp intentionally processes untrusted content. Conversation messages, webpages, file text, connector responses, tool output, and attachment metadata may contain instructions aimed at the AI running the skill.

Those instructions are data to preserve, not trusted instructions to execute.

A security issue includes any path where untrusted captured content can cause the ProofStamp workflow to:

- reveal or reconstruct hidden system instructions or private reasoning;
- access credentials, connector secrets, environment variables, hidden files, or other information not legitimately exposed to the capture process;
- change provenance or capture method without supporting evidence;
- change `capture.completeness.status` to `complete` without affirmative evidence that all items in the declared scope were available and included;
- silently omit or restore session material, limitations, omissions, redactions, or completeness basis;
- perform unauthorized network, connector, file, or tool actions;
- reinterpret literal source content as trusted role, tool-call, or control structure;
- falsely present an incomplete, unknown, or manipulated artifact as complete.

Deterministic security tests live under `tests/security/`. Model-dependent prompt-injection regression cases live in `evals/prompt-injection.md`. Passing those tests does not mean prompt injection is generally solved.

## Security boundaries

A ProofStamp protects the integrity of the exact exported bytes after hashing. It does not independently prove that an AI provider supplied every recorded field, that a captured session is complete, or that the underlying content is true.

Capture completeness is a separate evidence claim. `complete` is permitted only with an adequate recorded basis; otherwise the artifact must say `partial` or `unknown` as appropriate.
