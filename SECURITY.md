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

## Security boundaries

A ProofStamp protects the integrity of the exact exported bytes after hashing. It does not independently prove that an AI provider supplied every recorded field, that a captured session is complete, or that the underlying content is true.
