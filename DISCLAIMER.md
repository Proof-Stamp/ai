# Disclaimer

ProofStamp AI is open-source software for creating and verifying integrity records for AI-session evidence artifacts.

It is not a legal, forensic, compliance, archival, certification, identity, or authentication service.

## What a ProofStamp means

A matching SHA-256 fingerprint can show that a specific file matches the exact bytes that were fingerprinted.

External time evidence, such as an email receipt or another independent record containing the same fingerprint, can provide evidence that the fingerprint reached that external system no later than the recorded time.

A ProofStamp does **not**, by itself, prove:

- that an AI session is authentic, complete, accurate, or provider-signed;
- that every recorded field was supplied or authenticated by the AI provider;
- that the underlying statements, sources, outputs, or user claims are true;
- authorship, ownership, identity, or original creation time;
- that a file was unchanged before it was fingerprinted;
- that an external timestamp is the original creation time of the session; or
- that a ProofStamp will be accepted as evidence by a court, regulator, arbitrator, auditor, insurer, employer, or other third party.

See `references/TRUST-MODEL.md` for the technical trust boundary.

## User responsibility

Users are responsible for deciding whether ProofStamp AI is appropriate for their use case and for complying with applicable laws, contractual duties, confidentiality obligations, retention requirements, and organizational policies.

AI sessions may contain personal information, confidential material, credentials, proprietary documents, connector output, or other sensitive data. Review an artifact before storing, sharing, emailing, publishing, or submitting it to a third party.

ProofStamp AI does not guarantee that the capture process can access or preserve every part of a session. Information that is unavailable to the capture process must not be reconstructed or represented as captured evidence.

## Third-party systems

ProofStamp AI may be used with third-party services such as AI providers, email providers, hosting platforms, browsers, connectors, or timestamp services. Those services operate under their own terms, policies, availability, retention practices, and security controls. ProofStamp does not control or guarantee them.

## No warranty or professional advice

ProofStamp AI is provided for informational and technical use and does not provide legal or other professional advice.

The software is provided without warranties or conditions, subject to the terms and limitations in the Apache License 2.0. To the extent permitted by applicable law, contributors and maintainers are not liable for losses arising from use of, inability to use, or reliance on the software or generated artifacts except as otherwise required by applicable law.

If your use case has legal, regulatory, evidentiary, forensic, or compliance consequences, obtain appropriate professional advice and independently evaluate the evidence requirements that apply to you.
